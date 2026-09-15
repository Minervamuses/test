# Drone Image Super-Resolution

本機、單一 Spandrel 推論流程。目前實作 **Phase 01 單張框架**：從 `input/` 讀取一張圖片，使用專案內的 `models/model.pth`，將同 stem 的 RGB PNG 寫入 `output/`，保留原圖。

**真實圖片與預訓練權重尚待提供，未完成真實 SR 驗收。** 完整批次、`--input`／`--output`、SwinIR 相容性及大圖分塊屬後續階段，目前未提供。請先使用一張小圖；現階段多張輸入會明確停止。

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

torch／torchvision 的版本配對依 [PyTorch 官方安裝說明](https://pytorch.org/get-started/previous-versions/)；採 CUDA 12.8 wheel 的依據是 [Blackwell 支援](https://pytorch.org/blog/pytorch-2-7/)。Pip 也會安裝這些套件所需的 CUDA runtime、cuDNN、Triton、NumPy、safetensors、einops 等傳遞依賴。

本機唯讀資源觀察為 NVIDIA GeForce RTX 5070 Ti **Laptop** GPU，driver 591.74，VRAM 12227 MiB，compute capability 12.0。這些硬體資訊本身不能證明 checkpoint 可推論；實測狀態見下方「驗證紀錄」。

## 安裝

以下是已批准的 Linux x86_64／Python 3.12 安裝步驟，請在專案根目錄執行。其他 Python 版本需另選對應 wheel。GPU 需要 WSL 可見的相容 NVIDIA driver；套件會提供 CUDA runtime，不需另行安裝系統 CUDA Toolkit。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --no-cache-dir --only-binary=:all: --progress-bar off \
  'https://download.pytorch.org/whl/cu128/torch-2.11.0%2Bcu128-cp312-cp312-manylinux_2_28_x86_64.whl' \
  'https://download.pytorch.org/whl/cu128/torchvision-0.26.0%2Bcu128-cp312-cp312-manylinux_2_28_x86_64.whl' \
  'spandrel==0.4.2' 'Pillow==12.3.0' 'setuptools==81.0.0'
python -m pip install --no-deps --no-build-isolation -e .
```

官方 wheel 目錄所連的 `download-r2.pytorch.org` 在本機曾回傳 403，因此上述命令直接使用可讀取的 `download.pytorch.org` 官方檔案。首次安裝估計下載 3–5 GB，請保留約 15 GB 磁碟；實際時間依網速而定。本次安裝的批准上限是 6 GB／20 分鐘。

## 準備與執行

1. 將來源與使用條件已確認的 Real-ESRGAN Compact RGB SR `.pth` 權重放在專案的 `models/model.pth`。程式不會下載模型；實際 descriptor 的 scale／channels 與 checkpoint 身分仍需驗收。
2. 將一張小圖片放在 `input/` 第一層，接受 `.jpg`、`.jpeg`、`.png`、`.tif`、`.tiff`（大小寫皆可）。
3. 在專案根目錄、啟用環境後執行：

```bash
python -m drone_sr
```

例如 `input/DJI_001.JPG` 對應 `output/DJI_001.png`。輸出不存在會建立；成功 PNG 完整寫入後才替換同名舊結果。來源與其 symlink／hard link 不可被當作輸出覆寫。預設資料夾相對於目前工作目錄，模型仍固定於原始專案內。

啟動時自動選擇可用 CUDA，否則使用 CPU，並顯示 `Device`；CUDA 執行失敗會報錯，不會暗中改成 CPU 重跑大圖。尚無分塊，請不要直接交付大圖或整個資料集。多頁 TIFF、高位深與浮點圖片會明確拒絕；普通圖片轉成 RGB，不保存 alpha、GIS 或其他 metadata。

缺輸入／缺模型／模型載入失敗會報錯；空輸入顯示 `No supported images found in input/`。單張成功或失敗均有對應檔名與 `Processed`／`Failed` 摘要。

## 驗證紀錄

執行中：環境安裝與 runtime checks 尚未完成。本節將依實際結果更新；目前只完成 Python 語法檢查。

準備中的 focused checks：

```bash
python -m unittest discover -s tests -p 'test_image_io.py' -v
python -m unittest discover -s tests -p 'test_inference.py' -v
```

測試中的合成像素、未訓練小模型與 mock 用來驗證程式契約，**不證明真實 SR 品質或預訓練 checkpoint 相容性**。執行狀態與完整觀察證據以 [build/build-log.md](build/build-log.md) 為準；所有階段的完成條件見 [build/GOALS.md](build/GOALS.md)。
