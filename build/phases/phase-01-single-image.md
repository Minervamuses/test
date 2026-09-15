# Phase 01 — 最小單張 Spandrel 推論

## 目標與來源

一張真實本機圖片經 Real-ESRGAN Compact checkpoint 與 Spandrel，產生可開啟且尺寸正確的 PNG。

依據 [GOALS.md](../GOALS.md)、[PLANS.md](../PLANS.md) 及根目錄 AGENTS.md。不以大量骨架檔案代替推論證據。

## 範圍與非目標

包含最少 packaging、模型載入、RGB tensor 轉換、單張 inference、PNG 與小測試。先用 input/ 的一張圖；完整批次 args／日誌交給 phase-02。

本階段不做 SwinIR 驗收、tiling、效能優化或額外 backend；沿用全局非目標。

## 依賴與前置未知

- 無前置階段。重查 WSL/Linux、root、使用者檔案及 PLANS.md 基線。
- 使用者稍後提供真實圖片、權重。缺材料可做不依賴它的準備，但本階段不能 Complete。
- 核對 Python／PyTorch wheel、GPU 架構及 driver 相容，不能只看 nvidia-smi。
- 依 PLANS.md 先完成具體依賴版本／安裝成本提案，已有授權才安裝。不改用 Windows 工具。
- 核對 checkpoint 確為 Compact RGB SR、來源／使用條件及 descriptor channels／scale，不只靠檔名。

## 預期影響元件與授權

可能新增 pyproject.toml、README.md 基本準備段落、.gitignore、input/.gitkeep、output/.gitkeep、src/drone_sr/__init__.py、__main__.py、model.py、image_io.py、inference.py，以及 tests/test_image_io.py、tests/test_inference.py。不要求尚無職責的檔案。

models/model.pth 是使用者提供並由開發者準備的本機資產；權重、真實圖、.venv、產出不加入版控，也不初始化 Git。授權與停止條件見 PLANS.md。

## 實作與驗證

1. **唯讀 preflight：** 重查 nvidia-smi、free -h、df -h，讀官方 PyTorch／Spandrel 版本需求並提出最小清單。真實圖太大先用小裁切副本，保留來源。
2. **最小測試：** test_image_io.py 用已知像素測 RGB 通道、[0,1]、BCHW、clamp、PNG round trip；test_inference.py 測 descriptor 輸出尺寸及錯誤。用 unittest，不引入框架。
3. **最小實作：** 固定載入 models/model.pth，ModelLoader 取得適用 image descriptor，eval 模式下呼叫 descriptor(tensor)。初版明確 float32，不掃 precision。
4. **尺寸責任：** 優先用所裝 descriptor 的 size requirements／padding／裁回；實測後才決定是否需最小共用補充。不呼叫裸 model 繞過 descriptor，禁止 architecture 分支。
5. **真實驗證：** 用一張真實小圖執行 python -m drone_sr。開啟原圖與 PNG 確認內容／色彩、可解碼、寬高各乘 scale，原圖雜湊不變。不做畫質分數。
6. **負向驗證：** 缺 checkpoint／不可載入 checkpoint 在輸出前清楚報錯並停止，不自動下載或換 backend。

### 預定檢查命令

目前無測試檔；以下在工具鏈與檔案建立後採用，按 PLANS.md 記錄實際命令：

~~~bash
python -m unittest discover -s tests -p 'test_image_io.py' -v
python -m unittest discover -s tests -p 'test_inference.py' -v
python -m drone_sr
~~~

前兩項是便宜軟體檢查；第三項須有真實單張 input 與 checkpoint。缺材料記 unavailable，不以合成圖代替真實驗收。下載／安裝／GPU 推論依已批准清單與資源預算進行。

## 驗收條件

- 真實單張 Compact PNG 已開啟，內容與尺寸正常，來源不變。
- Spandrel descriptor 載入並推論，無架構專屬流程。
- I/O、尺寸、載入失敗的最小測試通過，真實與 mock 證據分開。
- 實際環境、checkpoint、命令及耗時可追溯；缺材料或框架不相容不能標完成。

## 證據與交接

於 ../build-log.md 記版本、命令、檔案／雜湊、尺寸、裝置、結果／失敗。若 descriptor 或版本資訊影響下游，才建立 ../context/phase-01-context.md。

必要驗證通過才交接 phase-02；失敗維持 In progress 或 Blocked，按 PLANS.md 處理。後續只依已確認載入／I/O 邊界推進。
