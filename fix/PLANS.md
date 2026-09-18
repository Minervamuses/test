# fix — 執行計劃

## 概要

- 計劃根目錄：專案根目錄的 `fix/`。
- 目標：[GOALS.md](GOALS.md)。
- 專案形態：minimal，單用途本機 CLI；本次只動一個函式與其測試與文件。
- 風險：**medium**。改動面積小，但位置在所有圖片的必經路徑上，且 phase-01 有一個會靜默破壞既有防護的順序陷阱（見下）。無遠端服務、無資料遷移、無依賴變更。
- 執行模式：**Autonomous within authorization envelope**。使用者啟動實作後，在下列授權範圍內依序實作與驗證，不為一般可逆操作重複詢問。
- 三階段依序關閉：方向正確性、位深拒絕完整性、文件對齊與整體驗收。每階段即時驗證，不把檢查留到最後。

## 資訊唯一來源

| 資訊 | 所屬檔案 |
|---|---|
| 目標、成功條件、限制、非目標、不變式 | `GOALS.md` |
| 順序、依賴、授權、停止條件、修訂規則 | `PLANS.md` |
| 啟動／續作提示 | `PROMPTS.md` |
| 各階段工作與預定檢查 | `phases/phase-*.md` |
| 實作狀態與觀察證據 | `build-log.md` |
| 重要實作發現 | `context/phase-NN-context.md`，必要時才建立 |
| 實際程式審查 | `code_review/phase-NN-review.md`，審查時才建立 |

沿用已完成 V1 的慣例，以 `phases/` 存放階段文件，避免 `fix/fix/` 重複命名。初始不建立 `context/` 或 `code_review/`。

## 已確認基線

以下為 2026-09-18 在專案 `.venv`（Python 3.12.3、Pillow 12.3.0、torch 2.11.0+cu128）的**唯讀調查觀察**，不是本計劃的實作證據。所有臨時檔在 `$TMPDIR`，未修改任何專案檔。

### 程式結構

- `read_image()` 位於 `src/drone_sr/image_io.py:13-18`，是專案唯一的「檔案 → tensor」解碼點。`src/` 內 `Image.open` 只出現在此一處；`__main__.py:52` 匯入它，`test-data/*/validate_*.py` 的 `pil_to_tensor` 只用於比對既有輸出，不是第二條讀圖路徑。
- 現行守門依序為：mode 白名單（`image_io.py:14`）→ `n_frames` 檢查（`:16-17`）→ `convert("RGB")` 與 tensor 轉換（`:18`）。
- `read_image()` 失敗時由 `__main__.py:71-84` 捕捉，記為該張 Failed 並繼續下一張，退出碼 1。**位深拒絕不需要新增錯誤處理路徑。**

### EXIF 方向

- 八個 Orientation 值以 40×20、四角標記的 JPEG 實測：只有 1 正確；**2、3、4 尺寸正確但像素錯誤**；5、6、7、8 尺寸與像素皆錯（輸出 40×20，正確應為 20×40）。
- 同樣的失敗模式適用於帶 eXIf chunk 的 PNG。
- **TIFF 目前是對的，但不是本專案處理的。** Pillow 在 `TiffImagePlugin.py:1328` 自行呼叫 `ImageOps.exif_transpose(self, in_place=True)` 並刪除 tag 274；`JpegImagePlugin` 與 `PngImagePlugin` 沒有對應呼叫。因此在 `read_image()` 內呼叫 `exif_transpose()` 對 TIFF 是 no-op，不會旋轉兩次。
- `write_png()` 輸出經位元組層級 chunk 掃描只有 `IHDR`／`IDAT`／`IEND`，無 `eXIf`，`getexif()` 回空 dict。
- 以真實 Compact 權重實測（32×28 真實裁切，正確方向 SR 對比旋轉後 SR 再轉回）：61.12% 像素有差異，但最大差 8/255、平均 0.76/255。模型非旋轉等變，但**使用者實際受害的是朝向錯誤，不是畫質變化**；文件與驗收不應把後者說成主要危害。

### `exif_transpose()` 可行性

- 對 `read_image()` 接受的七種 mode（`1`、`L`、`LA`、`P`、`RGB`、`RGBA`、`CMYK`）皆正常，回傳新物件。
- 無 EXIF 時為安全 no-op；套用後 tag 274 被清除，連呼叫兩次結果穩定（不會重複旋轉）。
- 不修改磁碟上的來源檔（前後 SHA-256 相同）。
- 回傳物件在 `with Image.open(...)` 區塊結束後仍可使用，無 use-after-close 問題。
- **順序陷阱：** 回傳的是 `Image` 而非 `TiffImageFile`，`getattr(img, "n_frames", 1)` 由 2 變成 1。實測：`original: TiffImageFile n_frames=2` → `transposed: Image n_frames=1`。**若置於 `n_frames` 檢查之前，多頁 TIFF 拒絕會靜默失效。**

### 來源位深

- 真正的 16-bit 彩色來源被靜默接受並截斷：PNG `IHDR bitdepth=16 colortype=2`、TIFF `BitsPerSample=(16,16,16)`，來源通道值 `[256, 257, 511]` 全部變成 8-bit `[1, 1, 1]`。
- 破口涵蓋 PNG colortype **2、4、6**（分別映射為 `RGB`、`RGBA`、`RGBA`）；只有 colortype 0（灰階，映射為 `I;16`）會被現行 mode 檢查擋下。
- 既有測試 `tests/test_image_io.py:49` 的 fixture `Image.new("I;16", (2,2)).save(...)` 實際寫出 `IHDR bitdepth=16 colortype=0`，讀回 `I;16`。它只證明單一灰階 mode 名稱被拒絕，走的是 mode 查表路徑，**原理上無法涵蓋 16-bit 彩色**。
- 偵測可行性（皆在 `load()` 觸發轉換之前可得）：
  - TIFF：`im.tag_v2.get(258)`（`BitsPerSample`），實測 16-bit 灰階回 `(16,)`、16-bit RGB 回 `(16, 16, 16)`。
  - PNG：檔案 IHDR 第 24 個位元組即位深（PNG 規格固定位置），可直接讀檔頭。另可交叉核對 `im.tile[0].args`，16-bit 為 `'RGB;16B'`、8-bit 為 `'RGB'`；但 `im.tile`／`im.png` 屬內部介面，且 `im.png` 在 `load()` 後變成 `None`。**建議以容器層級檢查為主，內部屬性最多作為交叉核對。**

### 既有驗證與素材

- `.venv/bin/python -m unittest discover -s tests` → `Ran 29 tests ... OK`，執行前後 `git status` 一致，不修改追蹤檔。
- 目前 repo 內 35 張可開啟圖片全部是 8-bit RGB PNG、Orientation 皆為 `None`（影片抽幀）。唯一的 JPEG `test-data/phase-02-cli-20260917/default run/input/a_good.JPG` 的 EXIF 為空。**沒有任何現成素材能驗證本次修正**，phase-01／02 必須自建 fixture。
- `models/model.pth` → `realesr-general-x4v3.pth`（Compact）存在；SwinIR 權重亦在。
- 本次調查環境 `torch.cuda.is_available()` 為 False。

## 執行授權

### 啟動後的常規範圍

使用者啟動實作後，下列動作不需重複詢問：

- 修改 `src/drone_sr/image_io.py` 在本計劃範圍內的部分。
- 於 `tests/test_image_io.py` 新增或調整本計劃所需測試，並在 `$TMPDIR` 或測試自建的暫存目錄產生 fixture。
- 修改 `README.md` 中與方向、位深相關的敘述。
- 執行本機便宜檢查（`unittest`、小型真實批次）。
- 維護 `fix/build-log.md`、必要的 `fix/context/`，以及被新證據影響的未開始階段文件。
- 沿用 V1 慣例：每個完成步驟 commit 到目前分支。

### 停止並取得所需授權

- 目標、成功條件、非目標或必須保留的行為需要改變。
- 需要新增依賴、變更 `pyproject.toml`／`requirements-wsl.txt`／`.venv`，或改變公共介面。
- 需要 push、merge、rebase、切換分支或其他 worktree 變更。
- 需要 credentials、外部寫入、下載、雲端或付費服務。
- 預期超過約十分鐘、全資料集重跑或模型／GPU 掃描的工作。
- 兩次聚焦修正仍失敗，或一次昂貴嘗試無效：停止擴大，回報證據、未解原因與最小下一步。
- 缺必要證據而無法完成當前驗收：記 `Blocked` 與缺項，不得標 `Complete`。
- **禁止修改任何 `AGENTS.md`。**

### 專案指引

所有適用的 `AGENTS.md` 始終權威，本計劃不取代它。

## 階段路線圖

| 階段 | 可觀察結果 | 依賴 | 階段文件 |
|---|---|---|---|
| 01 | 八個 EXIF 方向的輸出像素與正確結果相同；既有守門全部不變 | 無 | [phase-01](phases/phase-01-exif-orientation.md) |
| 02 | 16-bit 彩色 PNG／TIFF 被明確拒絕並記為該張失敗 | 01 | [phase-02](phases/phase-02-source-bit-depth.md) |
| 03 | README 與實際行為一致，整體驗收與真實批次通過 | 01、02 | [phase-03](phases/phase-03-docs-and-acceptance.md) |

狀態僅由 `build-log.md` 保存。

## 依賴與排序說明

phase-01 與 phase-02 都修改同一個函式 `read_image()` 的守門區段，必須依序進行，不可平行。

排序理由是 phase-01 的順序陷阱：`exif_transpose()` 會使 `n_frames` 失真，因此它必須置於既有兩個檢查之後。先完成並驗證 phase-01，phase-02 再在已確定的守門順序上插入位深檢查，可避免兩個改動互相掩蓋彼此的回歸。

phase-02 的位深檢查必須在任何會觸發解碼／轉換的操作之前執行，否則資訊已經遺失。這與 phase-01 的「之後」要求不衝突：`exif_transpose()` 不改變來源檔的位深事實，位深檢查讀的是容器層級 metadata。兩者的相對順序由 phase-02 依實測決定並記錄。

## 計劃維護與失敗處理

- 開始／恢復先核對 live files、使用者變更與 `build-log.md`，不依賴前次對話。
- 必要檢查失敗或缺證據，不開始依賴階段。先診斷，只修當前原因。
- 新證據推翻後續假設時，先修 `PLANS.md` 與受影響的未開始階段文件，再繼續實作。
- 已完成歷史保留，`build-log.md` 以追加方式更正，不抹除影響後續理解的失敗紀錄。
- 重要發現才建立 `context/phase-NN-context.md`，包含來源、理由與下游影響。
- `GOALS.md` 的穩定目標只依使用者明確新決定更新。

## 整體完成標準

- [ ] 三個階段在 `build-log.md` 均為 `Complete` 且有對應觀察證據。
- [ ] `GOALS.md` 每項成功條件都有觀察依據。
- [ ] 「必須保留的行為與不變式」逐條有證據，特別是多頁 TIFF 與 float 拒絕未因 phase-01 失效。
- [ ] 既有 29 個測試加上本次新增測試全數通過，且既有斷言未被放寬。
- [ ] 一次真實小批次 CLI 驗收通過，原始檔雜湊不變。
- [ ] README 敘述與實際行為逐條對應；剩餘限制（未壓縮 TIFF 上游缺陷、0600 權限、未驗證項）明確記錄。
- [ ] 完成即停止，不展開後續優化。
