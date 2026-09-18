# Phase 02 — 來源位深明確拒絕

## 目標與來源

`read_image()` 在資訊被轉換丟失之前檢查**來源檔案的原始位深**，超過每通道 8-bit 就以 `ValueError` 拒絕。CLI 將該張記為 Failed 並附原因、繼續下一張、退出碼 1。README 宣稱的「高位深會明確拒絕」自此對彩色來源也成立。

依據 [GOALS.md](../GOALS.md)、[PLANS.md](../PLANS.md)「已確認基線 — 來源位深」。

## 範圍與非目標

**範圍：** `src/drone_sr/image_io.py` 的 `read_image()` 加入來源位深檢查；`tests/test_image_io.py` 加入真正高位深 fixture 的測試。

**非目標：** **不新增高位深支援**，不做 16→8 的縮放轉換，不改既有 mode 白名單的語義，不改 `__main__.py` 的錯誤處理（既有路徑已足夠），不處理 `.avif` 等不在接受副檔名內的容器。

## 依賴與前置未知

- phase-01 必須 `Complete`：兩者修改同一守門區段，依序進行以免互相掩蓋回歸。
- **沒有現成素材。** repo 內所有圖片皆為 8-bit。fixture 必須自建，且**必須是真正的高位深檔案**。
- **未解：** 32-bit float **彩色** TIFF（`SampleFormat=3`、3 samples）是否也漏過 mode 檢查。計劃撰寫期間無法建立合法 fixture。若本階段能建立則一併涵蓋；不能建立就在 `build-log.md` 記為未驗證，不宣稱「浮點全部拒絕」。

## 預期影響元件與授權

`src/drone_sr/image_io.py`（`read_image()`）、`tests/test_image_io.py`。

不加依賴：偵測只使用既有 Pillow 與標準庫。不改 `AGENTS.md`。

## 偵測方式

位深事實必須在任何觸發解碼或轉換的操作之前讀取。計劃撰寫期間已確認可行的來源：

| 容器 | 來源 | 實測 |
|---|---|---|
| TIFF | `im.tag_v2.get(258)`（`BitsPerSample`） | 16-bit 灰階 `(16,)`；16-bit RGB `(16, 16, 16)`；8-bit RGB `(8, 8, 8)` |
| PNG | 檔案 IHDR 第 24 個位元組（規格固定位置） | 16-bit `16`；8-bit `8` |

**交叉核對（非主要依據）：** `im.tile[0].args` 在 16-bit RGB PNG 為 `'RGB;16B'`、8-bit 為 `'RGB'`。`im.tile` 與 `im.png` 屬內部介面，且 `im.png` 在 `load()` 後變為 `None`。建議以容器層級檢查為主；若實作者選擇改用 rawmode 判斷，須在 `build-log.md` 說明理由並記錄其在兩種容器、各 colortype 下的實測結果。

JPEG 基線為 8-bit，不需額外檢查；其他副檔名不在接受範圍內。

## 實作與驗證

### Preflight

- 確認 phase-01 為 `Complete`，`git status` 乾淨，測試全過。
- 重讀 `read_image()` 目前的實際守門順序（phase-01 已改動過）。
- 確認位深檢查與 `exif_transpose()` 的相對順序：位深讀的是容器 metadata，不受方向修正影響，但實際順序須實測後記錄。

### Red

先寫失敗測試，涵蓋：

1. **16-bit RGB PNG**（IHDR `bitdepth=16 colortype=2`）→ 期望 `ValueError`。
2. **16-bit RGBA PNG**（`colortype=6`）與 **16-bit 灰階+alpha PNG**（`colortype=4`）→ 期望 `ValueError`。這兩者目前也被映射成 `RGBA` 而漏過。
3. **16-bit RGB TIFF**（`BitsPerSample=(16,16,16)`）→ 期望 `ValueError`。
4. **回歸：8-bit 各 colortype 仍正常接受且無損。** 包含 1-bit／2-bit／4-bit PNG 與調色盤 PNG —— 低位深是合法輸入，不得被新檢查誤擋。
5. **回歸：既有拒絕仍有效。** 16-bit 灰階（`I;16`）、float（`F`）、多頁 TIFF。

**fixture 必須是真正的高位深檔案，且其編碼要在測試中獨立確認**（回頭解析 PNG IHDR 位元組或讀 TIFF `BitsPerSample`），不能只呼叫 `Image.new(...).save(...)` 就假設得到想要的位深。既有 `test_high_bit_depth_is_rejected_explicitly` 正是因為這個假設而只覆蓋到灰階。

注意 `Image.fromarray` 無法建立 16-bit RGB／RGBA（實測 `Cannot handle this data type`）。PNG 可用 `struct` 加 `zlib` 手寫 chunk；TIFF 可手寫 IFD。這些屬測試 fixture，不是正式依賴。

### Green

在 `read_image()` 內、任何解碼或轉換之前加入位深檢查，超過 8 即 `raise ValueError`，訊息要能讓使用者看出是哪一張、為什麼被拒。

### Refactor

既有 `test_high_bit_depth_is_rejected_explicitly` 的名稱與內容不符（fixture 為灰階）。在本階段將其改名或擴充為涵蓋彩色的版本，**但不得刪除既有的灰階斷言** —— 那是仍需保留的行為。

### 驗證

- **Focused：**
  ~~~bash
  .venv/bin/python -m unittest discover -s tests -p 'test_image_io.py' -v
  ~~~
- **較廣：**
  ~~~bash
  .venv/bin/python -m unittest discover -s tests
  ~~~
- **CLI 端到端：** 在暫存資料夾放一張 16-bit RGB PNG 與一張正常 8-bit PNG，執行真正的 `python -m drone_sr --input ... --output ...`，確認 `Processed: 1`／`Failed: 1`、失敗行列出檔名與原因、退出碼 1、兩張來源檔雜湊不變。
- **失敗行為：** 任一必要檢查失敗時，phase-03 不得開始。

## 可靠性、安全與復原

- 安全與隱私：無。新檢查只讀容器 metadata，不解碼不受信任的完整影像即可拒絕，略為降低解碼大型異常檔的成本。
- 相容性：**誤擋是本階段的主要風險。** 低位深（1／2／4-bit）與調色盤 PNG 是合法輸入，必須有明確回歸測試。
- 資料完整性：來源檔唯讀。
- 復原：改動限於單一函式，`git` 可回復。

## 驗收條件

- [ ] 16-bit PNG colortype 2、4、6 皆以 `ValueError` 被拒絕。
- [ ] 16-bit RGB TIFF 以 `ValueError` 被拒絕。
- [ ] fixture 的來源位深在測試中被獨立確認，而非假設。
- [ ] 1／2／4／8-bit PNG 與調色盤 PNG 仍被接受且結果無損。
- [ ] 16-bit 灰階、float、多頁 TIFF 的既有拒絕仍有效。
- [ ] phase-01 的方向修正未因本階段回歸。
- [ ] CLI 端到端：混合批次的 `Processed`／`Failed`、訊息與退出碼符合預期，來源雜湊不變。
- [ ] 既有測試全過，既有斷言未被放寬。

## 證據、失敗與交接

在 `../build-log.md` 記錄：所採偵測方式與理由、每個 fixture 的來源編碼如何被獨立確認、完整的接受／拒絕對照表（容器 × colortype × 位深）、CLI 端到端輸出、既有測試結果。

若 float 彩色 TIFF 仍無法建立合法 fixture，明確記為未驗證並在 phase-03 的 README 敘述中反映，不得宣稱「浮點全部拒絕」。

發現偵測方式與 `PLANS.md` 記載不符時，建立 `../context/phase-02-source-bit-depth-context.md` 並先修受影響的未開始階段。完成後依 `PLANS.md` 自主模式進入 phase-03。
