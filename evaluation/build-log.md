# evaluation — Build Log

本檔是執行狀態與觀察證據的唯一來源。計劃文件描述打算做的事，本檔只記錄實際發生的事。

## 階段摘要

| 階段 | 狀態 | 開始 | 完成 | 證據 | 阻塞 |
|---|---|---|---|---|---|
| 01 — 固定退化契約與 bicubic 基線 | Complete | 2026-09-19 | 2026-09-19 | 24 項檢查通過；真實樣本尺寸鏈 4056×3040 → 1014×760 → 4056×3040；bicubic 與獨立重算逐位元相同 | 無 |
| 02 — 度量模組與 lpips 依賴 | In progress | 2026-09-19 | — | — | 等待 scipy／tqdm 授權（見 01:22 記錄） |
| 03 — SR 線接上未修改的 pipeline | Not started | — | — | — | 無 |
| 04 — 執行器、run 目錄與逐張＋平均報告 | Not started | — | — | — | 無 |
| 05 — 真實小樣本驗收、成本量測與文件對齊 | Not started | — | — | — | 無 |

狀態只用：`Not started`、`In progress`、`Blocked`、`Complete`。

只有在該階段的驗收與必要驗證都有觀察證據時，才標 `Complete`。

## 證據規則

- 記錄確切的命令或人工程序，以及簡潔的通過／失敗結果。
- 區分「實際觀察到」與「引用、歷史或計劃中」的證據。
- 略過或不可執行的檢查要記下來並寫明原因。**略過的檢查不是通過的檢查。**
- 大量輸出用路徑連結，不要整段貼進來。
- **每筆活動記錄要寫下對應的 commit hash**（見 `PLANS.md`「版本控制節奏與可追溯性」），讓文字證據能對回程式狀態。
- 不記 credentials、祕密、完整 diff 或例行敘述。
- 證據互相矛盾時，兩筆觀察都保留，該階段維持 `Blocked` 直到解決。

本計劃特別要求記入的證據：

- 每次真實執行的 run 目錄路徑、納入張數、排除張數與原因。
- 兩條線對等性的直接證據（bicubic 可從 LR 檔獨立重算、兩線輸入為同一檔案）。
- 執行前後 `src/drone_sr/`、`tests/`、`input/`、`output/`、`models/`、`pyproject.toml`、`requirements-wsl.txt` 的未變動確認方式與結果。
- 實測的單張耗時、峰值記憶體與所用 device，以及據此推估的全量成本。
- LPIPS 權重的來源 URL、檔案大小與 SHA-256。

## 待 GPU 補測

交付裝置是 GPU，但 coding agent 的沙箱 session 看不到它。依 `PLANS.md`「GPU 交接協定」，需要 GPU 的項目集中在此，**不標 `Blocked`**。清單清空前，計劃不得標為整體完成。

| # | 來源階段 | 要量什麼 | 沙箱內為何做不到 | 對應驗收條件 | 狀態 |
|---|---|---|---|---|---|
| — | — | 尚未產生項目（五個階段皆 `Not started`） | — | — | — |

狀態只用：`待補`、`已補（使用者 shell）`。已補的項目要在「活動紀錄」有對應的一筆，寫明確切命令、輸出與量測環境。

## 活動紀錄

尚無實作活動。計劃 bundle 已撰寫完成，但其中所有預定檢查都**尚未**以實作證據執行過。

## 2026-09-19 — 計劃修訂：交付裝置是 GPU，沙箱 session 看不到它

- **狀態：** 五個階段仍為 `Not started`。本次為純計劃修訂，沒有任何實作。
- **授權範圍：** `PLANS.md`「計劃維護與失敗處理」、`PROMPTS.md`「依相反證據修正計劃」。使用者於 2026-09-19 指出本機有 GPU 並要求修正計劃。
- **被推翻的理解：** 2026-09-18 記錄的 `torch.cuda.is_available() = False` 被當成本機狀態，實際上只是 coding agent 沙箱 session 的狀態。
- **驗證（實際觀察）：**
  - 使用者的一般 WSL shell：`.venv/bin/python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"` → `True NVIDIA GeForce RTX 5070 Ti Laptop GPU`。
  - 同日沙箱 session 內：`nvidia-smi` → `Failed to initialize NVML: GPU access blocked by the operating system`；`/dev/dxg` 不存在；`torch.cuda.device_count()` → `0`；`torch.version.cuda` → `12.8`（wheel 本身帶 CUDA，缺的是裝置存取）。
  - 對照 `README.md:121`–`123`：本機先前已在 `cuda:0` 上跑完整 4K 批次，GPU 路徑本身可用。
- **計劃變更：**
  - `GOALS.md`「授權限制」：改寫 GPU 那條，記入兩個環境的實測差異，並要求所有交付數字在使用者 shell 量測。
  - `GOALS.md`「固定的度量約定」：新增第 6 條「執行裝置與決定性」——單次執行裝置固定、GPU 須設 `cudnn.benchmark = False`、決定性檢查在實際裝置上做、跨裝置數字不可並列比較。
  - `GOALS.md`「未解問題」：LPIPS 的瓶頸由 CPU 耗時改為 12227 MiB VRAM。
  - `PLANS.md`「已確認基線 / 資源」：記入裝置可見性修正、GPU 對照數字（`README.md:122` 的 0.220 秒），成本估算改為分裝置兩套。
  - `phases/phase-02`：LPIPS 裝置政策、決定性檢查須在實際裝置上通過、資源實測須在使用者 shell、新增兩項驗收條件。
  - `phases/phase-03`：cuda 可用性由 `Unresolved` 改為已解（GPU），量測須在使用者 shell，新增峰值 VRAM 與量測環境註明的驗收條件。
  - `phases/phase-04`：樣本上限預設值須綁在實測裝置上，報告標頭新增執行裝置與跨批次可比性欄位。
- **未變更：** 退化契約、PSNR／SSIM／LPIPS 的定義、階段順序與依賴、非目標、`AGENTS.md`。
- **限制：** 本次修訂**沒有任何 GPU 上的實測數字**。GPU 路徑的耗時、峰值 VRAM 與決定性全部仍未驗證，由 phase-02／03 在使用者 shell 補上。修訂中引用的 GPU 數字全部來自 `README.md` 既有紀錄，不是本計劃的觀察。
- **阻塞：** 無。但若實作在沙箱 session 內進行，真實資料的執行與量測必須交由使用者的 shell，否則 phase-02／03／05 的資源與裝置驗收取不到證據。
- **下一步：** 提交未提交的計劃 bundle 與 `.gitignore`（見 `PLANS.md`「尚未提交的既有工作」），然後開始 phase-01（不需 GPU，沙箱內可完整執行）。
- **證據位置：** 本筆記錄。本次修訂的內容隨計劃 bundle 一併提交於 `7b995b8`（`.gitignore` 為 `4b87282`）。

## 2026-09-19 — 計劃修訂：採用批次 GPU 交接，需 GPU 的項目不再標 Blocked

- **狀態：** 五個階段仍為 `Not started`。純計劃修訂，沒有實作。
- **授權範圍：** 使用者於 2026-09-19 在兩個選項中選定「批次交接」（選項 B），取代原先「每個需要 GPU 的階段各自 `Blocked` 並停下」的行為。
- **要解決的問題：** 修訂前的寫法會讓 phase-02 因為「LPIPS 全尺寸資源實測必須在交付裝置上」這項驗收缺證據而標 `Blocked`，phase-04 依賴 02 因此不能開始，整個計劃停在那裡；而交接怎麼做（給哪個命令、輸出貼到哪、誰寫進 build-log）當時完全沒有規定。
- **計劃變更：**
  - `PLANS.md`：新增「GPU 交接協定」一節（分工原則、待 GPU 補測清單、五步交接程序、腳本的驗證責任）。
  - `PLANS.md`「停止並取得所需授權」：在「缺必要證據記 `Blocked`」那條加上唯一例外——協定列出的三類 GPU 項目推遲到清單，不標 `Blocked`；正確性檢查不適用此例外。
  - `PLANS.md`「整體完成標準」：新增一條，清單清空才算完成。
  - `build-log.md`：新增「待 GPU 補測」區塊與其狀態詞彙。
  - `PROMPTS.md`：啟動提示的必讀界線新增一條指向本協定；最終整合審查新增檢查清單是否清空。
  - `phases/phase-02`、`phases/phase-03`：新增「GPU 項目的處理」，說明哪些推遲、哪些沙箱內必須做完才可標 `Complete`；受影響的驗收條件標上「可推遲」。
  - `phases/phase-05`：新增產生、煙霧測試與回收交接腳本的範圍與驗收條件。
- **未變更：** 退化契約、度量定義（含第 6 條裝置與決定性）、階段順序與依賴、非目標、`AGENTS.md`。
- **限制：** 協定本身尚未被執行過一次，交接腳本還不存在。清單目前是空的，因為還沒有階段開始。
- **阻塞：** 無。
- **下一步：** 提交計劃 bundle 與 `.gitignore`，然後開始 phase-01（不需 GPU，沙箱內可完整執行）。
- **證據位置：** 本筆記錄。本次修訂的內容隨計劃 bundle 一併提交於 `7b995b8`。

## 2026-09-19 01:09 (CST) — Phase 01: preflight

- **狀態：** `Not started` → `In progress`
- **授權範圍：** [phases/phase-01-degradation-and-bicubic.md](phases/phase-01-degradation-and-bicubic.md)「實作與驗證計劃 / Preflight」。
- **本階段範圍（複述）：** 原圖探索（`input/` 直接子項的 png／jpg／jpeg，忽略子資料夾與其他副檔名）、原圖解碼（`Image.open` → 第一影格 → `exif_transpose` → `convert("RGB")`、>8-bit 略過）、mod-crop 到 4 的倍數、`BICUBIC` 降採樣成 LR PNG、**從磁碟上的 LR PNG** `BICUBIC` 放大回真值尺寸、建立一個新的 run 目錄。
- **非目標（複述）：** 不做 SR、不算度量、不裝依賴、不做報告與平均、不做 run 目錄防覆蓋規則、不動 `src/drone_sr/**`。
- **停止條件（複述）：** 若尺寸對齊必須靠第二次縮放，停止回報；若需修改 `src/drone_sr/**`，停止回報。
- **驗證（實際觀察）：**
  - `.venv/bin/python -c "import sys, PIL, torch, numpy; ..."` → Python `3.12.3`、Pillow `12.3.0`、torch `2.11.0+cu128`、numpy `2.5.3`、`torch.cuda.is_available()` → `False`。**量測環境：沙箱 session**；依 `GOALS.md`「授權限制」，`False` 是沙箱狀態，不是本機能力。本階段不需要 GPU。
  - `input/` 直接子項 744 個、無子資料夾（`find input -mindepth 1 -maxdepth 1 -type d | wc -l` → `0`）；副檔名分佈 `738 jpg`、`4 json`、`2 txt`、**0 png**。與 `PLANS.md`「已確認基線」一致。
  - `output/` 現況：`.gitkeep` 與 `whaledrone_seek10s_x1536_y768_512.png`（既有 SR 產物，不得更動）。
  - 基線雜湊清單（761 筆，涵蓋 `input/`、`output/`、`models/`、`src/**.py`、`tests/**.py`、`pyproject.toml`、`requirements-wsl.txt`）已存於 `$TMPDIR/baseline/manifest-before.txt`，供本階段結束時比對。
  - `git status --short` → 僅十二個沙箱裝置檔（`.bashrc`、`.claude/`、`.mcp.json` 等），與 `PLANS.md`「計劃 bundle 的提交狀態」記載一致，**不清理、不提交**。`HEAD` = `507f2a9`，分支 `main`。
  - `drone_sr` 以 editable 安裝於 `.venv`（`__editable__.drone_sr-0.1.0.pth`），任意工作目錄皆可 import，評估工具不需要調整 `sys.path`。
- **preflight 的實質發現（真實 MPO 的影格順序）：** 對 `input/DJI_20230127115759_0001_W.JPG` 實測 `n_frames = 2`，**frame 0 為 4056×3040 主圖、frame 1 為 960×720 縮圖**。因此 `GOALS.md` 退化契約第 1 條的「取第一影格」在這批資料上取到的是全解析度主圖，契約可照字面執行，不需要 `context/phase-01-context.md` 的例外處理。
- **解決 Unresolved（測試命令）：** 採用 `.venv/bin/python -m unittest discover -s evaluation`。已實測 unittest discovery 不會遞迴進入非 package 的子目錄（`$TMPDIR/dprobe` 探測：`sub/test_nested.py` 未被收集），因此 `evaluation/runs/`、`evaluation/phases/` 不會被掃到。評估檢查一律放在 `evaluation/` 之下，**不進入專案既有的 `tests/`**，也不用 `tests/` 的既有命令去掃評估程式。
- **Unresolved（維持）：** `input/` 仍為 0 張 PNG，PNG 原圖路徑只能以合成 fixture 驗證；結束時須記明「PNG 原圖僅以合成 fixture 驗證，尚未在真實 PNG 資料上執行」。
- **限制：** 本筆為唯讀 preflight，尚無任何實作或評估產物。
- **阻塞：** 無。
- **下一步：** 依 phase-01「Commit 切點」先提交定義驗收的檢查（red），再分四顆實作。
- **證據位置：** 本筆記錄。觀察時的 `HEAD` = `507f2a9`。本筆隨 `docs: start phase 01` 提交，該顆與本階段其餘 commit 的 hash 於 close 記錄一併列出（沿用 `507f2a9` 的既有做法，不用 `--amend` 回填）。

## 2026-09-19 01:15 (CST) — Phase 01: close

- **狀態：** `In progress` → `Complete`
- **授權範圍：** [phases/phase-01-degradation-and-bicubic.md](phases/phase-01-degradation-and-bicubic.md)。
- **變更：** 新增四個模組與四個檢查模組於 `evaluation/`：`sources.py`（探索與解碼）、`degradation.py`（mod-crop、降採樣、PNG 寫出）、`bicubic.py`（從磁碟 LR PNG 放大）、`runs.py`（建立 run 目錄）。未動 `src/drone_sr/**`、`tests/**` 或任何受保護路徑。
- **驗證（聚焦，實際觀察）：**
  - `.venv/bin/python -m unittest discover -s evaluation` → **`Ran 24 tests` `OK`**。
  - `.venv/bin/python -W error::DeprecationWarning -m unittest discover -s evaluation` → **`Ran 24 tests` `OK`**（refactor 前為 `FAILED (errors=5)`，肇因於 Pillow 12 已棄用的 `Image.getdata`）。
  - `.venv/bin/python -m unittest discover -s tests` → **`Ran 33 tests` `OK`**，每一顆 commit 後皆重跑並通過。
- **驗證（較廣，真實資料，實際觀察）：** run 目錄 `evaluation/runs/20260918T171502Z/`（UTC 命名；當地時間 2026-09-19 01:15 CST），取 `input/` 前兩張。
  - `DJI_20230127115759_0001_W.JPG`：原始 `(4056, 3040)` → 裁切後 `(4056, 3040)`、裁掉 `(0, 0)` → LR `(1014, 760)` → bicubic `(4056, 3040)`。
  - `DJI_20230127115802_0002_W.JPG`：同上尺寸鏈。
  - **兩條線對等性的直接證據：** 兩張的 bicubic PNG 與「另外獨立 `Image.open(lr.png).convert("RGB").resize(cropped_size, BICUBIC)`」逐位元相同（`tobytes()` 相等）→ `True`。
  - 六個中間檔的檔頭皆為 `89504e470d0a1a0a`（PNG magic），逐檔列出，無一例外。
  - 端到端（解碼→裁切→降採樣→寫 LR→從 LR 放大→寫 bicubic）每張 **5.10 秒 / 4.24 秒**。**量測環境：沙箱 session、CPU。** 這是退化與 bicubic 線的診斷數字，不是交付用的資源量測；可對外引用的單張成本由 phase-03／05 在使用者 shell 量。bicubic 線依 `GOALS.md`「固定的度量約定」第 6 條恆為 Pillow CPU 實作。
- **驗證（不變式，實際觀察）：** 761 筆雜湊清單（`input/`、`output/`、`models/`、`src/**.py`、`tests/**.py`、`pyproject.toml`、`requirements-wsl.txt`）執行前後 `diff` **完全相同**。`git status --short` 仍只列十二個沙箱裝置檔，與 preflight 一致。`git check-ignore -v evaluation/runs/20260918T171502Z/report.md` → 命中 `.gitignore:15`，run 產物不進版本控制。
- **驗收條件對照：** 八項全部由上述觀察滿足——尺寸往返（含 203×101 非 4 倍數案例：裁切成 200×100、LR 50×25、bicubic 200×100）、覆寫 LR 檔使 bicubic 輸出改變、獨立重算逐位元相同、探索規則、MPO 可解碼與 16-bit 明確拒絕、真實 4056×3040 尺寸鏈、PNG magic、受保護路徑未變動。
- **限制：**
  - **PNG 原圖僅以合成 fixture 驗證，尚未在真實 PNG 資料上執行。** `input/` 仍為 0 張 PNG。
  - 16-bit 拒絕只實作並驗證 PNG 的 IHDR 位深；探索只收 png／jpg／jpeg，Pillow 的 JPEG 解碼為 8-bit，因此目前沒有其他能抵達此檢查的深色深來源。
  - 兩張來源檔名 stem 相同時（例如同時存在 `a.png` 與 `a.JPG`）會寫到同一個輸出路徑。目前 `input/` 738 張檔名皆唯一，未觸發；phase-04 的執行器需決定是要視為單張失敗排除還是中止。
  - 上述耗時為沙箱 CPU 數字，非交付環境。
- **阻塞：** 無。本階段不需要 GPU，未產生「待 GPU 補測」項目。
- **下一步：** phase-02（度量模組與 `lpips` 依賴）。它與 01 互相獨立，依賴皆已滿足。
- **證據位置：** 本筆記錄；run 目錄 `evaluation/runs/20260918T171502Z/`（未進版本控制）。本階段 commit 依序為 `05d3c9f`（`docs:` start）、`b48088a`（`test:` red，24 項、4 個 import 錯誤）、`ea72bc8`（`feat:` sources）、`8d9f910`（`feat:` degradation）、`1b7ac51`（`feat:` bicubic，本階段核心）、`e7f030a`（`feat:` runs）、`b61477b`（`refactor:` 移除已棄用 API），close 記錄本身另成一顆。

## 2026-09-19 01:22 (CST) — Phase 02: preflight

- **狀態：** `Not started` → `In progress`
- **授權範圍：** [phases/phase-02-metrics-and-lpips.md](phases/phase-02-metrics-and-lpips.md)「實作與驗證計劃 / Preflight」。
- **本階段範圍（複述）：** 以 torch 自行實作 PSNR 與 SSIM、安裝 `lpips` 並包成穩定介面、建立 `evaluation/requirements.txt`、六組性質檢查、真實尺寸 LPIPS 資源實測（可推遲至 GPU 清單）。
- **非目標（複述）：** 不做退化／SR／報告；不裝 `lpips` 以外的套件；不動 `pyproject.toml` 與 `requirements-wsl.txt`；不加 Y 通道或 MS-SSIM。
- **停止條件（複述）：** 網路取不到套件或權重；`lpips` 需要與現有 torch 衝突的相依；需要第二個新套件；LPIPS 在真實尺寸 OOM 或單張數分鐘。**不得**改用縮圖後再算 LPIPS。
- **驗證（實際觀察）：**
  - `.venv/bin/python -c "import lpips"` → `ModuleNotFoundError`。確認目前確實沒有。
  - 安裝前版本：`torch 2.11.0+cu128`、`torchvision 0.26.0+cu128`、`pillow 12.3.0`、`spandrel 0.4.2`、`numpy 2.5.3`。完整 `pip list --format=freeze`（37 筆）存於 `$TMPDIR/baseline/pip-before.txt`。
  - `scipy`、`tqdm`、`skimage` 皆 **MISSING**。
  - 網路可用：`curl https://pypi.org/simple/lpips/` → `http=200`（0.94 秒）。
  - **`pip install --dry-run --report - lpips` 在 180 秒後被 `timeout` 殺掉（exit 143），全程無輸出。** 未進一步重試；改以 PyPI JSON API 與 wheel 內容做唯讀確認，成本遠低於讓 pip 解析含 torch 的相依樹。
- **preflight 的實質發現一（`lpips` 的相依）：** PyPI metadata（`https://pypi.org/pypi/lpips/json`）顯示 `lpips 0.1.4` 的 `requires_dist` 為 `torch>=0.4.0`、`torchvision>=0.2.1`、`numpy>=1.14.3`、**`scipy>=1.0.1`**、**`tqdm>=4.28.1`**。前三者已滿足且版本遠高於下限，**安裝不會動到既有 torch／torchvision**；後兩者是 venv 內尚不存在的套件。
  - 檢查 wheel 原始碼確認這不是可繞過的軟相依：`lpips/__init__.py:10` 為模組層級的 `from lpips.trainer import *`，而 `lpips/trainer.py` 在模組層級 `from scipy.ndimage import zoom` 與 `from tqdm import tqdm`。因此 **`import lpips` 硬性需要 scipy 與 tqdm**。
  - `skimage`、`rawpy`、`cv2` 的 import 全部位於函式內（`__init__.py` 第 24、28、44、57、76、80、88 行皆有縮排），不影響 import。
  - **這觸及 `PLANS.md`「停止並取得所需授權」的「需要 `lpips` 以外的任何新依賴」。** 依該條停止並向使用者確認，不自行安裝。詳見下一筆記錄。
- **preflight 的實質發現二（LPIPS 權重的來源分兩處）：** `lpips-0.1.4-py3-none-any.whl`（53763 bytes、SHA-256 `fd537af5828b69d2e6ffc0a397bd506dbc28ca183543617690844c08e102ec5e`、BSD、`https://github.com/richzhang/PerceptualSimilarity`）**本身就內含線性層權重** `lpips/weights/v0.1/alex.pth`（6009 bytes）。因此需要另外下載的只有 torchvision 的 AlexNet backbone 權重。這使「權重取不到」的風險小於計劃撰寫時的預期。
- **限制：** 本筆為唯讀 preflight 與網路唯讀查詢，尚未安裝任何套件，`.venv` 未變動。AlexNet backbone 權重尚未下載，其 URL／大小／SHA-256 尚未記錄。
- **阻塞：** `lpips` 的安裝等待使用者對 scipy 與 tqdm 的決定。PSNR 與 SSIM 不依賴此決定，先行實作。
- **下一步：** 先完成 PSNR 與 SSIM 及其性質檢查（不依賴該決策），再就 scipy／tqdm 取得授權。
- **證據位置：** 本筆記錄；`$TMPDIR/baseline/pip-before.txt`。commit 見本階段 close 記錄的清單。

<!-- 追加重要事件時用這個格式：

## <含時區的時間> — Phase <NN>: <事件>

- **狀態：** <原狀態> → <新狀態>
- **授權範圍：** 連結到該階段文件
- **變更：** 簡潔的實際變更
- **驗證：** 確切命令或程序與結果
- **審查：** 適用時的發現或簽核
- **限制：** 未測或已接受的限制
- **阻塞：** 目前阻塞或「無」
- **下一步：** 依 PLANS.md 的下一個可執行動作
- **證據位置：** context、review、log、產物或 commit
-->
