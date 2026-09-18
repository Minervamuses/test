# Drone Image Super-Resolution

本機、單一 Spandrel 推論流程。已完成 build/ 四階段 V1：**資料夾批次、自動 GPU／CPU、小圖直接推論與大圖自動分塊**。從 `input/` 或指定資料夾逐張讀取圖片，使用專案內的 `models/model.pth`，將同 stem 的 RGB PNG 寫入 `output/` 或指定資料夾，保留原圖。

交付預設為官方 `realesr-general-x4v3.pth`（Compact）：已將一張真實 3840×2160 海面畫面處理為 15360×8640 PNG，並完成批次／極小 CPU 驗證。SwinIR-M 通過 512×512 真實裁切與最小分塊相容性；完整影片處理、SwinIR 大圖與畫質排名不在本次驗證範圍。

## 採用的環境與版本

目標為 Linux／WSL Ubuntu 24.04、Python 3.12、x86_64。使用 `.venv` 與 pip，透過 setuptools 的 editable 安裝連結 `src/drone_sr/`；模型位置固定錨定原始專案目錄，與執行命令的位置無關。

| 元件 | 版本／來源 |
|---|---|
| Python | 本機 3.12.3，Ubuntu 24.04.2 |
| pip | venv 內 24.0 |
| torch | 2.11.0+cu128，PyTorch 官方 CUDA 12.8 wheel |
| torchvision | 0.26.0+cu128，與 torch 配對的官方 wheel |
| spandrel | 0.4.2，PyPI |
| Pillow | 12.3.0，PyPI |
| setuptools | 81.0.0，`setuptools.build_meta` |
| NumPy／safetensors／einops | 2.5.3／0.8.0／0.8.2，PyPI 傳遞依賴 |
| Triton | 3.6.0，PyPI 傳遞依賴 |
| CUDA runtime／cuDNN | 12.8.90／9.19.0.56，NVIDIA 官方 wheel |

torch／torchvision 的版本配對依 [PyTorch 官方安裝說明](https://pytorch.org/get-started/previous-versions/)；採 CUDA 12.8 wheel 的依據是 [Blackwell 支援](https://pytorch.org/blog/pytorch-2-7/)。[requirements-wsl.txt](requirements-wsl.txt) 固定主要套件、Triton 與必要 CUDA wheel 的版本／官方來源；NVIDIA wheel 的 SHA-256 與 PyPI 對應檔案相同。NumPy、safetensors、einops 等其餘傳遞依賴由 pip 解析，上表記錄本次實際版本，並非完整 lock。

本機唯讀資源觀察為 NVIDIA GeForce RTX 5070 Ti **Laptop** GPU，driver 591.74，VRAM 12227 MiB，compute capability 12.0。這些硬體資訊本身不能證明 checkpoint 可推論；實測狀態見下方「驗證紀錄」。

## 安裝

以下是已批准的 Linux x86_64／Python 3.12 安裝步驟，請在專案根目錄執行。其他 Python 版本需另選對應 wheel。GPU 需要 WSL 可見的相容 NVIDIA driver；套件會提供 CUDA runtime，不需另行安裝系統 CUDA Toolkit。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --no-deps --no-cache-dir --progress-bar off \
  'https://download.pytorch.org/whl/cu128/torch-2.11.0%2Bcu128-cp312-cp312-manylinux_2_28_x86_64.whl' \
  'https://download.pytorch.org/whl/cu128/torchvision-0.26.0%2Bcu128-cp312-cp312-manylinux_2_28_x86_64.whl'
python -m pip install --no-cache-dir --only-binary=:all: --progress-bar off -r requirements-wsl.txt
python -m pip install --no-deps --no-build-isolation -e .
```

第一步只裝兩個官方 wheel，第二步補齊必要依賴，完成前請勿執行推論。本次先保留第一次下載成功的兩個 wheel，從本機檔案安裝後續接以上依賴命令；沒有額外重跑一次全新的環境建置。

來源採 PyTorch 的 `download.pytorch.org`、NVIDIA 的 `pypi.nvidia.com`，其餘套件使用 PyPI。前者避開本機曾回傳 403 的 `download-r2.pytorch.org`；NVIDIA 來源則處理 PyPI cuDNN 下載過慢的實際問題。CUDA wheel 約 2.93 GB，另有 torch／torchvision 約 0.83 GB 與其餘套件，合計約 4 GB。安裝期間請保留約 15 GB 磁碟；本機完成後 `.venv` 實測約 6.7 GiB。沿用已下載 wheel 的安裝花 11 分 13 秒，其他網路環境的時間未驗證。

## 準備與執行

1. 將下方指定的 Compact RGB SR `.pth` 權重準備為專案的 `models/model.pth`。程式不會下載模型。本機已保存原檔名，並以相對 symlink `models/model.pth → realesr-general-x4v3.pth` 使用它。
2. 將圖片放在 `input/` 或指定資料夾第一層，接受 `.jpg`、`.jpeg`、`.png`、`.tif`、`.tiff`（大小寫皆可），不遞迴掃描。
3. 在專案根目錄、啟用環境後執行：

```bash
python -m drone_sr
```

指定資料夾時：

```bash
python -m drone_sr --input "/path/to/images" --output "/path/to/sr-results"
```

兩個參數各自可省略，預設為 `input/`、`output/`。含空白路徑請加引號；相對路徑以執行時的工作目錄為基準。模型仍固定於專案內，不隨資料夾參數改變。

例如 `input/DJI_001.JPG` 對應 `output/DJI_001.png`。輸出不存在會建立；成功 PNG 完整寫入後才替換同名舊結果。來源與其 symlink／hard link 不可被當作輸出覆寫。預設資料夾相對於目前工作目錄，模型仍固定於原始專案內。

啟動時自動選擇可用 CUDA，否則使用 CPU，並顯示 `Device`；CUDA 執行失敗會報錯，不會暗中改成 CPU 重跑大圖。大圖會自動分塊，記憶體與已驗證尺寸見下節；不會自動掃描影片或整個資料集。多頁 TIFF、來源高位深（每通道超過 8-bit）與浮點圖片會明確拒絕；高位深依容器編碼判定（PNG 的 IHDR 位深、TIFF 的 `BitsPerSample`），不是只看解碼後的 Pillow mode，因此 16-bit 彩色也擋得住。普通圖片轉成 RGB；讀入時先依 EXIF Orientation 把方向校正到像素上，輸出 PNG 不保留方向標記，也不保存 alpha、GIS 或其他 metadata。

缺輸入、輸出路徑是檔案、相同輸入／輸出目錄、缺模型或模型載入失敗會報錯並停止；空輸入顯示 `No supported images found in input/`（指定路徑則顯示該路徑）。檔名穩定排序、逐張處理，模型只載入一次。

壞圖、推論或儲存失敗會列出檔名及原因，繼續下一張。多張輸入映射同名 PNG 時，衝突項全部記失敗；輸出指向任何輸入的 symlink／hardlink 也拒絕。成功寫出的數量為 `Processed`，其餘為 `Failed`；全成功或無支援圖片時退出碼 0，設定錯誤或任一圖片失敗為 1。

## 自動分塊與資源

- 寬、高都不超過 **512** 時整張推論；任一邊超過 512 就分塊，無需額外參數。
- 每塊有效核心最多 **512×512**，四側各帶 **32 像素上下文**，模型最大接收 576×576；圖片外緣依實際範圍裁切。按模型倍率裁掉上下文，只把核心寫回一次，descriptor 自動處理最低尺寸／補邊／裁回。
- 完整輸入與大圖拼接結果留在 CPU RAM，GPU 一次只處理當前塊。4K 圖做 4× 時，完整 RGB float32 結果本體約 **1.48 GiB**，編碼另需副本；本機代表批次程序峰值 RSS 約 **5.44 GiB**。分塊不能消除完整輸出的 RAM 需求，請先用少量圖片確認其他尺寸。
- SwinIR descriptor 的 `DISCOURAGED` 表示可分塊但上下文可能改變結果。本次僅驗證 192×176、內部核心 128 的小例；未驗证 SwinIR 的 512 核心大圖或所有場景接縫。最終大圖預設採已驗證的 Compact。

## 採用的權重

- 檔案：[realesr-general-x4v3.pth（官方下載）](https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth)，4,885,111 bytes；[release v0.2.5.0](https://github.com/xinntao/Real-ESRGAN/releases/tag/v0.2.5.0)，asset id 76259217，asset 更新時間 2022-08-30。
- 本機 SHA-256：`8dc7edb9ac80ccdc30c3a5dca6616509367f05fbc184ad95b731f05bece96292`。官方 API 未提供 digest；此值用於本次取得檔案的追溯與後續一致性檢查。
- 實際 descriptor：Compact／SRVGGNetCompact、RGB 3→3、原生 4×、1,213,296 個參數；本程式採 float32。只使用此單一 checkpoint，沒有混合另一個降噪權重。
- 官方 repository [授權文件](https://github.com/xinntao/Real-ESRGAN/blob/v0.2.5.0/LICENSE) 為 BSD-3-Clause。權重與資料不納入 Git；另一台機器需另外準備檔案。

### 開發者已驗證的第二 checkpoint

- [SwinIR-M real-world 4× 官方權重](https://github.com/JingyunLiang/SwinIR/releases/download/v0.0/003_realSR_BSRGAN_DFO_s64w8_SwinIR-M_x4_GAN.pth)：`003_realSR_BSRGAN_DFO_s64w8_SwinIR-M_x4_GAN.pth`，67,129,861 bytes；GitHub release v0.0／asset 44142419，2021-09-06。
- 本機 SHA-256：`b9afb61e65e04eb7f8aba5095d070bbe9af28df76acd0c9405aeb33b814bcfc6`；官方 API digest 未提供。[官方 repository LICENSE](https://github.com/JingyunLiang/SwinIR/blob/main/LICENSE) 為 Apache-2.0。
- Spandrel 0.4.2 實測辨識為 SwinIR，RGB／4×／11,715,559 parameters；minimum=16、multiple=1。採 FP32；descriptor 不支援 FP16，tiling 為 DISCOURAGED（可能產生上下文差異）。
- 驗證時僅暫時將 `models/model.pth` 指向此檔，完成後恢復 Compact；沒有加入模型 CLI 選項。兩顆權重都保留，交付預設為先前使用者選定、已通過 4K 大圖且資源需求較低的 Compact，不宣稱畫質最優。
- 真實 512×512 → 2048×2048 RGB PNG：CLI 約 **11.64 秒**；獨立一次上傳＋GPU 推論 **3.24 秒**，PyTorch 峰值 allocated **4.32 GiB**／reserved **6.65 GiB**（截至 forward，排除 CUDA context、其他程序和 PNG 階段）。此案例在本機 12 GB 筆電 GPU 通過，不等於全尺寸 SwinIR 驗證。
- 同一權重另通過 17×19 → 68×76、1×1 → 4×4 的尺寸檢查。已開啟真實 PNG，內容、色彩和尺寸正常；細紋平滑，無高解析度真值，不做畫質排名。來源／輸出／命令／量測位於 `test-data/phase-03-swinir-20260917/`，結果為其 `output/whaledrone_seek10s_x1536_y768_512.png`。

## 驗證紀錄

2026-09-15，在上述 WSL 環境已確認：

- `pip check` 通過；專案 editable 安裝成功。
- 下列 focused checks **13／13 通過**：I/O 7 項，descriptor／模型載入 6 項。
- 使用**未訓練的極小 Compact 模型**與合成 5×7 RGB 圖，實際跑 `python -m drone_sr`：CPU 與 CUDA 各成功寫出 10×14 PNG，原圖 SHA-256 不變。CPU 子程序透過 `CUDA_VISIBLE_DEVICES=''` 隱藏 GPU，實際執行 CPU 分支；GPU 子程序自動選 `cuda:0`，wheel 包含 `sm_120`。各命令約 2.03／2.48 秒，僅是這個極小案例的耗時。
- 缺模型、不可載入模型、壞圖的實際 CLI 錯誤／計數符合預期；既有成功 PNG 在模型錯誤後保持不變。`--help`、空輸入與缺輸入檢查通過。
- 當時尚未驗證真實圖片與預訓練 Compact checkpoint；此缺項已於下列 2026-09-17 單張驗證補足。當時 SwinIR、大圖／分塊、資料夾 args／批次尚未驗證，後续已補足下列必要實例；未重跑一次全新環境建置。

2026-09-17，使用上述正式權重與已下載的 WhaleDrone 影片：

- 從第 10 秒 seek 畫面取 `(x=1536, y=768, w=512, h=512)` 海面裁切，執行真正 `.venv/bin/python -m drone_sr`；`cuda:0`、Processed 1／Failed 0，產生 2048×2048 RGB PNG，影片／輸入／權重 hash 不變。
- CLI 包含程序啟動約 5.90 秒。另一次同一 production 函式路徑量測：GPU 同步計時的上傳＋推論約 0.220 秒，PyTorch 峰值 allocated 約 264 MiB／reserved 284 MiB（模型載入至推論結束，不含 CUDA context／其他程式或 PNG 輸出階段；不是整張顯卡用量）。沒有 warmup 或參數掃描，兩次結果像素一致。
- 已開啟原圖及 PNG：海面構圖、反光位置與藍綠色正常；細紋較平滑，未證明新增紋理是真實細節，沒有畫質分數或鯨魚細節驗收。此小裁切的 VRAM 有餘裕，不能據此承諾 4K 全圖或整段影片效能。
- 輸入：`input/whaledrone_seek10s_x1536_y768_512.png`；輸出：`output/whaledrone_seek10s_x1536_y768_512.png`；完整來源／命令／雜湊／量測存於 `test-data/phase-01-compact-20260917/` 與 build-log。此目錄的腳本是單次驗證紀錄，不是正式 CLI 或可重跑 benchmark。

同日完成 Phase 02：

- CLI correctness tests 12／12、直接相關 I/O tests 7／7 通過。模型與快速 tensor 放大在 CLI tests 中是 mock；真實推論另由下列案例驗證。
- 預設及指定含空白／相對路徑的批次，各用兩個真實小裁切和中間一張故意損壞的圖片；GPU 均跑到底，Processed 2／Failed 1、退出碼 1 符合預期，成功 PNG 開啟正常。原始 hash、無關 output 保留，既有同名測試結果成功替換；兩種介面輸出 hash 相同。
- 隱藏子程序 CUDA 後，以同一正式權重及真正 CLI 跑 32×28 真實裁切，CPU 成功產生 128×112 PNG，約 2.11 秒（含啟動）；沒有拿 mock 當 CPU 證據。
- 原始素材座標、格式、hash、完整 console／命令與結果存於 `test-data/phase-02-cli-20260917/` 及 build-log。此目錄的壞圖與舊輸出僅供本次隔離驗收。
- 本輪收尾完整軟體 suite 25／25 通過（`python -m unittest discover -s tests -v`，無 skipped）；真實推論不包含在此 suite。當時 Phase 03 因缺 SwinIR checkpoint／下載授權而 Blocked，Phase 04 分塊尚未開始。後續已選定官方 SwinIR-M real-world 4×、512×512 驗證；67.13 MB 權重測速估約 24 分鐘，使用者已批准計劃內工作；下載與 SwinIR 驗證現已完成，詳見下節及 build-log 最新紀錄。

### V1 最終驗收（2026-09-17）

- 兩模型的真實 direct／tiled 小例均成功：Compact 640×576 → 2560×2304，走正式 512 核心自動分塊；SwinIR 192×176 → 768×704，使用內部強制 128 核心。完整圖與接縫交會裁切已檢視，這些海面樣本未見明顯拼接線；不要求兩條路徑每像素相同。
- Compact 真正 CLI 同批次處理完整 4K 圖、故意壞圖、32×28 真實小圖：**Processed 2／Failed 1／退出碼 1** 符合預期，壞圖後仍繼續。整批含啟動／推論／PNG 約 **37.96 秒**，不是單獨 GPU forward 的時間。
- 完整輸出為 **15360×8640 RGB PNG、117,800,469 bytes**，SHA-256 `bce5bfc0b9b347f06982e13f56c49ee6cc43ca910f1bf0c558887e4d613d7822`。原圖及無關輸出 hash 保留，驗收目錄的同名舊結果只在成功後替換。
- 完整 PNG 已解碼；影像檢視工具無法傳輸約 118 MB 原檔，因此人工檢查使用其全圖縮覽、原尺寸接縫及最右／最下／右下裁切。未發現明顯拼縫、空白條、重影或裁切缺失。Pillow 對此 1.33 億像素結果會發出尺寸警告，但本次解碼成功；未停用圖片保護。
- 最終完整 correctness suite **29／29 通過、無 skipped**；`--help` 仍只有資料夾參數。預設／指定資料夾與極小 CPU 的既有真實證據沿用，未重跑不受影響的案例。

本機結果：[全圖預覽](<test-data/phase-04-tiling-20260917/full batch/full-preview.png>)、[完整 PNG（約118 MB）](<test-data/phase-04-tiling-20260917/full batch/output/a_full.png>)。來源、完整命令、尺寸、雜湊、裁切與結果為 `test-data/phase-04-tiling-20260917/` 下的 JSON／console，階段紀錄為 [build/build-log.md](build/build-log.md)。圖片／權重不納入 Git。

驗收資料只來自使用者指定的單一 [WhaleDrone](https://huggingface.co/datasets/LucieLprt-Dvldr/WhaleDrone) MP4（資料集標示 CC-BY-NC-4.0），沒有下載 SRT 或其他影片。結果是海面場景，沒有鯨魚／道路／屋頂細節或配對高解析度真值驗證。V1 不含整段影片轉換、Docker、PSNR／SSIM、模型排名；未重新建立第二套乾淨環境驗證安裝。

### 讀圖正確性修正（2026-09-18）

`read_image()` 的兩個已重現缺陷已修正，兩者都會讓程式正常結束卻輸出與來源意義不符的內容：

- **EXIF 方向未套用。** 現於 mode 與單影格檢查之後、轉 RGB 之前呼叫 `ImageOps.exif_transpose()`。八個 Orientation 值（JPEG 與帶 `eXIf` chunk 的 PNG）經 `read_image()` → `write_png()` 後，輸出**逐像素**等於正確結果；Orientation 2／3／4 尺寸不變但像素會錯，只比尺寸看不出來。TIFF 由 Pillow 自行處理，未被旋轉兩次。
- **高位深拒絕不完整。** 原本只看 `image.mode`，而 Pillow 把 16-bit PNG colortype 2／4／6 與 16-bit RGB TIFF 映射成 `RGB`／`RGBA`，通過白名單後被靜默截成 8-bit（來源通道值 256／257／511 全變成 1）。現於任何解碼之前讀容器編碼，超過 8-bit 即以 `ValueError` 拒絕，該張記為 Failed 並繼續下一張。1／2／4-bit 與調色盤 PNG 是合法輸入，仍照常接受。
- 完整 correctness suite **33／33 通過、無 skipped**（既有 29 ＋ 本次新增 4）。既有斷言未放寬；repo 內 34 張既有 8-bit 圖片經 `read_image()` → `write_png()` 的輸出位元組與修正前完全相同。
- 真實小批次以正式 Compact 權重、真正 `python -m drone_sr` 執行（**CPU**，本輪環境 `torch.cuda.is_available()` 為 False）：同一張真實海面裁切分別做成無 EXIF 的 64×48 JPEG、真正的 16-bit RGB PNG，以及像素已旋轉並標記 Orientation 6 的 JPEG。結果 `Processed: 2`／`Failed: 1`／退出碼 1，16-bit 那張列出原因且未產生輸出檔，三張來源 SHA-256 不變。方向圖輸出為 256×192，與未旋轉參考圖同向（未修正時會是 192×256），兩者平均差 0.60／255，差異來自旋轉後重新 JPEG 編碼與模型非旋轉等變。

已知限制（本次未處理，且不得視為已驗證）：

- 本輪所有檢查在 **CPU** 執行，未在 GPU 上重跑；此修正只影響讀圖，與裝置無關，但沒有本輪的 GPU 觀察證據。
- 位深檢查涵蓋 PNG 與 TIFF 兩種容器；JPEG 以基線 8-bit 處理，未驗證 12-bit JPEG。
- 浮點圖片的拒絕來自兩條不同路徑：單通道 float（mode `F`）回報 `Unsupported image mode: F`；32-bit float **彩色** TIFF 則是 Pillow 連識別都失敗（`UnidentifiedImageError`），同樣記為該張 Failed，但訊息不是本程式發出的。
- 未壓縮 TIFF ＋ Orientation 5–8 ＋ mode `L`／`P`／`RGBA`／`CMYK` 時，Pillow 會轉置像素緩衝區卻未更新 `size`，輸出既非原圖也非正確方向。這是上游缺陷，本次未處理；本專案實際輸入為 8-bit RGB，碰不到此路徑。
- 輸出 PNG 權限為 `0600`（原子寫入使用 `tempfile.NamedTemporaryFile` 的副作用），本次未更動。

本次修正的計劃、階段文件與完整觀察證據見 [fix/build-log.md](fix/build-log.md)。

```bash
python -m pip check
python -m unittest discover -s tests -p 'test_image_io.py' -v
python -m unittest discover -s tests -p 'test_inference.py' -v
python -m unittest discover -s tests -p 'test_cli.py' -v
python -m unittest discover -s tests -p 'test_tiling.py' -v
python -m unittest discover -s tests -v
```

測試中的合成像素、未訓練小模型與 mock 用來驗證程式契約，**不證明真實 SR 品質或預訓練 checkpoint 相容性**。執行狀態與完整觀察證據以 [build/build-log.md](build/build-log.md) 為準；所有階段的完成條件見 [build/GOALS.md](build/GOALS.md)。
