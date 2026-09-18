# Phase 01 — 固定退化契約與 bicubic 基線

## 來源輸入

- `../GOALS.md`（特別是「固定的退化與放大契約」與「必須保留的行為與不變式」）
- `../PLANS.md`
- `src/drone_sr/image_io.py:24`（`read_image()` 的解碼語意，本階段要對齊其 RGB／EXIF 行為，但不得呼叫它讀原圖）
- 真實資料：`input/`（738 張 MPO JPEG、0 張 PNG）

## 目標

給定一張高解析原圖，可觀察地產生：一張 mod-crop 後的真值、一張 LR PNG（寬高各為真值的 1/4）、一張 bicubic PNG（尺寸與真值完全相同，且可證明是從磁碟上的 LR PNG 放大而來）。三者都寫在一個新的 `evaluation/runs/<timestamp>/` 目錄下。

## 範圍內

- 原圖探索：列出 `input/`（可由參數覆寫）**直接子項**中副檔名為 `.png`、`.jpg`、`.jpeg`（大小寫不敏感）的檔案，穩定排序。忽略子資料夾與所有其他副檔名。
- 原圖解碼：Pillow `Image.open` → `ImageOps.exif_transpose` → `convert("RGB")`，多影格來源取第一影格；每通道 > 8-bit 的來源略過並記錄原因。
- mod-crop：自右／下裁到寬高皆為 4 的倍數，逐張記錄原始尺寸、裁切後尺寸與裁掉的像素數。
- 降採樣：`Image.Resampling.BICUBIC`，輸出 `(W // 4, H // 4)` 的 PNG。
- bicubic 放大：**重新從磁碟開啟 LR PNG**，`Image.Resampling.BICUBIC` 放大回真值尺寸，輸出 PNG。
- run 目錄建立與子目錄配置（`hr/`、`lr/`、`bicubic/` 或等價結構）。

## 非目標

- 不做 SR（phase-03）。
- 不算任何度量、不裝任何依賴（phase-02）。
- 不做報告、不做平均、不做 run 目錄的防覆蓋規則（phase-04 擁有完整的 run 生命週期；本階段只要能建立一個新目錄即可）。
- 不修改 `src/drone_sr/**`。

## 依賴與前提

- 依賴階段：無。
- 需要 `.venv` 內既有的 Pillow 12.3.0，不需要新依賴、不需要網路、不需要模型。
- **Unresolved：** 是否有原圖為 PNG 的樣本可測。`input/` 目前 0 張 PNG，PNG 路徑必須以自建 fixture 驗證，並在 build-log 記明「PNG 原圖僅以合成 fixture 驗證，尚未在真實 PNG 資料上執行」。

## 預期影響的元件

- 新增：`evaluation/` 下的退化模組與影像 I/O（確切檔名由實作決定，例如 `evaluation/degradation.py`）。
- 讀取：`input/`（唯讀）。
- 寫入：`evaluation/runs/<timestamp>/`、`$TMPDIR` 內的 fixture。

## 授權與停止條件

- 常規：建立與修改 `evaluation/` 下的檔案、產生 fixture、跑本機便宜檢查。
- **停止：** 若發現要達成尺寸對齊就必須對放大結果再縮放一次，停下來回報，不得自行引入第二次縮放（違反 `GOALS.md` 的固定契約）。
- **停止：** 若需要修改 `src/drone_sr/**` 才能完成本階段。

## 實作與驗證計劃

### Preflight

- 確認 `.venv/bin/python -c "import PIL; print(PIL.__version__)"` 為 12.3.0。
- 確認 `input/` 現況（張數、副檔名分佈、是否有子資料夾）。
- 記錄 `input/` 與 `output/` 的目前狀態，供結束時比對。

### Red

先寫最小的失敗檢查，再實作。至少涵蓋：

1. **尺寸往返：** 對一張合成的 `H×W` 原圖（挑 `H`、`W` **不是** 4 的倍數的尺寸，例如 101×203），mod-crop 後應為 100×200，LR 應為 25×50，bicubic 輸出應為 100×200。
2. **來源真的是 LR 檔：** 產生 LR PNG 後，在放大之前把該檔覆寫成另一張明顯不同的圖，bicubic 輸出必須跟著改變。若輸出不變，代表 bicubic 線讀的不是磁碟上的 LR 檔。
3. **獨立重算：** bicubic 輸出必須與「另外獨立開啟該 LR PNG 並以相同參數 resize」的結果逐像素相同。
4. **探索規則：** 在含有 `a.png`、`b.JPG`、`c.jpeg`、`d.txt`、`e.json` 與一個子資料夾（內含 `f.png`）的 fixture 目錄上，只列出 `a.png`、`b.JPG`、`c.jpeg`。
5. **多影格來源：** 對一張 MPO 或多影格來源，解碼結果尺寸等於第一影格尺寸，不拋例外。
6. **高位深拒絕：** 16-bit PNG 原圖被略過並帶明確原因，不被靜默截斷。

### Green

實作滿足上述檢查所需的最小行為，不把 phase-03／04 的工作提前。

### Refactor

不預期需要獨立的 refactor。若有，限於本階段範圍，之後重跑聚焦檢查。

### Verification

- **聚焦：** 上述 red 檢查全部通過。實作為獨立腳本或 `unittest`；若用 `unittest`，放在 `evaluation/` 之下，**不得**放進專案既有的 `tests/`。
- **較廣：** 在真實資料上跑 1–2 張（例如 `input/DJI_20230127115759_0001_W.JPG`），確認：原始 4056×3040 → 裁切後仍為 4056×3040（裁切量 0）→ LR 1014×760 → bicubic 4056×3040。
- **檔案格式：** 以檔頭 magic（`\x89PNG\r\n\x1a\n`）確認所有中間檔都是 PNG。
- **不變式：** 執行前後比對 `input/`、`output/`、`src/drone_sr/` 的檔案清單與雜湊，確認未變動。`git status --short` 與階段開始時一致（除了 `evaluation/` 新增物）。
- **Unresolved：** 專案目前沒有為評估工具設定的測試命令。preflight 時決定用 `.venv/bin/python -m unittest discover -s evaluation` 或直接執行腳本，並把實際採用的命令寫進 build-log；不要沿用 `tests/` 的既有命令去掃到評估程式。
- **失敗行為：** 任一聚焦檢查失敗，本階段維持 `In progress`，phase-03 不得開始。

## 可靠性、安全與復原

- 寫入只發生在新建的 `evaluation/runs/<timestamp>/` 與 `$TMPDIR`，不觸碰既有資料，無需回滾程序。
- 主要風險是**靜默的不對等**（bicubic 偷用原圖衍生物），因此上面第 2、3 項檢查是本階段的核心，不可簡化成「輸出尺寸對就好」。

## 驗收條件

- [ ] 合成 fixture 的尺寸往返檢查全部通過，包含寬高非 4 倍數的情況。
- [ ] 覆寫 LR 檔會改變 bicubic 輸出（證明讀的是磁碟檔）。
- [ ] bicubic 輸出與獨立重算結果逐像素相同。
- [ ] 探索規則只取直接子項的 png／jpg／jpeg，忽略子資料夾與其他副檔名。
- [ ] 多影格 MPO 來源可解碼；16-bit 來源被明確略過並記錄原因。
- [ ] 真實 4056×3040 樣本的完整尺寸鏈已實際觀察並記錄。
- [ ] 所有中間檔經 magic 檢查為 PNG。
- [ ] `input/`、`output/`、`src/drone_sr/` 未變動。

## Commit 切點

依 `../PLANS.md`「版本控制節奏與可追溯性」拆分。實作段建議四顆，每顆各自可被檢查、可單獨 revert：

1. `feat: discover and decode evaluation source images` — 列檔規則（直接子項的 png／jpg／jpeg、忽略子資料夾與其他副檔名）、`exif_transpose`、第一影格、>8-bit 略過。body 記在真實 `input/` 上列出的張數。
2. `feat: add mod-crop and fixed bicubic downscale` — 裁到 4 的倍數並降採樣成 LR PNG。body 記真實樣本的尺寸鏈與裁切量。
3. `feat: upscale the bicubic baseline from the LR file` — 從磁碟 LR PNG 放大回真值尺寸。body 記「覆寫 LR 檔輸出隨之改變」與「獨立重算逐像素相同」兩項觀察。
4. `feat: create a fresh evaluation run directory` — run 目錄建立（防覆蓋規則屬 phase-04）。

第 3 顆是本階段的核心，單獨成顆的理由：兩條線是否對等的證據集中在它身上，日後若懷疑比較不公平，要能只看這一顆的 diff。

## 要記錄的證據

- 實際採用的檢查命令與結果，寫進 `../build-log.md`。
- 真實樣本的尺寸鏈與裁切量。
- 若發現 `GOALS.md` 的契約在某類來源上無法照字面執行（例如某種來源格式的第一影格不是全解析度主圖），寫 `../context/phase-01-context.md`，並在繼續前更新受影響的未開始階段。

## 交接

- phase-03 可以開始的條件：本階段的 LR PNG 產出穩定，且尺寸鏈證據已記錄。
- 留給後續階段：run 目錄的防覆蓋與命名規則屬於 phase-04；本階段只需能建立一個新目錄。
