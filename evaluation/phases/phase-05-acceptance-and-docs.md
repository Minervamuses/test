# Phase 05 — 真實小樣本驗收、成本量測與文件對齊

## 來源輸入

- `../GOALS.md`（成功條件、已知會影響結論解讀的性質）
- `../PLANS.md`（整體完成標準）
- `../build-log.md`（前四階段的實測數字）
- `README.md:11`、`README.md:156`（目前明示不提供 PSNR／SSIM 的範圍敘述）
- `AGENTS.md`「評估、驗證與回報」

## 目標

在真實原圖上跑完一次有界樣本，產生可引用的數字並經目視檢查；全量執行的成本已依實測估算並回報給使用者；`README.md` 的範圍敘述與實際情況一致；所有未驗證的部分明確列出。

## 範圍內

- 依 `../PLANS.md`「GPU 交接協定」第 2–3 步產生 `evaluation/gpu_checks/run_on_user_shell.sh`，一次做完「待 GPU 補測」清單上的所有項目；先在沙箱內以 CPU 小尺寸煙霧測試，才交給使用者。
- 回收使用者貼回的輸出：寫進 `../build-log.md`，每筆標明量測環境，並勾掉清單對應項目。
- 一次真實小樣本執行（張數依實測耗時決定，預估控制在十分鐘以內）。**依 phase-04 的實測**：沙箱 CPU 單張 30.3 秒、峰值 RSS 4287 MiB、每張產物約 53 MB，十分鐘上限約 20 張；執行器預設 `--limit 5` 對應約 150 秒。交付裝置（GPU）的對應數字由「待 GPU 補測」補上後再定案。交付數字來自使用者 shell 的那次執行；沙箱內若另跑過 CPU 版本，兩筆都保留並各自標明環境。
- 開啟真值、LR、SR、bicubic 四種影像目視檢查，確認內容合理。
- 依實測估算全量 738 張的時間與磁碟成本，寫進 build-log 並回報使用者。
- 文件：新增 `evaluation/README.md`（如何執行、固定約定、結果怎麼讀、每個 run 的體積、限制）。
- 對齊 `README.md:11` 與 `README.md:156`：主 pipeline 本身仍不計算 PSNR／SSIM，評估是 `evaluation/` 的獨立工具；`README.md:156`「沒有配對且對齊的高解析度真值」的敘述需說明本計劃改用合成退化真值，以及這個真值的前提。
- 逐條核對 `GOALS.md` 的成功條件與 `PLANS.md` 的整體完成標準。

## 非目標

- **不跑全量 738 張。** 需要使用者另外同意。
- 不因為數字不如預期而調整退化流程、度量約定或模型設定。
- 不做模型比較、不做畫質優化、不做 SwinIR 驗收。
- 不改 `AGENTS.md`。

## 依賴與前提

- 依賴階段：04 `Complete`。
- **已解（phase-04 實測）：** 單張成本與記憶體見上；`context/phase-04-context.md` 記錄了 SSIM 實作的成本修正與「PSNR／SSIM 恆在 CPU」這項裝置歸屬，後者影響報告標頭怎麼寫，驗收時需確認標頭已分欄。
- **Unresolved：** 小樣本的代表性。`input/` 是同一次飛行的連續影像，場景高度相似，小樣本的平均不能外推成「本專案在各類場景的表現」。挑樣本時盡量涵蓋不同時間戳，並在報告與 build-log 記明此限制。
- **Unresolved：** 全量執行是否值得做，由使用者在看到成本估算後決定。

## 預期影響的元件

- 新增：`evaluation/README.md`。
- 修改：`README.md` 的範圍敘述（第 11 行附近與第 156 行附近，實作時以實際行號為準）。
- 寫入：一個新的 `evaluation/runs/<timestamp>/`。

## 授權與停止條件

- 常規：跑有界小樣本、寫 `evaluation/README.md`、修改 `README.md` 中與評估範圍相關的敘述。
- **停止：** 全量執行，或任何預估超過約十分鐘的執行。
- **停止：** 需要修改 `AGENTS.md`（禁止）。
- **停止：** 小樣本結果與 `GOALS.md` 的某項成功條件矛盾且原因不明。先診斷並記錄，不得把矛盾的結果當成通過。

## 實作與驗證計劃

### Preflight

- 確認 phase-04 為 `Complete`。
- 確認磁碟可用空間足以容納本次 run（phase-04 實測每張約 53 MB；5 張約 265 MB）。
- 記錄 `input/`、`output/`、`src/`、`tests/` 狀態供結束比對。

### 執行與觀察

本階段以觀察為主，不需要 red／green。程序：

1. 跑一次小樣本，記錄命令、run 目錄、實際耗時。
2. 開啟至少兩張圖的四個版本（真值、LR、SR、bicubic）目視檢查：構圖與色彩正常、SR 沒有明顯 artifact、bicubic 明顯較模糊。**目視結果要如實寫，包含不利於 SR 的觀察。**
3. 讀一次 `report.md`，逐欄確認有值。
4. 三個指標各自看勝方。若出現 `GOALS.md` 預告的組合（PSNR／SSIM 輸、LPIPS 贏），如實記錄並依該段說明解讀，**不得回頭調整實驗**。
5. 依實測耗時與體積估算全量成本。

### Verification

- **代表性驗收：** 小樣本 `report.md` 逐張與平均都有值，失敗／排除清單與實際相符。
- **不變式：** `src/drone_sr/`、`tests/`、`pyproject.toml`、`requirements-wsl.txt`、`input/`、`output/`、`models/` 未變動（雜湊或 `git status --short`）。
- **既有測試：** 收尾跑一次 `.venv/bin/python -m unittest discover -s tests`，確認仍全數通過。
- **文件：** `README.md` 修改後，其範圍敘述與實際行為逐條對應；`evaluation/README.md` 的每個命令都實際跑過。
- **完成標準核對：** 逐條走過 `GOALS.md` 的成功條件與 `PLANS.md` 的整體完成標準，每條對應到一筆觀察證據或一筆明確記錄的限制。
- **失敗行為：** 任一成功條件缺證據，計劃不得標為完成；把缺項寫進 build-log。

## 可靠性、安全與復原

- 本階段是唯一產生「可對外引用數字」的階段，主要風險是**過度宣稱**。每個數字都要附帶其前提：樣本張數、場景單一、真值來自 JPEG、RGB 而非 Y 通道、純 bicubic 退化、device。
- `README.md` 的修改要保守：只改與評估範圍相關的敘述，不重寫其他段落。

## 驗收條件

- [ ] 交接腳本已在沙箱內煙霧測試過，且使用者已在自己的 shell 執行過一次，輸出已寫進 build-log 並標明量測環境。
- [ ] 「待 GPU 補測」清單已清空。
- [ ] 一次真實小樣本執行完成，命令、run 目錄、耗時、張數已記錄。
- [ ] 至少兩張圖的四個版本已開啟目視檢查，觀察結果如實記錄（含不利觀察）。
- [ ] `report.md` 逐張、平均、失敗清單、標頭欄位全部有值。
- [ ] 三個指標的勝方與差距已記錄，並依 `GOALS.md` 的解讀前提說明。
- [ ] 全量 738 張的時間與磁碟成本已估算並回報使用者；全量**未**執行。
- [ ] `evaluation/README.md` 存在，其中的命令都實際跑過。
- [ ] `README.md` 的範圍敘述與實際情況一致。
- [ ] `src/`、`tests/`、`input/`、`output/`、`models/`、manifest 未變動；既有測試仍全數通過。
- [ ] `GOALS.md` 每項成功條件都對應到證據或明確記錄的限制。
- [ ] 未驗證項明列：全量資料集、GPU 路徑（若本次為 CPU）、PNG 原圖的真實資料、其他場景、SSIM 交叉核對狀態。

## Commit 切點

文件類本來就依檔案分顆，避免評估工具的說明與主 README 的範圍修正混在一起：

1. `docs: add evaluation tool usage and limitations` — 只動 `evaluation/README.md`。
2. `docs: align README scope with the evaluation tool` — 只動 `README.md`（第 11 行附近與第 156 行附近的範圍敘述）。單獨成顆，讓日後能只 revert 主 README 的改動而不影響評估工具。
3. `docs: close the evaluation plan with acceptance evidence` — 只動 `evaluation/build-log.md`。body 記小樣本的 run 目錄、三個指標的勝方、全量成本估算，以及未驗證項清單。

## 要記錄的證據

- 小樣本的實際數字（逐張與平均），或指向 run 目錄的 `report.md`。
- 目視檢查的具體觀察，不只是「看起來正常」。
- 全量成本估算的推算方式與依據的實測值。
- 文件修改的具體位置與改動內容。
- 最終的未驗證項清單。

## 交接

- 本階段完成即為整體完成。停止，不自行展開後續的畫質優化、模型比較或全量執行。
- 若使用者之後同意全量執行，那是一次新的授權，依同一套執行器與同一份固定約定進行，並在 `build-log.md` 追加紀錄。
