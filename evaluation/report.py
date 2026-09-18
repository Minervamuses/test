"""The single Markdown report: header, per-image table, averages, exclusions.

The header exists so that a number found here months from now can be traced
back: commit hash, model hash, weight hashes, devices, and every fixed
convention it was produced under. ../GOALS.md, "已知會影響結論解讀的性質",
requires the interpretation caveats too, so INTERPRETATION below is not
optional text and must not be trimmed.
"""

import hashlib
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from summary import HIGHER_IS_BETTER, decide_winner

REQUIRED_HEADER_FIELDS = (
    "執行時間",
    "run 目錄",
    "git HEAD",
    "worktree 狀態",
    "原圖來源資料夾",
    "探索規則",
    "取樣方式",
    "取樣上限",
    "探索到的張數",
    "實際處理張數",
    "降採樣與放大演算法",
    "倍率",
    "Pillow 版本",
    "mod-crop 規則",
    "模型檔",
    "模型 SHA-256",
    "模型架構",
    "模型 scale",
    "SR tile 設定",
    "SR 線 device",
    "度量 device",
    "cudnn.benchmark",
    "跨批次可比性",
    "色彩空間與 data_range",
    "SSIM 參數",
    "SSIM 邊界與變異數",
    "PSNR inf 規則",
    "平均的納入規則",
    "LPIPS 套件版本",
    "LPIPS net",
    "LPIPS 線性層權重 SHA-256",
    "LPIPS backbone 來源",
    "LPIPS backbone SHA-256",
)

INTERPRETATION = """\
- 本報告的真值是**自己造的**：取高解析原圖，以 bicubic 降採樣 4× 得到低解析輸入，再由兩條線放大回原尺寸。兩條線讀的是**磁碟上同一個 LR PNG**，bicubic 線沒有任何路徑碰得到原圖。
- 退化是**純 bicubic 降採樣**，而 `realesr-general-x4v3` 是以真實世界複合退化（模糊、雜訊、壓縮）訓練的 GAN 模型。在乾淨的 bicubic 基準上，GAN 類 SR 常見的結果是 **PSNR／SSIM 輸給 bicubic，但 LPIPS 明顯勝出**。若出現這個組合，那是評估設定的已知性質，不是實作錯誤。
- 因此「是否打贏一般放大手段」必須**三個指標分別下結論**：PSNR 與 SSIM 衡量逐像素保真度，LPIPS 衡量感知相似度。不得只用 PSNR 判勝負。
- PSNR／SSIM 採 **RGB 三通道**計算，不是論文常見的 Y 通道，數值不可直接與論文對照。
- SR 增加的細節是**重建**而非還原：模型畫出的紋理未必對應真實地物。銳利不等於正確。
- 本報告只描述**本次退化設定下**的結果，不可外推成「本專案在真實低解析影像上的畫質排名」。
- 真值來源若為 JPEG，真值本身已是有損解碼結果。這不影響兩條線的對等性（兩邊比的是同一個真值），但絕對數值受此影響。
"""


@dataclass(frozen=True)
class RunEnvironment:
    started: datetime
    run_dir: Path
    git_head: str
    worktree_clean: bool
    source_directory: Path
    discovery_rule: str
    sampling: str
    limit: int
    discovered: int
    selected: int
    pillow_version: str
    model_target: str
    model_sha256: str
    architecture: str
    model_scale: int
    tile_size: int
    sr_device: str
    metric_device: str
    cudnn_benchmark: bool
    lpips_version: str
    lpips_net: str
    lpips_linear_sha256: str
    lpips_backbone_url: str
    lpips_backbone_sha256: str


def _number(value: float | None, digits: int) -> str:
    if value is None:
        return "n/a"
    if value == float("inf"):
        return "inf"
    if value == float("-inf"):
        return "-inf"
    return f"{value:.{digits}f}"


_DIGITS = {"PSNR": 4, "SSIM": 6, "LPIPS": 6}


def _size(pair: tuple[int, int]) -> str:
    return f"{pair[0]}×{pair[1]}"


def _header_rows(environment: RunEnvironment, sr_device: str) -> dict[str, str]:
    worktree = (
        "追蹤檔全部乾淨"
        if environment.worktree_clean
        else "**有未提交的追蹤檔變更**（此份數字對應的程式狀態未完全被 commit 涵蓋）"
    )
    return {
        "執行時間": environment.started.strftime("%Y-%m-%d %H:%M:%S %z (%Z)"),
        "run 目錄": str(environment.run_dir),
        "git HEAD": environment.git_head,
        "worktree 狀態": worktree,
        "原圖來源資料夾": str(environment.source_directory),
        "探索規則": environment.discovery_rule,
        "取樣方式": environment.sampling,
        "取樣上限": str(environment.limit),
        "探索到的張數": str(environment.discovered),
        "實際處理張數": str(environment.selected),
        "降採樣與放大演算法": "Pillow `Image.Resampling.BICUBIC`（降採樣與 bicubic 放大皆是）",
        "倍率": f"{environment.model_scale}×",
        "Pillow 版本": environment.pillow_version,
        "mod-crop 規則": "自右／下裁到寬高皆為 4 的倍數，裁切後的原圖才是真值；裁切不改動任何保留下來的像素",
        "模型檔": environment.model_target,
        "模型 SHA-256": environment.model_sha256,
        "模型架構": environment.architecture,
        "模型 scale": str(environment.model_scale),
        "SR tile 設定": f"任一邊 > {environment.tile_size} 時自動分塊（核心 {environment.tile_size}、halo 32）",
        "SR 線 device": sr_device,
        "度量 device": f"{environment.metric_device}（bicubic 線恆為 Pillow 的 CPU 實作，不受此影響）",
        "cudnn.benchmark": str(environment.cudnn_benchmark),
        "跨批次可比性": (
            "CPU 與 GPU 的浮點結果不保證相同（TF32、cuDNN 演算法選擇），"
            "**不同 device 的數字屬於不同批次，不可並列比較**"
        ),
        "色彩空間與 data_range": "RGB 三通道、8-bit、`data_range = 255`；**不是 Y 通道**",
        "SSIM 參數": "Gaussian window 11×11、σ=1.5、K1=0.01、K2=0.03；三通道各自計算後取平均",
        "SSIM 邊界與變異數": (
            "邊界為 `valid`（不補邊，SSIM map 為 `(H-10)×(W-10)`）；"
            "變異數為 Wang et al. 的高斯加權有偏估計，非 scikit-image 的樣本共變異修正"
        ),
        "PSNR inf 規則": "`MSE == 0` 記為 `inf`，該張**排除於 PSNR 平均**之外，SSIM／LPIPS 照常納入",
        "平均的納入規則": "只對 SR 線與 bicubic 線**都成功量到**的圖片取算術平均；任一線失敗，兩邊都不計入",
        "LPIPS 套件版本": environment.lpips_version,
        "LPIPS net": environment.lpips_net,
        "LPIPS 線性層權重 SHA-256": environment.lpips_linear_sha256,
        "LPIPS backbone 來源": environment.lpips_backbone_url,
        "LPIPS backbone SHA-256": environment.lpips_backbone_sha256,
    }


def _per_image_table(results) -> list[str]:
    if not results:
        return ["（本次沒有任何圖片在兩條線上都成功量到。）"]
    lines = [
        "| 檔名 | 原始尺寸 | 真值（裁切後） | LR 尺寸 "
        "| SR PSNR | bicubic PSNR | PSNR 勝方 "
        "| SR SSIM | bicubic SSIM | SSIM 勝方 "
        "| SR LPIPS | bicubic LPIPS | LPIPS 勝方 |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for item in results:
        cells = [item.source_name, _size(item.original), _size(item.cropped), _size(item.low)]
        for name in ("PSNR", "SSIM", "LPIPS"):
            sr_value = getattr(item.sr, name.lower())
            bicubic_value = getattr(item.bicubic, name.lower())
            winner, _ = decide_winner(name, sr_value, bicubic_value)
            cells += [_number(sr_value, _DIGITS[name]), _number(bicubic_value, _DIGITS[name]), winner]
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def _average_table(summary) -> list[str]:
    lines = [
        f"納入 {summary.included} 張、排除 {summary.failed} 張（排除的圖片兩條線都不計入）。",
        "",
        "| 指標 | 方向 | SR 平均 | bicubic 平均 | 勝方 | 差距 | 納入張數 | 因 inf 排除 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for metric in summary.metrics:
        direction = "越高越好" if HIGHER_IS_BETTER[metric.name] else "越低越好"
        digits = _DIGITS[metric.name]
        lines.append(
            f"| {metric.name} | {direction} | {_number(metric.sr_mean, digits)} "
            f"| {_number(metric.bicubic_mean, digits)} | {metric.winner} "
            f"| {_number(metric.margin, digits)} | {metric.counted} | {metric.excluded_infinite} |"
        )
    return lines


def _conclusion(summary) -> list[str]:
    lines = ["", "### 三個指標各自的結論", ""]
    for metric in summary.metrics:
        if metric.winner == "n/a":
            lines.append(f"- **{metric.name}：** 沒有可用的比較（納入 0 張）。")
        elif metric.winner == "tie":
            lines.append(f"- **{metric.name}：** 兩條線平均相同。")
        else:
            digits = _DIGITS[metric.name]
            lines.append(
                f"- **{metric.name}：** {metric.winner} 較佳，差距 {_number(metric.margin, digits)}"
                f"（{'越高越好' if HIGHER_IS_BETTER[metric.name] else '越低越好'}）。"
            )
    lines += [
        "",
        "三者方向若不一致，那不是矛盾：PSNR／SSIM 與 LPIPS 衡量的是不同的東西。見「解讀前提」。",
    ]
    return lines


def _failure_table(failures) -> list[str]:
    if not failures:
        return ["本次沒有失敗或被略過的來源。"]
    lines = ["| 檔名 | 環節 | 原因 |", "|---|---|---|"]
    lines += [f"| {f.source_name} | {f.stage} | {f.reason} |" for f in failures]
    return lines


def render_report(environment: RunEnvironment, results, failures, summary) -> str:
    sr_device = environment.sr_device
    sections = [
        "# 評估報告 — SR 線 vs bicubic 基線",
        "",
        "取高解析原圖為真值，以固定退化流程造出低解析輸入，再由兩條線放大回真值尺寸並比對。",
        "",
        "## 1. 執行環境與參數",
        "",
        "| 項目 | 值 |",
        "|---|---|",
    ]
    rows = _header_rows(environment, sr_device)
    missing = [field for field in REQUIRED_HEADER_FIELDS if not rows.get(field)]
    if missing:
        raise ValueError(f"Report header is missing required fields: {missing}")
    sections += [f"| {field} | {rows[field]} |" for field in REQUIRED_HEADER_FIELDS]
    sections += ["", "## 2. 解讀前提（不可省略）", "", INTERPRETATION.rstrip()]
    sections += ["", "## 3. 逐張成績", ""] + _per_image_table(results)
    sections += ["", "## 4. 平均", ""] + _average_table(summary) + _conclusion(summary)
    sections += ["", "## 5. 失敗與排除", ""] + _failure_table(failures) + [""]
    return "\n".join(sections)


def write_report(destination: Path, text: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(project_root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments], cwd=project_root, capture_output=True, text=True, check=True
    ).stdout.strip()


def describe_environment(
    *,
    started: datetime,
    run_dir: Path,
    project_root: Path,
    source_directory: Path,
    sampling: str,
    limit: int,
    discovered: int,
    selected: int,
    sr_line,
    metric_device: str,
) -> RunEnvironment:
    """Read the actual state of everything the header claims."""
    import lpips
    import torch
    from importlib.metadata import version
    from PIL import Image as PILImage
    from torchvision.models import AlexNet_Weights

    from drone_sr.inference import MODEL_PATH
    from drone_sr.tiling import TILE_SIZE

    status = _git(project_root, "status", "--porcelain")
    tracked_dirty = [line for line in status.splitlines() if not line.startswith("??")]

    backbone_url = AlexNet_Weights.IMAGENET1K_V1.url
    cached = Path(torch.hub.get_dir()) / "checkpoints" / backbone_url.rsplit("/", 1)[-1]
    backbone_sha = (
        _sha256(cached)
        if cached.is_file()
        else f"未找到本機快取（{cached}）；torchvision 以 check_hash 驗證 URL 內嵌的雜湊前綴"
    )

    return RunEnvironment(
        started=started,
        run_dir=run_dir,
        git_head=_git(project_root, "rev-parse", "HEAD"),
        worktree_clean=not tracked_dirty,
        source_directory=source_directory,
        discovery_rule="來源資料夾的**直接子項**中副檔名為 .png／.jpg／.jpeg（大小寫不敏感）；忽略子資料夾與其他副檔名",
        sampling=sampling,
        limit=limit,
        discovered=discovered,
        selected=selected,
        pillow_version=PILImage.__version__ if hasattr(PILImage, "__version__") else version("pillow"),
        model_target=MODEL_PATH.resolve().name,
        model_sha256=_sha256(MODEL_PATH.resolve()),
        architecture=str(getattr(sr_line, "architecture", "RealESRGAN Compact")),
        model_scale=sr_line.scale,
        tile_size=TILE_SIZE,
        sr_device=str(sr_line.device),
        metric_device=metric_device,
        cudnn_benchmark=torch.backends.cudnn.benchmark,
        lpips_version=version("lpips"),
        lpips_net="alex",
        lpips_linear_sha256=_sha256(Path(lpips.__file__).parent / "weights" / "v0.1" / "alex.pth"),
        lpips_backbone_url=backbone_url,
        lpips_backbone_sha256=backbone_sha,
    )
