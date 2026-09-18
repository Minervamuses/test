# Phase 01 — EXIF 方向正確套用

## 目標與來源

`read_image()` 在建立 tensor 之前，把 EXIF Orientation 代表的幾何真正套用到像素上；輸出 PNG 的朝向與來源圖片在看圖軟體中的顯示一致。八個 Orientation 值經完整 `read_image()` → `write_png()` 流程後，像素與 `ImageOps.exif_transpose()` 的正確結果**逐像素相同**。

依據 [GOALS.md](../GOALS.md)、[PLANS.md](../PLANS.md)「已確認基線 — EXIF 方向」。

## 範圍與非目標

**範圍：** `src/drone_sr/image_io.py` 的 `read_image()` 加入 `ImageOps.exif_transpose()`；`tests/test_image_io.py` 加入方向測試。

**非目標：** 不保存或輸出任何 EXIF／方向標記（輸出維持乾淨 PNG）；不處理未壓縮 TIFF 的 Pillow 上游缺陷；不改 `write_png()` 除非測試證明必要；不改函式簽章或 CLI 行為；不重構。

## 依賴與前置未知

- 無前置階段。
- **沒有現成素材。** repo 內 35 張圖片 Orientation 皆為 `None`，唯一的 JPEG EXIF 為空。fixture 必須在測試中自建。
- **未解：** `exif_transpose()` 的正確插入點需由實測確認，不可照抄回報者的「在轉 RGB、建立 tensor 前」字面描述。見下方風險。

## 預期影響元件與授權

`src/drone_sr/image_io.py`（`read_image()` 與其 import）、`tests/test_image_io.py`。

不改 `AGENTS.md`、不加依賴（`ImageOps` 屬既有 Pillow）、不動 `__main__.py`／`inference.py`／`tiling.py`。

## 已知風險：順序陷阱

`ImageOps.exif_transpose()` 回傳 `Image` 而非 `TiffImageFile`，`getattr(img, "n_frames", 1)` 由 2 變成 1。實測：

~~~text
original   : type=TiffImageFile n_frames=2
transposed : type=Image        n_frames=1
~~~

**若置於現行 `n_frames` 檢查之前，多頁 TIFF 拒絕會靜默失效。** `AGENTS.md` 優先序第 1 條要求保留已正常運作的行為，`GOALS.md`「必須保留的行為」亦列此項。

插入點必須在 mode 白名單與 `n_frames` 兩個檢查**之後**。此點由下方 Red 階段的回歸測試強制，不依賴實作者記得。

## 實作與驗證

### Preflight

- 確認 `git status` 乾淨、既有 29 測試通過。
- 重讀 `image_io.py:13-18` 的實際守門順序（不要假設與計劃撰寫時相同）。
- 以一次性腳本在 `$TMPDIR` 重新確認：`exif_transpose()` 對七種接受 mode 皆正常、無 EXIF 時為 no-op、套用後 tag 被清除、不修改來源檔。

### Red

先寫失敗測試，至少涵蓋：

1. **八個 Orientation 的逐像素正確性**（JPEG）。使用非正方形、非對稱且四角可辨識的 fixture，例如 40×20 加四個不同顏色的角標。斷言 `read_image()` 的結果與 `ImageOps.exif_transpose(Image.open(src))` 逐像素相同。**必須斷言像素，不能只斷言尺寸** —— Orientation 2、3、4 尺寸正確而像素錯誤，只比尺寸會讓它們靜默通過。
2. **多頁 TIFF 拒絕的回歸測試**。這是順序陷阱的守門測試，必須存在且必須在本階段一併加入，即使它目前已經通過。
3. **來源檔不被修改**：比對前後 SHA-256。

JPEG 有失真壓縮，逐像素比對的兩邊都應經過同一次 JPEG 編解碼（即兩邊都從同一個已存檔的 JPEG 讀取），避免把壓縮誤差當成方向錯誤。若仍有邊界誤差，改用純色區塊 fixture 而不是放寬斷言。

### Green

在 `read_image()` 內、兩個既有檢查之後，於 `convert("RGB")` 之前套用 `ImageOps.exif_transpose()`。採最小改動，不重排既有邏輯。

### Refactor

僅在行為為綠之後、且限於本階段範圍。重構後重跑 focused 檢查。

### 驗證

- **Focused：**
  ~~~bash
  .venv/bin/python -m unittest discover -s tests -p 'test_image_io.py' -v
  ~~~
- **較廣：**
  ~~~bash
  .venv/bin/python -m unittest discover -s tests
  ~~~
  既有 29 測試必須全過，且不得以放寬既有斷言的方式通過。
- **PNG eXIf 交叉檢查：** 以帶 eXIf chunk 的 PNG 確認同樣修正生效。
- **TIFF 未被旋轉兩次：** 以帶 Orientation 的 TIFF 確認輸出與修正前一致（Pillow 已自行處理，本修正對它應為 no-op）。
- **失敗行為：** 任一必要檢查失敗時，phase-02 不得開始。先診斷當前原因，不擴大重構。

## 可靠性、安全與復原

- 安全與隱私：無。本階段不新增輸出的 metadata，方向資訊僅用於像素幾何。
- 相容性：對無 EXIF 的一般圖片必須是完全 no-op —— 既有 8-bit PNG 的輸出位元組不得改變。此點需有明確證據。
- 資料完整性：來源檔唯讀，前後雜湊必須相同。
- 復原：改動限於單一函式，`git` 可回復；無資料遷移。

## 驗收條件

- [ ] 八個 Orientation 值（JPEG）的輸出與正確結果逐像素相同。
- [ ] 帶 eXIf chunk 的 PNG 同樣正確。
- [ ] 帶 Orientation 的 TIFF 未被旋轉兩次。
- [ ] 多頁 TIFF 仍以 `Only single-frame images are supported` 被拒絕，且有測試守住。
- [ ] float（mode `F`）與 16-bit 灰階（`I;16`）仍被拒絕。
- [ ] 無 EXIF 的既有 8-bit 圖片輸出位元組不變。
- [ ] 來源檔案雜湊不變。
- [ ] 既有 29 測試全過，既有斷言未被放寬。

## 證據、失敗與交接

在 `../build-log.md` 記錄：實際插入點（檔案與行）、八個方向的比對方式（逐像素）與結果、多頁 TIFF 回歸結果、既有測試數量與通過狀況、來源雜湊比對。

只有在發現與 `PLANS.md`「已確認基線」不符的行為時才建立 `../context/phase-01-exif-orientation-context.md`，記錄來源、理由與下游影響。

無法完成逐像素驗證時記 `Blocked` 與缺項，不得改以尺寸比對宣稱通過。完成後依 `PLANS.md` 自主模式進入 phase-02。
