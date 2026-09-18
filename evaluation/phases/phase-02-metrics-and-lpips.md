# Phase 02 — 度量模組與 lpips 依賴

## 來源輸入

- `../GOALS.md`（特別是「固定的度量約定」與「授權限制」）
- `../PLANS.md`（已確認基線：`.venv` 沒有 lpips／torchmetrics／scikit-image）
- `README.md:93-107`（專案記錄外部權重的既有慣例：URL、位元組大小、SHA-256、授權）

## 目標

`evaluation/` 內存在一個度量模組，對兩張同尺寸的 8-bit RGB 影像可算出 PSNR、SSIM、LPIPS，三者皆通過性質檢查與決定性檢查；`lpips` 已釘版記錄於 `evaluation/requirements.txt`，其預訓練權重的來源與 SHA-256 已記錄。

## 範圍內

- 以 torch 自行實作 PSNR 與 SSIM，遵守 `GOALS.md` 的固定度量約定。
- 安裝 `lpips` 並取得其預訓練權重；包成穩定的呼叫介面。
- 建立 `evaluation/requirements.txt`，釘住 `lpips` 版本。
- 度量正確性的觀察證據。
- 實測 LPIPS 在真實 4056×3040 尺寸上的耗時、峰值 RSS 與峰值 VRAM（在交付裝置上，見「依賴與前提」）。

## 非目標

- 不做退化、不做 SR、不做報告。
- 不裝 `lpips` 以外的任何套件（`scikit-image`、`torchmetrics`、`piq` 皆不在授權內）。
- 不修改 `pyproject.toml` 或 `requirements-wsl.txt`。
- 不新增 Y 通道、multi-scale SSIM 或其他 `GOALS.md` 未列的度量。

## 依賴與前提

- 依賴階段：無（與 phase-01 獨立）。
- 需要網路以安裝套件與下載權重。
- **Unresolved：** 沙箱或本機網路是否允許取得 `lpips` 套件與其 AlexNet backbone 權重。preflight 先確認；取不到就把本階段標 `Blocked` 並回報，**不得**改用未授權的替代套件，也不得跳過 LPIPS 繼續往下做。
- **Unresolved：** SSIM 是否有可用的獨立實作可做一次交叉核對。`scikit-image` 不在授權內，因此預設沒有。以性質檢查為必要證據，交叉核對列為加分項；若無法交叉核對，必須在 build-log 與最終報告記為限制。
- **Unresolved：** LPIPS 在 4056×3040 上的資源需求未知。**交付裝置是 GPU**（2026-09-19 使用者 shell 實測 `True`；沙箱 session 內看不到 GPU，見 `../GOALS.md`「授權限制」），因此主要風險是 **12227 MiB VRAM** 而非 CPU 耗時。真實尺寸的量測必須在使用者的 shell 執行；沙箱內只能做小尺寸的便宜檢查。
- **Unresolved：** LPIPS 的執行裝置。依 `../GOALS.md`「固定的度量約定」第 6 條，單次執行內裝置固定並寫進報告標頭。預設與 SR 線同裝置；只有在 VRAM 不足時才落到 CPU，且該次結果屬於不同批次，不可與 GPU 批次並列。

## 預期影響的元件

- 新增：`evaluation/metrics.py`（或等價命名）、`evaluation/requirements.txt`。
- 變更：既有 `.venv`（安裝 `lpips` 及其相依）。
- 下載：LPIPS 權重（存放位置依 `lpips` 套件預設，通常在套件內與 torch hub 快取；不要放進 `models/`）。

## 授權與停止條件

- 常規：安裝 `lpips`、下載其權重、寫 `evaluation/requirements.txt`、跑本機檢查。
- **停止並回報：** 網路不可用或權重取不到；`lpips` 需要與現有 torch 2.11.0 衝突的相依版本；需要任何第二個新套件。
- **停止並回報：** LPIPS 在真實尺寸上 OOM 或單張超過數分鐘。**不得**自行改成「縮小後再算 LPIPS」——那會改變度量定義，屬於 `GOALS.md` 固定約定的變更。GPU 上 OOM 時，先確認 SR 與 LPIPS 之間確實釋放了張量並呼叫過 `torch.cuda.empty_cache()`；仍 OOM 才回報，並在回報中一併給出 CPU 備援的實測成本，讓使用者能在兩者間選擇。

## 實作與驗證計劃

### Preflight

- `.venv/bin/python -c "import lpips"` 確認目前確實沒有。
- 確認安裝 `lpips` 不會升級或降級既有的 `torch`／`torchvision`（先用 pip 的 dry-run 或 `--no-deps` 加手動檢查；若會動到 torch，停止並回報）。
- 記錄安裝前 `pip list` 的相關項目，供結束時比對。

### Red

先寫失敗的性質檢查，再實作：

1. **同圖對自己：** PSNR 為 `inf`、SSIM 為 `1.0`（誤差 ≤ 1e-6）、LPIPS ≈ 0（≤ 1e-4）。
2. **PSNR 手算對照：** 對一組已知常數差的影像（例如整張差 1/255），PSNR 應等於手算的 `10 * log10(255**2 / 1)` ≈ 48.13 dB。
3. **單調性：** 對同一張圖疊加遞增強度的高斯雜訊，PSNR 單調下降、SSIM 單調下降、LPIPS 單調上升。
4. **值域：** SSIM 落在 `[-1, 1]`；LPIPS 對「bicubic 放大 vs 原圖」這種真實案例明顯 > 0 且 < 1。
5. **決定性：** 同樣輸入連跑兩次，三個指標的值完全相同（LPIPS 須設 `eval()` 與 `torch.inference_mode()`）。**此檢查必須在實際執行的裝置上通過**：GPU 路徑另須設 `torch.backends.cudnn.benchmark = False`，並在使用者的 shell 重跑一次。沙箱內 CPU 的決定性結果**不能**代表 GPU 路徑，因為 TF32 與 cuDNN 演算法選擇會讓數值漂移。
6. **對稱性與尺寸檢查：** 交換兩張輸入，PSNR／SSIM 不變；尺寸不同時拋出明確錯誤，不靜默縮放。

### Green

實作滿足上述檢查所需的最小行為。SSIM 使用 Gaussian window 11×11、σ=1.5、K1=0.01、K2=0.03，三通道各算後平均，邊界處理方式在程式內註明並寫進報告標頭。

### Refactor

不預期。若調整 SSIM 的張量實作，之後必須重跑全部性質檢查。

### Verification

- **聚焦：** 上述六組性質檢查全部通過。
- **交叉核對（加分，可能不可得）：** 若能在不新增專案依賴的前提下取得第二份 SSIM 實作，對同一組輸入比對；不可得則記為限制。
- **資源實測（須在使用者的 shell 執行）：** 以一張真實 4056×3040 影像與其 bicubic 版本算一次 LPIPS，記錄耗時、峰值 RSS、**峰值 VRAM** 與所用 device。沙箱 session 看不到 GPU，這項量測若在沙箱內執行只會得到 CPU 數字，不可當成交付環境的證據。
- **依賴隔離：** 安裝後確認 `torch`、`torchvision`、`Pillow`、`spandrel` 版本未變；`pyproject.toml` 與 `requirements-wsl.txt` 未被修改；`git status --short` 只多出 `evaluation/` 的新增物。
- **權重記錄：** 依 `README.md` 既有慣例記下 LPIPS 權重的來源 URL、位元組大小與 SHA-256。
- **Unresolved：** 測試命令與 phase-01 採用同一個（見 phase-01 的同名項目）。
- **失敗行為：** 任一性質檢查失敗，本階段維持 `In progress`；phase-04 不得開始。權重取不到則標 `Blocked`。
- **GPU 項目的處理：** 真實尺寸的資源實測與 GPU 上的決定性檢查沙箱內做不到，依 `../PLANS.md`「GPU 交接協定」推遲到「待 GPU 補測」清單，**不標 `Blocked`**。六組性質檢查在沙箱內（CPU）全部通過即可標 `Complete` 並讓 phase-04 開始。本階段結束時另須產出 LPIPS 全尺寸的探測腳本交給使用者（協定第 1 步）。

## 可靠性、安全與復原

- 安裝與下載是本計劃唯一的外部動作。只安裝 `lpips`，只下載其所需權重，並記錄雜湊，讓後續能確認用的是同一份權重。
- 主要風險是**看似合理但系統性偏差的度量**。這種錯誤不會讓程式崩潰，只會讓結論失真，所以性質檢查是必要證據而非形式；只跑得出數字不算通過。
- 回滾：若安裝 `lpips` 動到既有 torch，`.venv` 可依 `requirements-wsl.txt` 重建。發生此情況先停止並回報，不要自行重建環境。

## 驗收條件

- [ ] 六組性質檢查全部以實際輸出通過，數值記在 build-log。
- [ ] `evaluation/requirements.txt` 存在且釘住 `lpips` 版本。
- [ ] LPIPS 權重的 URL、大小與 SHA-256 已記錄。
- [ ] `torch`、`torchvision`、`Pillow`、`spandrel` 版本與安裝前相同。
- [ ] `pyproject.toml`、`requirements-wsl.txt`、`src/`、`tests/` 未變動。
- [ ] 真實尺寸的 LPIPS 耗時、峰值 RSS 與峰值 VRAM 已在交付裝置（使用者 shell 的 GPU）上實測並記錄（**可推遲至「待 GPU 補測」清單**）。
- [ ] 決定性檢查已在沙箱的 CPU 上通過。
- [ ] 同一決定性檢查已在 GPU 上通過且設了 `cudnn.benchmark = False`（**可推遲至「待 GPU 補測」清單**）。
- [ ] LPIPS 全尺寸的探測腳本已在沙箱內煙霧測試過，並交給使用者。
- [ ] SSIM 交叉核對的狀態（已做／不可得）已明確記錄。

## Commit 切點

實作段建議四顆。三個度量分開的理由：任何一個算錯都會讓報告數字系統性偏差，分開才能單獨 bisect 與 revert。

1. `chore: pin lpips for the evaluation tool` — 只動 `evaluation/requirements.txt`。body 記安裝後 `torch`／`torchvision`／`Pillow`／`spandrel` 版本未變，以及 LPIPS 權重的 URL、大小與 SHA-256。
2. `feat: add PSNR with a fixed RGB 255 data range` — body 記同圖 `inf`、常數差 1/255 約 48.13 dB 的實測值。
3. `feat: add SSIM with a fixed Gaussian window` — body 記同圖 1.0、單調性、決定性的實測值，以及交叉核對的狀態（已做／不可得）。
4. `feat: wrap LPIPS alex for the evaluation metrics` — body 記同圖 ≈0、真實案例落在 (0,1)、所用 device，以及 4056×3040 的耗時、峰值 RSS 與峰值 VRAM。

## 要記錄的證據

- 每組性質檢查的實際數值，不只是「通過」。
- 安裝命令、安裝後的版本清單差異。
- LPIPS 權重來源與雜湊。
- 真實尺寸 LPIPS 的耗時、峰值 RSS、峰值 VRAM 與所用 device，以及量測環境（沙箱 session 或使用者 shell）。
- 若 LPIPS 的資源需求會改變 phase-04／05 的樣本規模規劃，寫 `../context/phase-02-context.md` 並更新受影響的未開始階段。

## 交接

- phase-04 可以開始的條件：三個度量都有通過的性質檢查證據，且 LPIPS 在真實尺寸上被證明可執行。
- 留給後續階段：度量的批次呼叫、平均計算與失敗處理屬於 phase-04。
