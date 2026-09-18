# fix — Build Log

本檔是階段狀態與觀察證據的唯一來源；計劃描述預期工作，本檔只記實際實作與驗證。

## 階段摘要

| 階段 | 狀態 | 開始 | 完成 | 證據 | 阻礙 |
|---|---|---|---|---|---|
| 01 — EXIF 方向正確套用 | Complete | 2026-09-18 11:52 CST | 2026-09-18 12:06 CST | 本檔活動紀錄；commits `01b982b`、`534e6eb` | 無 |
| 02 — 來源位深明確拒絕 | Complete | 2026-09-18 12:10 CST | 2026-09-18 12:24 CST | 本檔活動紀錄；commits `ea59e25`、`982cc91` | 無 |
| 03 — 文件對齊與整體驗收 | Complete | 2026-09-18 12:28 CST | 2026-09-18 12:44 CST | 本檔活動紀錄；commit `f4e97e7` | 無 |

只使用 `Not started`、`In progress`、`Blocked`、`Complete`。`Complete` 必須有全部必要 acceptance 與檢查的觀察證據。

## 證據規則

- 記實際命令、工作目錄、環境、簡短結果，以及 pass／fail／skipped／unavailable。
- 方向驗證須記錄比對方式是逐像素或僅尺寸；只比尺寸不足以支持 acceptance。
- 位深驗證須記錄 fixture 的來源編碼如何被獨立確認（PNG IHDR 位元組、TIFF `BitsPerSample`），不能只說「建立了一張 16-bit 圖」。
- 真實批次驗證記輸入／輸出路徑與尺寸、device、原始檔雜湊前後比對、`Processed`／`Failed` 與退出碼。
- 未執行、缺材料、環境不可用（例如無 GPU）與實際通過分開記錄。
- 重大失敗與更正採追加，不抹除影響後續理解的歷史。
- 不貼完整 console、完整 diff 或敏感資料；大量輸出以路徑連結。

## 活動紀錄

本計劃於 2026-09-18 撰寫；實作於 2026-09-18 11:52 CST 啟動。

計劃撰寫期間的唯讀重現觀察記於 `PLANS.md` 的「已確認基線」，那是調查證據，**不是**本計劃的實作證據；實作啟動後仍須在本檔重新記錄實際執行結果。

後續每筆包含時間與時區、階段、狀態變更、授權依據、實際變更、命令與結果、證據位置、限制或阻礙，以及下一個符合依賴條件的動作。

<!-- 追加格式：

### <時間與時區> — Phase <NN>：<事件>

- **狀態：** <舊> → <新>
- **授權依據：** 連結到該階段文件
- **實際變更：** 簡潔描述
- **驗證：** 實際命令與結果
- **審查：** 適用時的 findings 或 sign-off
- **限制：** 未測或已接受的限制
- **阻礙：** 目前阻礙或「無」
- **下一步：** 依 PLANS.md 的下一個符合依賴條件的動作
- **證據位置：** context、review、log、產物或 commit
-->

### 2026-09-18 11:52 CST — Phase 01：啟動與唯讀 preflight

- **狀態：** Not started → In progress
- **授權依據：** [phase-01](phases/phase-01-exif-orientation.md)，使用者於本次對話啟動實作並授權階段範圍內的程式、測試與文件修改。
- **環境：** `/home/minervamuses/drone-image-analysis`，WSL2 Ubuntu、專案 `.venv`、Python 3.12.3、Pillow 12.3.0、torch 2.11.0+cu128，`torch.cuda.is_available()` = **False**（本階段不需 GPU）。
- **實際變更：** 尚未修改 application 程式。先將既有未追蹤的 `fix/` 計劃 bundle 提交為 `5c4406a`，使 build-log 自此可追蹤。
- **驗證（preflight，全部唯讀，臨時檔在 `$TMPDIR`）：**
  - `.venv/bin/python -m unittest discover -s tests` → `Ran 29 tests ... OK`（2.7 s）。基線 29 測試通過。
  - 重讀 `src/drone_sr/image_io.py:12-18`：守門順序與計劃撰寫時相同 —— mode 白名單（`:14`）→ `n_frames`（`:16`）→ `convert("RGB")` 與 tensor（`:18`）。
  - `exif_transpose()` 對七種接受 mode（`1`/`L`/`LA`/`P`/`RGB`/`RGBA`/`CMYK`）皆成功並回傳新物件；無 EXIF 時像素位元組不變（安全 no-op）。
  - 八個 Orientation 的 JPEG 實測：1 尺寸不變；2–4 尺寸 40×20 不變；5–8 由 40×20 轉為 20×40。套用後 tag 274 被刪除（Orientation 1 保留值 1，無作用），連呼叫兩次結果相同（不重複旋轉），來源檔 SHA-256 前後相同。
  - **順序陷阱重新確認（非照抄）：** 多頁 TIFF `original: TiffImageFile n_frames=2` → `transposed: Image n_frames=1`。置於 `n_frames` 檢查之前會使多頁拒絕靜默失效。
  - 回傳物件在 `with Image.open(...)` 結束後仍可使用（`size=(20, 40)` 可取像素）。
- **與 PLANS.md「已確認基線」的差異（更正，追加不抹除）：** 基線稱「Pillow 已刪去 tag 274」，實際機制更精確：`TiffImagePlugin.load_end()`（`.venv/.../PIL/TiffImagePlugin.py:1328-1330`）先呼叫 `ImageOps.exif_transpose(self, in_place=True)` 再 `del self.tag_v2[274]`，而 tag 只在 **load 之後**消失；lazy open 當下 `getexif().get(274)` 仍讀得到 6。由於 `ImageOps.exif_transpose()` 自身第一行就呼叫 `image.load()`，TIFF 仍不會被旋轉兩次 —— 結論不變，機制記錄於此。
- **對 phase-02 的下游影響：** `exif_transpose()` 會觸發 `load()`（PNG 的 `im.png` 於 load 後變 `None`），因此 phase-02 的來源位深檢查必須排在 `exif_transpose()` **之前**，與 PLANS.md「位深檢查須在任何觸發解碼／轉換的操作之前」一致。
- **pre-fix 基線產物：** 以修正前程式將 repo 內 34 張真實圖片逐一 `read_image()` → `write_png()`，記錄輸出 SHA-256 於 `$TMPDIR/roundtrip-before.txt`（34 行，全部成功，來源雜湊皆未變）。修正後將以相同腳本比對，作為「既有 8-bit 圖片輸出位元組不變」的證據。
- **限制：** 本環境無 GPU；本階段不涉及推論，不受影響。repo 內無任何帶 Orientation 的素材（34 張全為 8-bit RGB PNG ＋ 1 張 EXIF 為空的 JPEG），fixture 必須自建。
- **阻礙：** 無。
- **下一步：** phase-01 Red —— 先寫失敗測試（八方向逐像素、PNG eXIf、多頁 TIFF 回歸、來源雜湊）。
- **證據位置：** 本檔；commit `5c4406a`。

### 2026-09-18 12:06 CST — Phase 01：Red／Green 完成並驗收

- **狀態：** In progress → Complete
- **授權依據：** [phase-01](phases/phase-01-exif-orientation.md)。
- **實際變更：**
  - `src/drone_sr/image_io.py`：`import ImageOps`；**插入點為 `image_io.py:20`**，位於 mode 白名單（`:14`）與 `n_frames`（`:16-17`）兩個既有檢查**之後**、`convert("RGB")`（`:21`）之前。函式簽章、`write_png()`、CLI 皆未改。commit `534e6eb`。
  - `tests/test_image_io.py`：新增 3 個測試（8 方向逐像素、TIFF 未被旋轉兩次、多影格拒絕回歸）與 fixture helper `_oriented_source()`。commit `01b982b`。既有測試一字未改，`git diff` 中唯一被刪除的行是 `from PIL import Image`（改為 `from PIL import Image, ImageOps`），**沒有放寬任何既有斷言**。
- **驗證（工作目錄 `/home/minervamuses/drone-image-analysis`，`.venv`）：**
  - **Red（修正前）：** `.venv/bin/python -m unittest discover -s tests -p 'test_image_io.py'` → `FAILED (failures=14)`：JPEG 與 PNG 的 Orientation 2–8 各 7 個 subtest。**Orientation 3 的失敗發生在 `tests/test_image_io.py:90` 的 `tobytes()` 比對而非尺寸比對**，證明逐像素斷言確實抓到「尺寸正確、像素錯誤」這一類。Orientation 1、TIFF、多影格三項於修正前即通過（守門用）。
  - **Green（修正後）：** focused `... -p 'test_image_io.py'` → `Ran 10 tests ... OK`；較廣 `.venv/bin/python -m unittest discover -s tests` → **`Ran 32 tests ... OK`**（既有 29 ＋ 新增 3）。
  - **比對方式為逐像素：** 測試比對 `write_png()` 實際輸出 PNG 的 `Image.tobytes()` 與 `ImageOps.exif_transpose(Image.open(src)).convert("RGB").tobytes()`，並另行斷言 `size`。JPEG 兩側讀自同一個已存檔 JPEG，壓縮誤差相同，因此為精確相等而非近似。fixture 為 40×20、四角各一色，且對 Orientation≠1 斷言 `expected != stored`，確保 fixture 真的會因方向而不同。
  - **PNG eXIf：** fixture 以 `save(..., exif=...)` 寫出，位元組層級 chunk 掃描確認為 `IHDR`／`eXIf`／`IDAT`／`IEND`，重開 `getexif()[274]` 讀回；8 個方向與 JPEG 同樣通過。
  - **TIFF 未被旋轉兩次：** `test_oriented_tiff_is_not_transposed_twice` 以 Orientation 6 的 RGB TIFF 斷言輸出等於 Pillow 自行套用後的結果，且尺寸為 `(20, 40)`（套用一次，非零次或兩次）→ pass。
  - **順序陷阱的負向控制（實際執行，非推論）：** 暫時把 `exif_transpose()` 移到 `n_frames` 檢查之前並改判 `oriented`，focused 測試 → `FAILED (failures=2)`：`pages.tif` 與 `animated.png` 兩個 subtest 失敗。隨即 `git checkout -- src/drone_sr/image_io.py` 還原，重跑 `Ran 32 tests ... OK`，`git status` 對 `src`／`tests` 乾淨。**回歸測試確實守得住這個陷阱。**
  - **既有 8-bit 輸出位元組不變：** 以同一腳本（`$TMPDIR/roundtrip.py`）對 repo 內 34 張真實圖片跑 `read_image()` → `write_png()`，修正前後輸出 SHA-256 **34/34 完全相同**（`diff` 無差異），來源檔雜湊 34/34 未變。
  - **其他不變式（修正後實測，`$TMPDIR/invariants01.py`）：** mode `F` → `Unsupported image mode: F`；`I;16` → `Unsupported image mode: I;16`；多頁 TIFF 與多影格 PNG → `Only single-frame images are supported`；七種接受 mode 仍正常讀入為 `(1, 3, 2, 4)`。
- **驗收條件對照：** 八方向逐像素 ✅／PNG eXIf ✅／TIFF 未旋轉兩次 ✅／多頁 TIFF 仍拒絕且有測試守住 ✅／`F` 與 `I;16` 仍拒絕 ✅／8-bit 輸出位元組不變 ✅／來源雜湊不變 ✅／既有 29 測試全過且未放寬 ✅。
- **審查：** 未另建 `code_review/`；本階段改動為 2 行程式加 1 個 import，證據已逐條記錄。
- **限制：** 未涵蓋未壓縮 TIFF ＋ Orientation 5–8 ＋ mode `L`／`P`／`RGBA`／`CMYK` 的 Pillow 上游缺陷（`GOALS.md` 非目標，本專案輸入碰不到）。輸出仍不含任何方向標記（非目標，設計如此）。本階段不需 GPU，未執行推論。
- **阻礙：** 無。
- **下一步：** phase-02（依賴 01，現已 Complete）。位深檢查須排在 `exif_transpose()` 之前，理由見 11:52 CST 該筆紀錄。
- **證據位置：** 本檔；commits `01b982b`（Red）、`534e6eb`（Green）；`$TMPDIR/roundtrip-{before,after}.txt`（session 暫存，非專案檔）。

### 2026-09-18 12:24 CST — Phase 02：來源位深檢查完成並驗收

- **狀態：** Not started → In progress → Complete（前置 phase-01 為 Complete）
- **授權依據：** [phase-02](phases/phase-02-source-bit-depth.md)。
- **實際變更：**
  - `src/drone_sr/image_io.py`：新增模組層級 helper `_source_bits_per_sample()`（`image_io.py:12-22`），並在 `read_image()` 內 `image_io.py:31-33` 加入檢查。commit `982cc91`。
  - `tests/test_image_io.py`：擴充既有 `test_high_bit_depth_is_rejected_explicitly`（**保留原本的 `I;16` 灰階斷言一字未改**，在其後追加彩色案例），新增 `test_low_bit_depth_sources_stay_accepted`，以及 fixture helper `_write_png()`／`_write_tiff()`。commit `ea59e25`。
- **所採偵測方式與理由：** 依 PLANS.md 建議採**容器層級**，不用 Pillow 內部屬性。TIFF 讀 `image.tag_v2.get(258)`（`BitsPerSample`，open 當下即可得）取最大值；PNG 直接讀檔案前 26 bytes，取 IHDR 第 24 個位元組（PNG 規格固定位置），並以 `header[12:16] == b"IHDR"` 防護。其餘容器（JPEG 等）回傳 8，不額外檢查。查核 `.venv/.../PIL/PngImagePlugin.py:69-91` 的 `_MODES` 表確認 Pillow **沒有**公開的 PNG 位深屬性，且該表就是破口來源：`(16,2)→RGB`、`(16,4)→RGBA`、`(16,6)→RGBA` 全部落入既有白名單，只有 `(16,0)→I;16` 會被擋。
- **插入順序與理由（實測決定）：** 置於 mode 白名單與 `n_frames` **之後**、`exif_transpose()` **之前**。
  - 在 mode 檢查之後：維持既有錯誤訊息優先序，16-bit 灰階仍回報 `Unsupported image mode: I;16`，既有測試斷言因此無須放寬。
  - 在 `exif_transpose()` 之前：後者第一行呼叫 `image.load()`，解碼後位深事實已遺失。
  - **前置性為實測，不是推論：** 以 `unittest.mock.patch` 把 `Image.Image.load` 換成拋 `AssertionError` 後，四個 16-bit 來源仍全部回報 `ValueError: Unsupported source bit depth: 16 bits per sample`，沒有任何一個走到 `load()`。
- **fixture 來源編碼的獨立確認（非假設）：** Pillow 無法存出 16-bit 彩色 PNG 或 TIFF，因此以 `struct`＋`zlib` 手寫 PNG chunk、手寫單 strip little-endian TIFF IFD（僅測試 fixture，非正式依賴）。測試中回頭解析 PNG 檔案的 `raw[24]`／`raw[25]` 斷言為 `(16, colortype)`，TIFF 則以 `Image.open(...).tag_v2.get(258) == (16, 16, 16)` 斷言。
- **接受／拒絕對照表（修正後實測，`$TMPDIR/probe02.py`；16-bit 來源通道值為 256／257／511）：**

  | 容器 × 編碼 | Pillow mode | 修正前 | 修正後 |
  |---|---|---|---|
  | PNG bitdepth=16 colortype=2 | `RGB` | 靜默接受，截成 `[1,1,1]` | `ValueError: Unsupported source bit depth: 16 bits per sample` |
  | PNG bitdepth=16 colortype=4 | `RGBA` | 靜默接受，截成 `[1,1,1]` | 同上（拒絕） |
  | PNG bitdepth=16 colortype=6 | `RGBA` | 靜默接受，截成 `[1,1,1]` | 同上（拒絕） |
  | PNG bitdepth=16 colortype=0 | `I;16` | `Unsupported image mode: I;16` | 不變（仍由 mode 檢查擋下） |
  | TIFF `BitsPerSample=(16,16,16)` | `RGB` | 靜默接受，截成 `[1,1,1]` | `ValueError: Unsupported source bit depth: 16 bits per sample` |
  | PNG bitdepth=1／2／4 colortype=0 | `1`／`L`／`L` | 接受 | **仍接受**（未誤擋） |
  | PNG colortype=3（調色盤） | `P` | 接受，`[255,0,0]` | **仍接受且無損** |
  | PNG bitdepth=8 colortype=2 | `RGB` | 接受，`[10,20,30]` | **仍接受且無損** |
  | TIFF `BitsPerSample=(8,8,8)` | `RGB` | 接受，`[10,20,30]` | **仍接受且無損** |

- **未解問題結案 —— 32-bit float 彩色 TIFF：** 本階段成功手寫合法 fixture（`BitsPerSample=(32,32,32)`、`SampleFormat=(3,3,3)`、3 samples）。實測 **Pillow 在 `Image.open()` 階段就無法辨識**：`UnidentifiedImageError: cannot identify image file`（`OSError` 子類）。因此它根本到不了 mode 檢查，也到不了新的位深檢查，但**確實不會被靜默接受**；CLI 既有 `except Exception` 會記為該張 Failed。GOALS.md 的此項未解問題至此結案：**浮點彩色 TIFF 不會被靜默處理，但拒絕來自 Pillow 無法解析，訊息不是本專案的 `Unsupported image mode`**。phase-03 的 README 敘述必須反映這個差別，不得籠統宣稱「浮點一律以 `Unsupported image mode` 拒絕」。
- **驗證：**
  - **Red（修正前）：** `.venv/bin/python -m unittest discover -s tests -p 'test_image_io.py'` → `FAILED (failures=4)`（PNG colortype 2／4／6 與 16-bit RGB TIFF，皆為 `ValueError not raised`）。`test_low_bit_depth_sources_stay_accepted` 於修正前即通過，作為誤擋守門。
  - **Green：** focused → `Ran 11 tests ... OK`；較廣 `.venv/bin/python -m unittest discover -s tests` → **`Ran 33 tests ... OK`**（既有 29 ＋ phase-01 新增 3 ＋ phase-02 新增 1）。
  - **既有 8-bit 真實圖片未回歸：** 34 張 repo 圖片 `read_image()` → `write_png()` 的輸出 SHA-256 與 **phase-01 之前**的基線 34/34 完全相同。
  - **CLI 端到端（真實模型，`models/model.pth` → `realesr-general-x4v3.pth` Compact）：**
    ~~~text
    .venv/bin/python -m drone_sr --input $TMPDIR/cli02/input --output $TMPDIR/cli02/output
    Device: cpu / Model: loaded / Images: 3
    [1/3] a_good.png
    [2/3] b_high.png — Failed: Unsupported source bit depth: 16 bits per sample
    [3/3] c_oriented.jpg
    Processed: 2 / Failed: 1 / 退出碼 1（約 3.1 s）
    ~~~
    輸入為真實 32×24 8-bit 裁切（取自 `input/whaledrone_seek10s_x1536_y768_512.png`）、手寫 16-bit RGB PNG、Orientation 6 的 32×16 JPEG。輸出僅 `a_good.png`（128×96）與 `c_oriented.png`（**64×128**，即先校正為 16×32 再 ×4；未修正前會是 128×64），16-bit 那張**沒有產生任何輸出檔**。三個來源檔 `sha256sum -c` 全部 `OK`。
- **驗收條件對照：** 16-bit PNG ct2／4／6 拒絕 ✅／16-bit RGB TIFF 拒絕 ✅／fixture 位深獨立確認 ✅／1／2／4／8-bit 與調色盤仍接受且無損 ✅／16-bit 灰階、float、多頁 TIFF 既有拒絕仍有效 ✅（float 彩色 TIFF 之機制差異見上）／phase-01 方向未回歸 ✅（33 測試全過＋CLI 64×128）／CLI 端到端 ✅／既有測試未放寬 ✅。
- **限制：** 位深檢查只涵蓋 PNG 與 TIFF 兩種容器；JPEG 以基線 8-bit 處理，未驗證 12-bit JPEG（Pillow 預設不支援，且不在本次範圍）。CLI 驗收在 **CPU** 執行（本機 `torch.cuda.is_available()` 為 False），GPU 路徑未於本階段驗證。
- **阻礙：** 無。
- **下一步：** phase-03（依賴 01、02，均已 Complete）：README 對齊、整體驗收、真實批次。
- **證據位置：** 本檔；commits `ea59e25`（Red）、`982cc91`（Green）；`$TMPDIR/probe02.py`、`$TMPDIR/predecode.py`、`$TMPDIR/cli02/`（session 暫存，非專案檔）。

### 2026-09-18 12:44 CST — Phase 03：文件對齊與整體驗收

- **狀態：** Not started → In progress → Complete（前置 01、02 均為 Complete）
- **授權依據：** [phase-03](phases/phase-03-docs-and-acceptance.md)。
- **實際變更（僅 `README.md`，未改程式、測試或依賴）：** commit `f4e97e7`。
  1. **第 66 行讀寫契約句**：原句「多頁 TIFF、高位深與浮點圖片會明確拒絕；普通圖片轉成 RGB，不保存 alpha、GIS 或其他 metadata。」改為說明高位深**依容器編碼判定**（PNG IHDR 位深、TIFF `BitsPerSample`）而非只看解碼後 mode，並補上「讀入時先依 EXIF Orientation 把方向校正到像素上，輸出 PNG 不保留方向標記」。理由：原句的 metadata 承諾是**輸出端**的，被讀成涵蓋輸入端幾何；「高位深」在 phase-02 之前只對灰階成立。
  2. **新增 `### 讀圖正確性修正（2026-09-18）`**（置於 V1 最終驗收段落之後、指令區塊之前）：兩個缺陷的修正內容、33／33 無 skipped、34 張既有圖片輸出位元組不變、真實批次結果，以及**已知限制清單**（CPU-only、僅 PNG／TIFF 容器、浮點的兩條拒絕路徑、未壓縮 TIFF 上游缺陷、輸出 `0600`）。
  - **第 64 行 `input/DJI_001.JPG` 範例：** 檢視後敘述本身只談輸出檔名對應，修正後成立，未改動；方向行為由新增句涵蓋。
  - **README 新寫入的每句都對應本檔既有證據**，其中兩項在本階段另行實測後才寫入：輸出 PNG 權限確為 `0600`；輸出 chunk 僅 `IHDR`／`IDAT`／`IEND`，`getexif()` 為空、`orientation=None`（即確實不保留方向標記）。
- **驗證：**
  - **完整 suite：** `.venv/bin/python -m unittest discover -s tests -v` → **`Ran 33 tests ... OK`**，`grep -ci skipped` = **0**（無 skipped）。收尾再跑一次 `discover -s tests` 同為 33 通過。
  - **真實小批次 CLI（本計劃的驗收批次）：** 以 `input/whaledrone_seek10s_x1536_y768_512.png` 的真實 64×48 海面裁切為唯一素材，於 `$TMPDIR/cli03/input` 產生三個輸入 —— `a_good.jpg`（無 EXIF）、`b_high.png`（同一真實像素 ×257 寫成真正 16-bit RGB PNG，IHDR bitdepth=16 colortype=2）、`c_oriented.jpg`（像素先 ROTATE_90 存檔並標記 Orientation 6，因此正確顯示方向等於原裁切）。未修改 `input/`、`output/`、`test-data/` 任何既有檔案。
    ~~~text
    .venv/bin/python -m drone_sr --input $TMPDIR/cli03/input --output $TMPDIR/cli03/output
    Device: cpu / Model: loaded / Images: 3
    [1/3] a_good.jpg
    [2/3] b_high.png — Failed: Unsupported source bit depth: 16 bits per sample
    [3/3] c_oriented.jpg
    Processed: 2 / Failed: 1 / 退出碼 1（約 3.2 s，含啟動與模型載入）
    ~~~
    - **方向正確性（非循環證明）：** `c_oriented.png` 輸出為 **256×192**，與未旋轉參考 `a_good.png` **同向同尺寸**；未修正時其輸出會是 192×256。兩者平均差 **0.60／255**、最大差 27／255、34.3% 像素完全相同 —— 差異來自旋轉後重新 JPEG 編碼與模型非旋轉等變，與 PLANS.md 基線量到的 0.76／255 同量級。若方向未被套用，兩者連尺寸都不會一致。
    - 16-bit 那張**沒有產生任何輸出檔**（輸出目錄只有 `a_good.png`、`c_oriented.png`）。
    - 三張來源 `sha256sum -c` 全部 `OK`。
  - **device：** `cpu`。本輪 `torch.cuda.is_available()` 為 False。
- **GOALS.md 未解問題結案狀況：**
  - float 彩色 TIFF：phase-02 已結案（Pillow 無法識別，記為 Failed；訊息非本程式發出），已寫入 README 限制。
  - **GPU：** 本輪環境無可用 CUDA，真實批次以 CPU 執行。依 phase-03 規定**記為限制而非通過**，README 亦明確標示「未在 GPU 上重跑」。
- **限制：** 除上述 CPU-only 外，未壓縮 TIFF 上游缺陷、`0600` 權限、12-bit JPEG 皆未處理／未驗證，已逐項寫入 README。另觀察到 README 結尾仍連結已於 `af6989e` 移除的 `build/build-log.md` 與 `build/GOALS.md`；屬本階段非目標（不重寫其他章節），未更動，回報使用者。
- **阻礙：** 無。
- **下一步：** 三階段皆 Complete，依 PLANS.md「完成即停止」，不展開後續優化。
- **證據位置：** 本檔；commit `f4e97e7`；`$TMPDIR/cli03/`（session 暫存，非專案檔）。

### 2026-09-18 12:44 CST — 整體完成標準逐條核對

對照 [PLANS.md](PLANS.md)「整體完成標準」：

- **三個階段均為 Complete 且有觀察證據** —— 是。01（`01b982b`、`534e6eb`）、02（`ea59e25`、`982cc91`）、03（`f4e97e7`）。
- **GOALS.md 每項成功條件都有觀察依據** —— 是：
  1. 八個 Orientation 逐像素相同 → `test_exif_orientation_is_applied_to_pixels`，比對 `write_png()` 實際輸出的 `tobytes()`。
  2. JPEG 與 eXIf PNG 皆通過、TIFF 未旋轉兩次 → 同上測試的兩種格式 subTest ＋ `test_oriented_tiff_is_not_transposed_twice`。
  3. 真正 16-bit 彩色被拒、CLI 記 Failed、退出碼 1 → `test_high_bit_depth_is_rejected_explicitly` ＋ cli02／cli03 兩次真實 CLI。
  4. 既有 8-bit 輸出位元組不變 → 34／34 SHA-256 與修正前相同。
  5. 必須保留的行為全部成立、既有 29 測試通過 → 33／33 通過（既有 29 未改動、未放寬）；不變式另以 `$TMPDIR/invariants01.py` 實測。
  6. README 敘述可逐條對應證據 → 見本階段紀錄。
- **不變式逐條有證據，特別是多頁 TIFF 與 float 拒絕未因 phase-01 失效** —— 是：測試守門 ＋ 負向控制（把 `exif_transpose()` 移到前面會使 2 個 subtest 失敗）＋ 修正後實測。
- **既有 29 測試加新增測試全數通過，既有斷言未被放寬** —— 是，33／33、無 skipped；`git diff` 中測試檔唯一刪除行為 import 行。
- **一次真實小批次 CLI 驗收通過，原始檔雜湊不變** —— 是（cli03，`Processed: 2`／`Failed: 1`／退出碼 1，三張來源雜湊 `OK`）。
- **README 敘述與實際行為逐條對應；剩餘限制明確記錄** —— 是。
- **完成即停止** —— 是，不展開後續優化。

**未通過或未驗證（不得視為通過）：** 本輪全部檢查在 **CPU** 執行，無 GPU 觀察證據；12-bit JPEG、未壓縮 TIFF 上游缺陷路徑未驗證；輸出 `0600` 權限維持原狀。
