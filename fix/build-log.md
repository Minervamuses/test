# fix — Build Log

本檔是階段狀態與觀察證據的唯一來源；計劃描述預期工作，本檔只記實際實作與驗證。

## 階段摘要

| 階段 | 狀態 | 開始 | 完成 | 證據 | 阻礙 |
|---|---|---|---|---|---|
| 01 — EXIF 方向正確套用 | Complete | 2026-09-18 11:52 CST | 2026-09-18 12:06 CST | 本檔活動紀錄；commits `01b982b`、`534e6eb` | 無 |
| 02 — 來源位深明確拒絕 | Not started | — | — | — | 無 |
| 03 — 文件對齊與整體驗收 | Not started | — | — | — | 無 |

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
