# Phase 02 — 資料夾 CLI 與自動裝置

## 目標與來源

無參數或 --input／--output 指定資料夾均可批次執行，成功輸出、逐張失敗與摘要能對回輸入。

依據 [GOALS.md](../GOALS.md) 的介面／錯誤行為及 [PLANS.md](../PLANS.md) 授權。

## 範圍與非目標

包含資料夾參數、格式列舉、序列批次、output 建立／定點覆蓋、來源保留、自動 device、簡潔 log 與錯誤隔離。

不加模型／device／tile 選項、遞迴、並行或持久化報告；SwinIR、大圖留後續。

## 依賴與前置未知

- phase-01 在 build-log.md 為 Complete，單張 Compact 已跑通。
- 查看實際圖片 metadata；五種格式 correctness 可用局部合成圖，真實輸出沿用小樣本。
- 破壞性案例只放測試暫存資料夾，包含正常、損壞圖、既有 output。
- 最小內部退出碼約定：全成功或無支援圖片為 0；設定／模型致命錯誤或批次存在失敗為非 0。不增加使用者選項。

## 預期影響元件與授權

主要改 __main__.py、model.py、image_io.py，必要時局部調整 inference.py；加入 tests/test_cli.py，補既有 I/O／inference 測試與 README 基本命令。

這是新功能必要路徑，不借機重構。一般操作依 PLANS.md；額外依賴及昂貴工作須已有授權。

## 實作與驗證

1. **Preflight：** 核對單張證據與實際測試命令。先加最小 CLI／I/O 失敗測試，再加入參數解析，兩參數各自預設 input/、output/。
2. **路徑：** 穩定列舉第一層，忽略不支援檔案；模型獨立錨定專案。先驗證目錄及輸出映射再寫檔。
3. **資料保留：** 依 GOALS.md 處理同 stem 衝突及來源保護。成功結果採最小同目錄暫存寫入後替換，失敗不截斷舊成功結果。只清本次暫存，不刪整個 output。
4. **Device：** cuda if torch.cuda.is_available() else cpu；顯示實際 GPU 名稱或 CPU。模型只載入一次，tensor 跟隨裝置。CUDA 不可用自動 CPU；CUDA 推論失敗不新增默默 CPU 重跑機制。
5. **批次邊界：** 致命輸入／模型問題在開始前處理；單張解碼／推論／儲存失敗記檔名原因、繼續其他圖。舊檔不能算本次成功。
6. **Log：** 僅輸出 GOALS.md 的啟動、[i/N]、失敗原因及成功／失敗摘要。

### 預定檢查

工具鏈／檔案建立後執行：

~~~bash
python -m unittest discover -s tests -p 'test_cli.py' -v
python -m unittest discover -s tests -p 'test_image_io.py' -v
python -m drone_sr --help
~~~

最小測試涵蓋：

- 預設、僅 input、僅 output、兩者指定、含空白路徑；缺／空輸入及輸出不是目錄。
- jpg/jpeg/png/tif/tiff 及大寫副檔名；壞圖夾在兩張好圖間。
- 重跑覆蓋同名、無關 output 不變；同 stem 衝突、來源別名被拒絕；儲存失敗不破壞舊輸出。
- mock CUDA availability 只驗證選擇分支，不冒充硬體推論。

用兩張真實小圖和一個損壞副本，跑預設及指定資料夾命令；重用樣本。記錄實際路徑、來源雜湊、console、退出碼，開啟成功 PNG。

實際 GPU 證據可重用 phase-01；CPU 用極小真實裁切，在測試程序控制 CUDA 不可見，走相同自動選擇程式，不新增公開參數。先估成本，不能整張大圖 CPU 長跑。

## 驗收條件

- 兩種介面均正確輸出，--help 無被排除技術選項。
- 兩張成功、一張失敗批次跑到底，Processed: 2、Failed: 1，結果可核對。
- 缺輸入／模型、空目錄及壞圖處理符合 GOALS.md，致命錯誤不展開批次。
- 原始檔與無關 output 保留；覆蓋、衝突及儲存失敗無誤報。
- 自動 device 分支、真實 CUDA 及極小 CPU 證據分別記錄，限制明確。

## 證據與交接

../build-log.md 記 CLI／測試命令、各檔結果、雜湊、退出碼、真實 GPU／CPU 和耗時；重要路徑決策才寫 ../context/phase-02-context.md。

必要驗證完成才進 phase-03，失敗依 PLANS.md 阻擋後續並修當前原因。
