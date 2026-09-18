# Phase 03 — SR 線接上未修改的 pipeline

## 來源輸入

- `../GOALS.md`（固定的退化與放大契約第 4 條、必須保留的行為與不變式）
- `../PLANS.md`（已確認基線：可重用介面、模型 descriptor、資源）
- `src/drone_sr/image_io.py:24`、`src/drone_sr/image_io.py:41`、`src/drone_sr/inference.py:14`、`src/drone_sr/inference.py:44`
- `README.md:86-91`（自動分塊與資源）

## 目標

對 phase-01 產生的 LR PNG，透過**未修改的** `drone_sr` 公開函式產出 SR PNG，尺寸與 mod-crop 後的真值完全相同；整個過程中 `src/drone_sr/**` 逐位元不變，`output/` 未被寫入。同時量到單張的實際耗時、device 與峰值記憶體。

## 範圍內

- 以 import 方式重用 `read_image`、`load_model`、`upscale`、`write_png`。
- 啟動時斷言 `descriptor.scale == 4`；不是 4 就明確失敗，不自行補縮放。
- 斷言 SR 輸出尺寸等於真值尺寸。
- 模型只載入一次，逐張重用。
- 記錄 device、單張耗時、峰值 RSS。

## 非目標

- 不修改 `src/drone_sr/**` 的任何一行，不加參數、不加 hook、不做 monkey patch。
- 不複製或改寫推論／分塊邏輯到 `evaluation/`。
- 不換模型、不比較 SwinIR、不調 tile 大小。
- 不算度量、不做報告（phase-02／04）。

## 依賴與前提

- 依賴階段：01（需要它產出的 LR PNG 與尺寸鏈證據）。
- 需要 `models/model.pth` 存在且可載入。
- **已解（2026-09-19）：** 交付裝置是 **GPU**。使用者 shell 實測 `torch.cuda.is_available()` 為 `True`、`NVIDIA GeForce RTX 5070 Ti Laptop GPU`；coding agent 的沙箱 session 內為 `False`（GPU 被作業系統擋住）。2026-09-18 記錄的 `False` 是沙箱結果。**因此本階段的真實資料執行與所有資源量測必須在使用者的 shell 進行**；沙箱內只能跑小尺寸合成案例。device 仍須逐次記錄，不得假定。
- **Unresolved：** 4056×3040 真值對應的 1014×760 LR 在本機的單張端到端耗時、峰值 RSS 與峰值 VRAM。`README.md:86-91` 記載 4K 批次峰值 RSS 約 5.44 GiB、`README.md:122` 記載小案例的 GPU 峰值 allocated 約 264 MiB，但那都是主 pipeline 的量測，本階段要在交付裝置上自己量。

## 預期影響的元件

- 新增：`evaluation/` 下呼叫 SR 的模組（確切檔名由實作決定）。
- 讀取（唯讀 import）：`src/drone_sr/`。
- 寫入：`evaluation/runs/<timestamp>/sr/`。

## 授權與停止條件

- 常規：在 `evaluation/` 內實作、跑少量真實圖片的本機檢查。
- **停止：** 需要修改 `src/drone_sr/**` 才能完成本階段。這是回報的理由，不是動 pipeline 的理由。
- **停止：** `descriptor.scale != 4`。整個比較建立在 4× 上，不得自行用 resize 補足差額。
- **停止：** 單張耗時或記憶體導致小樣本執行預估超過約十分鐘。

## 實作與驗證計劃

### Preflight

- 記錄 `src/drone_sr/*.py` 的 SHA-256 與 `output/` 的檔案清單，供結束時比對。
- `.venv/bin/python -c "import torch; print(torch.cuda.is_available())"` 記錄 device 實況，**並記明這次是在沙箱 session 還是使用者 shell 執行**。兩個環境的結果不同（見「依賴與前提」），混記會讓後續的耗時數字無法判斷屬於哪個裝置。
- 載入 descriptor 並印出 `scale`、`purpose`、`input_channels`、`output_channels`。

### Red

1. **倍率斷言：** 以一個 scale 不是 4 的假 descriptor（或直接檢查斷言邏輯）確認會明確失敗，而不是靜默繼續。
2. **尺寸對齊：** 對一張小的合成 LR PNG（例如 25×50），SR 輸出應為 100×200，與真值尺寸相同。
3. **輸入來源：** SR 線讀的是磁碟上的 LR PNG。以與 phase-01 相同的手法驗證：覆寫 LR 檔後 SR 輸出隨之改變。

### Green

實作最小的呼叫層：載入一次 descriptor，逐張 `read_image(lr_png)` → `upscale` → `write_png`。錯誤逐張隔離，單張失敗不中止整批，並帶回可記錄的原因。

### Refactor

不預期。

### Verification

- **聚焦：** 上述三項檢查通過（小尺寸合成 LR，成本低）。
- **較廣（真實資料）：** 對 1–2 張真實 4056×3040 原圖走完 phase-01 + 本階段，確認 SR 輸出為 4056×3040，開啟檢視內容正常（不是噪點、不是全黑、色彩正常）。
- **不變式：** 執行後 `src/drone_sr/*.py` 的 SHA-256 與 preflight 相同；`output/` 檔案清單與雜湊未變；`git status --short src tests pyproject.toml requirements-wsl.txt models` 為空。
- **既有測試不受影響：** 收尾時跑一次 `.venv/bin/python -m unittest discover -s tests`，確認既有測試仍全數通過（`fix/PLANS.md` 記載基線為 29 個測試加上該計劃新增的測試；以實際輸出為準）。
- **資源（可對外引用的數字須在使用者的 shell 量）：** 記錄 device、單張端到端耗時、峰值 RSS 與峰值 VRAM。
- **失敗行為：** 任一不變式被破壞，本階段立即 `Blocked`，phase-04 不得開始，先回復並診斷。
- **GPU 項目的處理：** GPU 上的耗時與峰值 VRAM 沙箱內做不到，依 `../PLANS.md`「GPU 交接協定」推遲到「待 GPU 補測」清單，**不標 `Blocked`**。三項聚焦檢查、真實 4056×3040 案例的尺寸與目視（沙箱內以 CPU 執行，成本約十餘秒）、以及 pipeline 不變式在沙箱內通過即可標 `Complete`。

## 可靠性、安全與復原

- `write_png` 本身是原子寫入且會拒絕覆寫來源，與本階段的隔離要求一致。
- 主要風險是**無意間污染主 pipeline 或其輸出**。因此 preflight 的雜湊快照與結束比對是必要證據，不可省略成「我沒有改它」。
- 記憶體風險：4056×3040 的 float32 RGB 結果本體約 1.48 GiB（`README.md:90`）。本階段同時只處理一張，處理完即釋放。

## 驗收條件

- [ ] `descriptor.scale == 4` 已實際觀察並記錄。
- [ ] 小尺寸合成案例的 SR 輸出尺寸等於真值尺寸。
- [ ] 覆寫 LR 檔會改變 SR 輸出（證明讀的是磁碟檔）。
- [ ] 真實 4056×3040 案例走通，輸出已開啟目視確認內容正常。
- [ ] `src/drone_sr/*.py` 雜湊未變；`output/` 未變；相關 manifest 未變。
- [ ] 既有測試套件仍全數通過。
- [ ] 沙箱（CPU）的 device、單張耗時與峰值 RSS 已記錄，並註明量測環境。
- [ ] 交付裝置（GPU）上的單張耗時、峰值 RSS 與峰值 VRAM 已量測（**可推遲至「待 GPU 補測」清單**）。

## Commit 切點

實作段建議兩顆：

1. `feat: load the SR descriptor and assert 4x scale` — 載入一次、斷言 `scale == 4`。body 記 descriptor 的實際欄位值與 device。
2. `feat: run the SR line from the LR png` — 逐張 `read_image` → `upscale` → `write_png`，尺寸斷言與逐張失敗隔離。body 記單張耗時、峰值 RSS，以及 `src/drone_sr/*.py` 雜湊前後一致、既有測試通過數。

本階段不得出現任何修改 `src/drone_sr/**` 的 commit。若歷史上出現這種 commit，代表違反了計劃的核心不變式。

## 要記錄的證據

- descriptor 的實際欄位值。
- 雜湊比對的方式與結果（前後一致）。
- 既有測試的實際輸出摘要（通過數）。
- device、耗時、峰值 RSS 的實測數字，以及據此對小樣本規模的建議。
- 若實測顯示成本會改變 phase-05 的樣本規劃，寫 `../context/phase-03-context.md` 並更新 phase-04／05。

## 交接

- phase-04 可以開始的條件：SR 線與 bicubic 線都能從同一個 LR PNG 產出尺寸相同的結果，且 pipeline 不變式有證據。
- 留給後續階段：批次執行、run 目錄防覆蓋、報告與平均屬於 phase-04。
