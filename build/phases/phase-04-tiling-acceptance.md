# Phase 04 — 自動分塊與 V1 驗收

## 目標與來源

大型 UAV 圖經同一 Spandrel pipeline 逐塊 SR，輸出尺寸正確、無明顯拼接縫的完整 PNG；使用者仍只決定資料夾。完成 README 及 V1 全部證據對照。

依據 [GOALS.md](../GOALS.md)、[PLANS.md](../PLANS.md) 及 phase-03 已確認行為。

## 範圍與非目標

固定內部 tile／overlap、邊界與 padding／裁回配合、必要記憶體處理、correctness tests、真實驗收及 README。

不做參數掃描、OOM retry 框架、磁碟串流框架、precision 調參、benchmark。若真實尺寸超出最小流程能力，提出證據及最小方案，不自動擴建系統。

## 依賴與前置未知

- phase-03 Complete，兩模型共用流程已證明，候選已選。
- 使用者提供至少一張真實大型圖及少量小圖；唯讀確認尺寸／mode、scale、當時 RAM／VRAM。
- tile 約 512、overlap 約 32 只是需求起點，並非已驗證值。清楚定義有效核心區、擴展 halo、拼回座標，避免含義混用。
- 先以有限小裁切估大圖成本；預計超過約十分鐘或資源不足時，依 PLANS.md 提前告知並取得所需同意。
- descriptor 指示不適合 tiling 時先查原因，不靜默忽略或依模型名稱繞過。Phase-03 已實測 SwinIR-M 為 DISCOURAGED（可分塊但上下文可能影響結果），見 ../context/phase-03-context.md；兩模型各做最小 direct/tile 檢查，大圖以 Compact 候選驗收，不以小例宣稱 SwinIR 全尺寸無縫。

## 預期影響元件與授權

新增有實際職責的 src/drone_sr/tiling.py，接到 inference.py，必要時局部改 image_io.py；tests/test_tiling.py、直接受影響既有測試、README。

不改 AGENTS.md、不加依賴或持久化框架；超出 PLANS.md 時先做可審查提案。

## 實作與驗證

1. **Preflight：** 讀真實尺寸及現有程式。由輸出寬×高×通道×dtype 估最少 RAM，再考慮拼接／編碼副本。tile 限制模型工作集，不能假裝解決完整輸出 RAM。
2. **先測座標：** 用已知像素 ramp／座標標記及可預知放大函數測覆蓋、邊界、裁回。這是拼接 oracle，不是真實 SR 或 Bicubic baseline。
3. **最小分塊：** 以有效核心區切圖，帶 overlap 上下文。每塊呼叫同一 descriptor，按 scale 裁 halo，寫回對應核心位置。每有效區只寫一次，外邊界按實際圖裁切。
4. **尺寸要求：** tile 同樣遵從已確認 descriptor padding／裁回，拼接位置使用原始圖座標，不能把 padded 尺寸當核心。
5. **資源：** 大圖完整輸入／拼接結果在 CPU，GPU 一次只保留當前 tile 與結果，回傳後釋放引用。小圖可整張；用實測固定門檻，不提供 tile args。
6. **接縫檢查：** 可負擔 direct 的小型真實裁切分別走 direct／內部強制 tile，觀察同位置邊界；不要求逐像素完全相等。兩模型各用最小裁切確認共用 tile 相容，不形成效能 sweep。
7. **代表大圖：** 最終候選對一張真實大型 UAV 圖 auto tile，開啟完整 PNG，再看穿過接縫的道路／屋頂／紋理、右邊、下邊、右下角。不得有明顯接縫、空白條、重影、裁切缺失。失敗按位置診斷，遵守次數上限。
8. **固定預設：** 候選通過大圖才定為 models/model.pth。若改另一個已驗證候選，只補直接受影響最小實例，不全資料集重跑。
9. **README：** 寫已驗證 Linux/WSL、一次性準備、精確依賴版本、開發者固定權重來源／放置方式；使用者操作區只有預設命令及 --input／--output。說明 PNG／覆蓋、圖片限制、錯誤、實測範圍。權重缺失是準備錯誤，不是每次讓使用者選模型。

### 預定 correctness 檢查

~~~bash
python -m unittest discover -s tests -p 'test_tiling.py' -v
~~~

少量案例覆蓋下表，T 為單元測試的小型核心邊長如 8，並非 production 設定，避免大型 tensor：

| 尺寸 | 例子（寬×高） | 必查 |
|---|---|---|
| 可整除 | 2T × 2T | 核心覆蓋一次，接點不重複 |
| 不可整除 | (2T+3) × (T+5) | 右、下、右下角 |
| 小於 tile | (T-1) × (T-3) | 無空 tile，完整內容 |
| 奇數 | (2T+1) × (2T-1) | 不少列／多列 |
| 模型限制 | 不滿足已知 size requirements | padding 正確裁回 |

以至少兩個小倍率測座標；真實驗收使用 checkpoint 實際 scale，不能硬寫 x4。檢查尺寸、已知像素位置及每個有效區都有結果。

### 收尾整合驗證

固定最小真實批次驗證預設與自訂資料夾；重用仍有效證據，流程變更才重跑相關項。大圖成功、壞圖繼續、來源不變、覆蓋與無關輸出保留都有證據。

便宜 correctness suite 收尾執行一次：

~~~bash
python -m unittest discover -s tests -v
~~~

真實 checkpoint 測試為明確 opt-in 開發者驗證，不能讓 suite 每次載入兩模型或跑大圖。若 suite 昂貴，先按 PLANS.md 處理。

## 驗收條件

- 所有表列尺寸／邊界正確，padding 無殘留。
- 兩模型最小 tiled 實例通過同一路徑，最終模型有一張真實大圖及視覺證據。
- 最終寬高正確、無明顯接縫；不是只看 stub／shape。
- 小圖 direct、大圖 auto tile，CLI 維持資料夾介面。
- GOALS.md 每個成功條件有觀察依據，README 與限制真實；缺必要檢查不得標 V1 完成。

## 證據、失敗與交接

../build-log.md 記最終 checkpoint、固定 tile／overlap／門檻定義、測試命令、真實檔案／尺寸、device、耗時、接縫檢視位置與結果；重要資源／拼接發現才寫 ../context/phase-04-context.md。

大圖或接縫驗收無法完成，記 Blocked 與缺項，不能縮圖掩蓋大圖要求。保留原圖與先前有效 output，依 PLANS.md 修正／停止。

全部驗收後更新 build-log.md，回報實際產物、限制並停止；無後續優化階段。
