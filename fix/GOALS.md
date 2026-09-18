# fix — image_io 讀圖正確性修正 目標

## 目的與背景

V1 交付的 SR 流程（原 `build/` 四階段計劃，已全部 Complete 並於 `af6989e` 移除；歷史可用 `git show af6989e~1:build/build-log.md` 取回）在唯一的讀圖函式 `src/drone_sr/image_io.py` 的 `read_image()` 有兩個已重現的正確性缺陷。兩者都會讓程式正常結束、輸出可正常開啟，但內容與來源圖片的意義不符，且不會被記為失敗。

外部回報者以相同 Pillow 12.3.0 與內容雜湊一致的 `image_io.py` 提出這兩點；本專案已於 2026-09-18 在自己的 `.venv` 內獨立重現，並確認範圍比原回報更廣。詳細觀察見 `PLANS.md` 的「已確認基線」。

1. **EXIF 方向未套用。** `read_image()` 直接 `convert("RGB")`，未依方向標記校正像素；`write_png()` 也不輸出任何方向標記。方向資訊在「套用到像素」與「保留為標記」兩條路上同時消失。
2. **高位深拒絕不完整。** 拒絕機制只看 `image.mode`，而 `image.mode` 是 Pillow 解碼後的記憶體表示，不是來源檔案的編碼。Pillow 會把 16-bit 彩色映射成 `RGB`／`RGBA`，因此通過白名單並被靜默截成 8-bit。README 目前宣稱高位深會明確拒絕，實際行為沒有做到。

這是對已完成 V1 的聚焦修正，不是新功能，也不是重構。

## 期望結果

- 使用者把帶方向標記的照片（README 主打的 `input/DJI_001.JPG` 這類）放進 `input/`，輸出 PNG 的朝向與來源圖片在看圖軟體中的顯示一致。
- 使用者放進 16-bit 彩色圖片時，該張被明確列為失敗並附原因，流程繼續處理下一張；不會得到一張看似成功、實際已合併掉訊號的結果。
- README 對讀寫契約的描述與程式實際行為一致，不多宣稱也不少說明。

## 成功條件

- [ ] 八個 EXIF Orientation 值經 `read_image()` → `write_png()` 後，輸出像素與 `ImageOps.exif_transpose()` 的正確結果逐像素相同（不只尺寸相同）。
- [ ] JPEG 與帶 eXIf chunk 的 PNG 都通過上一條；TIFF 不因本次修正而被旋轉兩次。
- [ ] 真正的 16-bit 彩色來源（PNG colortype 2／4／6，TIFF `BitsPerSample` 任一 > 8）被 `ValueError` 拒絕，CLI 記為該張 Failed 並繼續下一張，退出碼 1。
- [ ] 既有 8-bit 一般圖片的輸出位元組不因本次修正而改變。
- [ ] 「必須保留的行為」全部仍然成立，既有 29 個測試全數通過。
- [ ] README 關於方向與位深的敘述可由本計劃記錄的證據逐條對應。

## 範圍內

- `src/drone_sr/image_io.py` 的 `read_image()`：套用 EXIF 方向、加入來源位深檢查。
- `tests/test_image_io.py`：方向（含鏡像）與真實 16-bit 彩色的測試。
- `README.md`：使方向與位深的敘述與實際行為一致。

## 非目標

- **不新增高位深支援。** 本次是把「拒絕」做完整，不是讓程式處理 16-bit。
- **不保存 EXIF、GPS、ICC 或其他 metadata。** 輸出維持乾淨 PNG；本次只要求在丟掉方向標記之前先把它代表的幾何套用到像素。
- **不修 Pillow 上游的未壓縮 TIFF 缺陷。** 已觀察到：未壓縮 TIFF ＋ Orientation 5–8 ＋ mode `L`／`P`／`RGBA`／`CMYK` 時，Pillow 轉置了像素緩衝區卻未更新 `size`，輸出既非原圖也非正確方向。`exif_transpose()` 對此無效（Pillow 已刪去 tag 274）。本專案實際輸入為 8-bit RGB PNG，碰不到此路徑。記錄於此，不在本次處理。
- **不改輸出檔權限。** 已觀察到輸出 PNG 為 `0600`（`tempfile.NamedTemporaryFile` 的原子寫入副作用），非 `0644`。本次不動，亦不寫入 README。
- 不改 CLI 介面、參數、輸出檔名規則或分塊邏輯。
- 不重構 `image_io.py`、不換框架、不建 benchmark、不處理鄰近問題。
- 不變更環境或依賴：沿用既有 `.venv` ＋ pip ＋ `requirements-wsl.txt`，不引入新套件。

## 必須保留的行為與不變式

以下在 2026-09-18 唯讀查核中確認為目前正確，修正後必須仍然成立：

- 多頁 TIFF 與多影格 PNG 以 `Only single-frame images are supported` 拒絕。**此項與 phase-01 有已知衝突風險，見該階段。**
- float 影像（mode `F`）以 `Unsupported image mode: F` 拒絕。
- 16-bit 灰階（mode `I;16`）維持被拒絕。
- 原始輸入檔位元組不被修改。
- `write_png()` 的原子替換、`clamp`／`round`、non-finite 拒絕、來源 symlink／hardlink 覆寫拒絕。
- CLI 逐張隔離失敗、`Processed`／`Failed` 計數與退出碼規則。
- 既有 29 個測試全數通過，且不得以放寬既有斷言的方式通過。

## 限制

- **限制：** 所有適用的 `AGENTS.md` 保持權威，本計劃不取代它。禁止修改任何 `AGENTS.md`。
  - **依據：** `AGENTS.md`。
  - **影響：** 優先序第 1 條要求「保留已正常運作的行為」，直接約束 phase-01 的修改位置。
- **限制：** 採最小可行修改，不順便重構或處理鄰近問題。
  - **依據：** `AGENTS.md`「工作方式與範圍」。
  - **影響：** 修正集中在 `read_image()` 內，不拆分模組、不改函式簽章。
- **限制：** 不新增正式依賴。
  - **依據：** `AGENTS.md` 要求新增依賴須先提案取得授權。
  - **影響：** 位深偵測只能使用既有 Pillow 與標準庫。
- **限制：** 執行環境為 Linux／WSL Ubuntu 24.04、專案內 `.venv`、Python 3.12.3、Pillow 12.3.0。
  - **依據：** `README.md`「採用的環境與版本」、2026-09-18 實測。
  - **影響：** 位深與方向的行為與 Pillow 版本相關；驗證須在此環境進行。

## 已知未知與使用者決策

- **未解：** 本機 GPU 路徑未能在本次調查環境中驗證（`torch.cuda.is_available()` 回 False，所有量測跑在 CPU）。
  - **重要性：** 本修正只影響讀圖，理論上與裝置無關，但 V1 的驗收慣例是以真實 GPU 執行為主要證據。
  - **解決方式：** phase-03 在可用 GPU 的環境跑一次真實批次；若仍不可用，記為限制而非通過。
- **未解：** 32-bit float **彩色** TIFF（`SampleFormat=3`、3 samples）是否也會漏過 mode 檢查。
  - **重要性：** 影響 README「浮點圖片會明確拒絕」是否完全成立。
  - **解決方式：** phase-02 若能以合法 fixture 建立則一併涵蓋；無法建立則在 `build-log.md` 明確記為未驗證，不宣稱通過。

## 來源輸入

- `AGENTS.md`（專案根目錄）。
- `README.md`：第 64 行的 `input/DJI_001.JPG` 範例、第 66 行的讀寫契約、第 126 行的 29／29。
- `src/drone_sr/image_io.py`、`src/drone_sr/__main__.py`、`tests/test_image_io.py`。
- 2026-09-18 使用者轉述的外部回報，以及同日在專案 `.venv` 內的獨立重現。
- 已完成的 V1 計劃歷史：`git show af6989e~1:build/build-log.md`。
