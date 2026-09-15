# build — Drone Image Super-Resolution V1 目標

## 目的與背景

讓使用者交付本機圖片，執行一次命令後取得 SR 圖片。使用者負責選資料夾，模型與推論細節由程式處理。

本計劃依 2026-09-15 完整需求貼文，以及同日補充：「我之後會拿到本機，現在你做成可以透過 args 指定資料夾的樣子」。因此資料夾參數納入 V1，未指定參數的簡單流程仍保留。根目錄 AGENTS.md 的 Docker／效果評估是較廣的專案背景，本次明確排除 Docker、PSNR／SSIM 與 benchmark，依本次要求執行。

## 預期成果與對外介面

完成一次性環境與權重準備後，從專案根目錄執行：

~~~bash
python -m drone_sr
~~~

預設讀取目前工作目錄的 input/，寫入 output/。也可指定資料夾：

~~~bash
python -m drone_sr --input "/path/to/images" --output "/path/to/sr-results"
~~~

兩個參數各自可省略，支援含空白的相對／絕對 Linux 路徑；相對路徑以目前工作目錄為基準。以上為預定介面，目前尚無程式。

只掃描輸入資料夾第一層，一次處理一張，以穩定順序執行。至少接受 .jpg、.jpeg、.png、.tif、.tiff，副檔名不分大小寫。輸出為同 stem 的 PNG，例如 DJI_001.JPG → DJI_001.png。原始圖片須保留。

## 成功條件

1. 預設及指定資料夾命令，均對少量真實圖片產生可開啟的 SR PNG，摘要可對應每個輸入。
2. 一條 architecture 無關的 Spandrel 流程，分別使用 Real-ESRGAN Compact、SwinIR 真實 checkpoint 成功推論；開發者驗證後選單一預設，最終一次啟動只載入 models/model.pth。
3. CUDA 可用時自動 GPU，不可用時自動 CPU，啟動明示實際裝置；兩個分支均有驗證。CPU 只需極小實例，不能以大圖 CPU 長跑替代 GPU 相容性確認。
4. RGB → float [0,1] → CHW → BCHW → model → clamp → PNG；模型與 tensor 的 dtype／device 一致。輸出寬高嚴格為原始寬高各乘 descriptor.scale。
5. 小圖直接推論，大圖自動帶 overlap 分塊。可整除、不可整除、小於 tile、奇數尺寸、最右、最下及右下角無缺列、多列、錯位或殘留 padding；真實圖檢視無明顯拼接縫。
6. output 不存在會建立；只覆蓋本次成功產生的同名結果，其他輸出與原始圖保留。失敗項目不能冒充成功。
7. 缺輸入、空輸入、缺模型／載入失敗、單張壞圖符合下節行為，成功／失敗數量可核對。
8. 必要 correctness tests 與 README 均有實際驗證證據。stub、mock、程序退出成功或文件內容，不等於真實模型／圖片驗收。

## 範圍與不可變條件

- SR backend 只有 Spandrel；ModelLoader().load_from_file(model_path) 取得 descriptor，推論呼叫 descriptor。不得雙套 inference 或依模型名稱分支。
- 固定模型位置錨定專案內部，不能隨 --input／--output 改變。開發者可替換 checkpoint／內部設定，不提供 --model 或 model path 參數。
- 不提供 --device、tile size／overlap、batch size、scale、padding、overwrite 等技術選項；--help 只需基本操作和資料夾參數。
- 模型倍率與 size requirements 來自 descriptor。兩模型測試是相容性驗證，不展開排名。
- 缺輸入或輸入不是目錄：清楚報錯並停止。
- 空輸入：No supported images found in input/；自訂路徑顯示實際目錄。
- 缺模型：SR model not found: models/model.pth。Spandrel 載入失敗也停止並指出原因。
- 壞圖：記錄檔名及原因，記為 Failed，繼續下一張。Processed 是本次成功寫出數，Processed + Failed 等於列舉的支援圖片數。
- Console 只保留標題、Device、Model: loaded、Images、[i/N] 檔名／失敗原因，以及 Finished／Processed／Failed／Output。
- 同 stem 衝突（如 001.jpg、001.png 都映射 001.png）：將衝突輸入記為失敗，繼續其他圖片，不任意改名或靜默遺失其中一張。這是保留輸入與結果對應的最小內部規則。
- 指定資料夾後仍不得覆寫任何輸入：相同輸入／輸出目錄應拒絕；輸出檔經路徑解析或檔案別名指回輸入時，也須在寫入前拒絕。
- 以普通圖片轉 RGB PNG 為目標；不承諾多頁 TIFF、高位深／多光譜保真、alpha 或 GIS metadata 保存。遇無法正確解碼／轉換的實際圖應明確記失敗，不假裝支援。

## 非目標

PSNR、SSIM、SR quality benchmark、Bicubic baseline、dataset download／selection、training、fine-tuning、多模型競賽、Docker、GUI、Web API、空拍影像拼接、GIS、ODM、object detection、segmentation。

不建立 plugin system、backend registry、model factory framework、Hydra config、database、DataLoader、worker、並行管線、通用測試／評估框架或動態參數搜尋。

## 限制與依據

- **環境：** 根目錄 AGENTS.md 指定 Linux／WSL Ubuntu 24.04；Windows Agent 透過 wsl.exe 操作 Linux shell、Git、Python、套件與檢查工具。應用程式不寫死部署路徑。
- **資源與成本：** 依 AGENTS.md，在下載／安裝／模型推論前確認實際資源、相容性與成本；先最小樣本。全資料集、模型／GPU 掃描、付費服務或預計超過約十分鐘的工作需已有明確授權。
- **材料：** 使用者將稍後提供本機圖片及權重；不下載 dataset 補足。目前不承諾模型速度、最終 tile 參數或框架相容性。
- **授權：** 本次只建立計劃；後續實作與環境授權由 PLANS.md 管理。

## 未知與待決事項

目前沒有阻止計劃成形的產品決策。待實作取得：

- 真實圖片、兩個 checkpoint 的本機位置、精確版本／來源與使用條件；使用者稍後提供。
- 相容依賴版本、CUDA 實際可用性、descriptor 尺寸行為：phase-01。
- 兩模型共用流程證據、單一預設候選：phase-03，經 phase-04 大圖確認後定案。
- 真實圖片尺寸／TIFF 模式、合理固定 tile／overlap 與切換門檻：phase-04。

缺真實材料可準備程式與合成 correctness checks，但真實推論的必要驗收仍未完成；不能用下載 dataset 或大量 CPU 推論補洞。

## 來源

- [專案指引](../AGENTS.md)。
- 使用者 2026-09-15 完整貼文「建立一個簡單可靠的 Drone Image Super-Resolution 批次推論專案」，及同日新增 args 資料夾要求。本文件已保留實質要求，續作不依賴暫存附件或聊天記憶。
