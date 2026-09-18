# evaluation — Build Log

本檔是執行狀態與觀察證據的唯一來源。計劃文件描述打算做的事，本檔只記錄實際發生的事。

## 階段摘要

| 階段 | 狀態 | 開始 | 完成 | 證據 | 阻塞 |
|---|---|---|---|---|---|
| 01 — 固定退化契約與 bicubic 基線 | Complete | 2026-09-19 | 2026-09-19 | 24 項檢查通過；真實樣本尺寸鏈 4056×3040 → 1014×760 → 4056×3040；bicubic 與獨立重算逐位元相同 | 無 |
| 02 — 度量模組與 lpips 依賴 | Complete | 2026-09-19 | 2026-09-19 | 52 項檢查通過；PSNR 48.1308 dB 對上手算；SSIM 與 naive 參考差 ≤1.3e-15；LPIPS 同圖 0.0 | 無（兩項 GPU 量測列入「待 GPU 補測」） |
| 03 — SR 線接上未修改的 pipeline | Complete | 2026-09-19 | 2026-09-19 | 60 項檢查通過；真實樣本 SR 輸出 4056×3040 等同真值；drone_sr 五個檔雜湊未變 | 無（一項 GPU 量測列入「待 GPU 補測」） |
| 04 — 執行器、run 目錄與逐張＋平均報告 | Complete | 2026-09-19 | 2026-09-19 | 94 項檢查通過；3 張真實樣本 report.md 完整；連跑兩次舊 run 逐位元未變 | 無 |
| 05 — 真實小樣本驗收、成本量測與文件對齊 | Not started | — | — | — | 無 |

狀態只用：`Not started`、`In progress`、`Blocked`、`Complete`。

只有在該階段的驗收與必要驗證都有觀察證據時，才標 `Complete`。

## 證據規則

- 記錄確切的命令或人工程序，以及簡潔的通過／失敗結果。
- 區分「實際觀察到」與「引用、歷史或計劃中」的證據。
- 略過或不可執行的檢查要記下來並寫明原因。**略過的檢查不是通過的檢查。**
- 大量輸出用路徑連結，不要整段貼進來。
- **每筆活動記錄要寫下對應的 commit hash**（見 `PLANS.md`「版本控制節奏與可追溯性」），讓文字證據能對回程式狀態。
- 不記 credentials、祕密、完整 diff 或例行敘述。
- 證據互相矛盾時，兩筆觀察都保留，該階段維持 `Blocked` 直到解決。

本計劃特別要求記入的證據：

- 每次真實執行的 run 目錄路徑、納入張數、排除張數與原因。
- 兩條線對等性的直接證據（bicubic 可從 LR 檔獨立重算、兩線輸入為同一檔案）。
- 執行前後 `src/drone_sr/`、`tests/`、`input/`、`output/`、`models/`、`pyproject.toml`、`requirements-wsl.txt` 的未變動確認方式與結果。
- 實測的單張耗時、峰值記憶體與所用 device，以及據此推估的全量成本。
- LPIPS 權重的來源 URL、檔案大小與 SHA-256。

## 待 GPU 補測

交付裝置是 GPU，但 coding agent 的沙箱 session 看不到它。依 `PLANS.md`「GPU 交接協定」，需要 GPU 的項目集中在此，**不標 `Blocked`**。清單清空前，計劃不得標為整體完成。

| # | 來源階段 | 要量什麼 | 沙箱內為何做不到 | 對應驗收條件 | 狀態 |
|---|---|---|---|---|---|
| 1 | 02 | LPIPS 對一張 4056×3040 真值與其 bicubic 版本的耗時、峰值 RSS、**峰值 VRAM**、device 名稱 | 沙箱 session 看不到 GPU（`/dev/dxg` 不存在、`torch.cuda.is_available()` 為 `False`），量到的是 CPU 數字 | phase-02「真實尺寸的 LPIPS 耗時、峰值 RSS 與峰值 VRAM 已在交付裝置上實測並記錄」 | 待補 |
| 2 | 02 | 同一組輸入連跑兩次，LPIPS 在 **GPU 上**數值完全相同，且 `torch.backends.cudnn.benchmark` 為 `False` | 同上。CPU 的決定性結果不能代表 GPU 路徑（TF32、cuDNN 演算法選擇） | phase-02「同一決定性檢查已在 GPU 上通過且設了 `cudnn.benchmark = False`」 | 待補 |
| 3 | 03 | SR 線在 GPU 上的單張端到端耗時、峰值 RSS、**峰值 VRAM**、device 名稱（LR 1014×760 → SR 4056×3040） | 沙箱 session 看不到 GPU，量到的是 CPU 數字 | phase-03「交付裝置（GPU）上的單張耗時、峰值 RSS 與峰值 VRAM 已量測」 | 待補 |

狀態只用：`待補`、`已補（使用者 shell）`。已補的項目要在「活動紀錄」有對應的一筆，寫明確切命令、輸出與量測環境。

## 活動紀錄

尚無實作活動。計劃 bundle 已撰寫完成，但其中所有預定檢查都**尚未**以實作證據執行過。

## 2026-09-19 — 計劃修訂：交付裝置是 GPU，沙箱 session 看不到它

- **狀態：** 五個階段仍為 `Not started`。本次為純計劃修訂，沒有任何實作。
- **授權範圍：** `PLANS.md`「計劃維護與失敗處理」、`PROMPTS.md`「依相反證據修正計劃」。使用者於 2026-09-19 指出本機有 GPU 並要求修正計劃。
- **被推翻的理解：** 2026-09-18 記錄的 `torch.cuda.is_available() = False` 被當成本機狀態，實際上只是 coding agent 沙箱 session 的狀態。
- **驗證（實際觀察）：**
  - 使用者的一般 WSL shell：`.venv/bin/python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"` → `True NVIDIA GeForce RTX 5070 Ti Laptop GPU`。
  - 同日沙箱 session 內：`nvidia-smi` → `Failed to initialize NVML: GPU access blocked by the operating system`；`/dev/dxg` 不存在；`torch.cuda.device_count()` → `0`；`torch.version.cuda` → `12.8`（wheel 本身帶 CUDA，缺的是裝置存取）。
  - 對照 `README.md:121`–`123`：本機先前已在 `cuda:0` 上跑完整 4K 批次，GPU 路徑本身可用。
- **計劃變更：**
  - `GOALS.md`「授權限制」：改寫 GPU 那條，記入兩個環境的實測差異，並要求所有交付數字在使用者 shell 量測。
  - `GOALS.md`「固定的度量約定」：新增第 6 條「執行裝置與決定性」——單次執行裝置固定、GPU 須設 `cudnn.benchmark = False`、決定性檢查在實際裝置上做、跨裝置數字不可並列比較。
  - `GOALS.md`「未解問題」：LPIPS 的瓶頸由 CPU 耗時改為 12227 MiB VRAM。
  - `PLANS.md`「已確認基線 / 資源」：記入裝置可見性修正、GPU 對照數字（`README.md:122` 的 0.220 秒），成本估算改為分裝置兩套。
  - `phases/phase-02`：LPIPS 裝置政策、決定性檢查須在實際裝置上通過、資源實測須在使用者 shell、新增兩項驗收條件。
  - `phases/phase-03`：cuda 可用性由 `Unresolved` 改為已解（GPU），量測須在使用者 shell，新增峰值 VRAM 與量測環境註明的驗收條件。
  - `phases/phase-04`：樣本上限預設值須綁在實測裝置上，報告標頭新增執行裝置與跨批次可比性欄位。
- **未變更：** 退化契約、PSNR／SSIM／LPIPS 的定義、階段順序與依賴、非目標、`AGENTS.md`。
- **限制：** 本次修訂**沒有任何 GPU 上的實測數字**。GPU 路徑的耗時、峰值 VRAM 與決定性全部仍未驗證，由 phase-02／03 在使用者 shell 補上。修訂中引用的 GPU 數字全部來自 `README.md` 既有紀錄，不是本計劃的觀察。
- **阻塞：** 無。但若實作在沙箱 session 內進行，真實資料的執行與量測必須交由使用者的 shell，否則 phase-02／03／05 的資源與裝置驗收取不到證據。
- **下一步：** 提交未提交的計劃 bundle 與 `.gitignore`（見 `PLANS.md`「尚未提交的既有工作」），然後開始 phase-01（不需 GPU，沙箱內可完整執行）。
- **證據位置：** 本筆記錄。本次修訂的內容隨計劃 bundle 一併提交於 `7b995b8`（`.gitignore` 為 `4b87282`）。

## 2026-09-19 — 計劃修訂：採用批次 GPU 交接，需 GPU 的項目不再標 Blocked

- **狀態：** 五個階段仍為 `Not started`。純計劃修訂，沒有實作。
- **授權範圍：** 使用者於 2026-09-19 在兩個選項中選定「批次交接」（選項 B），取代原先「每個需要 GPU 的階段各自 `Blocked` 並停下」的行為。
- **要解決的問題：** 修訂前的寫法會讓 phase-02 因為「LPIPS 全尺寸資源實測必須在交付裝置上」這項驗收缺證據而標 `Blocked`，phase-04 依賴 02 因此不能開始，整個計劃停在那裡；而交接怎麼做（給哪個命令、輸出貼到哪、誰寫進 build-log）當時完全沒有規定。
- **計劃變更：**
  - `PLANS.md`：新增「GPU 交接協定」一節（分工原則、待 GPU 補測清單、五步交接程序、腳本的驗證責任）。
  - `PLANS.md`「停止並取得所需授權」：在「缺必要證據記 `Blocked`」那條加上唯一例外——協定列出的三類 GPU 項目推遲到清單，不標 `Blocked`；正確性檢查不適用此例外。
  - `PLANS.md`「整體完成標準」：新增一條，清單清空才算完成。
  - `build-log.md`：新增「待 GPU 補測」區塊與其狀態詞彙。
  - `PROMPTS.md`：啟動提示的必讀界線新增一條指向本協定；最終整合審查新增檢查清單是否清空。
  - `phases/phase-02`、`phases/phase-03`：新增「GPU 項目的處理」，說明哪些推遲、哪些沙箱內必須做完才可標 `Complete`；受影響的驗收條件標上「可推遲」。
  - `phases/phase-05`：新增產生、煙霧測試與回收交接腳本的範圍與驗收條件。
- **未變更：** 退化契約、度量定義（含第 6 條裝置與決定性）、階段順序與依賴、非目標、`AGENTS.md`。
- **限制：** 協定本身尚未被執行過一次，交接腳本還不存在。清單目前是空的，因為還沒有階段開始。
- **阻塞：** 無。
- **下一步：** 提交計劃 bundle 與 `.gitignore`，然後開始 phase-01（不需 GPU，沙箱內可完整執行）。
- **證據位置：** 本筆記錄。本次修訂的內容隨計劃 bundle 一併提交於 `7b995b8`。

## 2026-09-19 01:09 (CST) — Phase 01: preflight

- **狀態：** `Not started` → `In progress`
- **授權範圍：** [phases/phase-01-degradation-and-bicubic.md](phases/phase-01-degradation-and-bicubic.md)「實作與驗證計劃 / Preflight」。
- **本階段範圍（複述）：** 原圖探索（`input/` 直接子項的 png／jpg／jpeg，忽略子資料夾與其他副檔名）、原圖解碼（`Image.open` → 第一影格 → `exif_transpose` → `convert("RGB")`、>8-bit 略過）、mod-crop 到 4 的倍數、`BICUBIC` 降採樣成 LR PNG、**從磁碟上的 LR PNG** `BICUBIC` 放大回真值尺寸、建立一個新的 run 目錄。
- **非目標（複述）：** 不做 SR、不算度量、不裝依賴、不做報告與平均、不做 run 目錄防覆蓋規則、不動 `src/drone_sr/**`。
- **停止條件（複述）：** 若尺寸對齊必須靠第二次縮放，停止回報；若需修改 `src/drone_sr/**`，停止回報。
- **驗證（實際觀察）：**
  - `.venv/bin/python -c "import sys, PIL, torch, numpy; ..."` → Python `3.12.3`、Pillow `12.3.0`、torch `2.11.0+cu128`、numpy `2.5.3`、`torch.cuda.is_available()` → `False`。**量測環境：沙箱 session**；依 `GOALS.md`「授權限制」，`False` 是沙箱狀態，不是本機能力。本階段不需要 GPU。
  - `input/` 直接子項 744 個、無子資料夾（`find input -mindepth 1 -maxdepth 1 -type d | wc -l` → `0`）；副檔名分佈 `738 jpg`、`4 json`、`2 txt`、**0 png**。與 `PLANS.md`「已確認基線」一致。
  - `output/` 現況：`.gitkeep` 與 `whaledrone_seek10s_x1536_y768_512.png`（既有 SR 產物，不得更動）。
  - 基線雜湊清單（761 筆，涵蓋 `input/`、`output/`、`models/`、`src/**.py`、`tests/**.py`、`pyproject.toml`、`requirements-wsl.txt`）已存於 `$TMPDIR/baseline/manifest-before.txt`，供本階段結束時比對。
  - `git status --short` → 僅十二個沙箱裝置檔（`.bashrc`、`.claude/`、`.mcp.json` 等），與 `PLANS.md`「計劃 bundle 的提交狀態」記載一致，**不清理、不提交**。`HEAD` = `507f2a9`，分支 `main`。
  - `drone_sr` 以 editable 安裝於 `.venv`（`__editable__.drone_sr-0.1.0.pth`），任意工作目錄皆可 import，評估工具不需要調整 `sys.path`。
- **preflight 的實質發現（真實 MPO 的影格順序）：** 對 `input/DJI_20230127115759_0001_W.JPG` 實測 `n_frames = 2`，**frame 0 為 4056×3040 主圖、frame 1 為 960×720 縮圖**。因此 `GOALS.md` 退化契約第 1 條的「取第一影格」在這批資料上取到的是全解析度主圖，契約可照字面執行，不需要 `context/phase-01-context.md` 的例外處理。
- **解決 Unresolved（測試命令）：** 採用 `.venv/bin/python -m unittest discover -s evaluation`。已實測 unittest discovery 不會遞迴進入非 package 的子目錄（`$TMPDIR/dprobe` 探測：`sub/test_nested.py` 未被收集），因此 `evaluation/runs/`、`evaluation/phases/` 不會被掃到。評估檢查一律放在 `evaluation/` 之下，**不進入專案既有的 `tests/`**，也不用 `tests/` 的既有命令去掃評估程式。
- **Unresolved（維持）：** `input/` 仍為 0 張 PNG，PNG 原圖路徑只能以合成 fixture 驗證；結束時須記明「PNG 原圖僅以合成 fixture 驗證，尚未在真實 PNG 資料上執行」。
- **限制：** 本筆為唯讀 preflight，尚無任何實作或評估產物。
- **阻塞：** 無。
- **下一步：** 依 phase-01「Commit 切點」先提交定義驗收的檢查（red），再分四顆實作。
- **證據位置：** 本筆記錄。觀察時的 `HEAD` = `507f2a9`。本筆隨 `docs: start phase 01` 提交，該顆與本階段其餘 commit 的 hash 於 close 記錄一併列出（沿用 `507f2a9` 的既有做法，不用 `--amend` 回填）。

## 2026-09-19 01:15 (CST) — Phase 01: close

- **狀態：** `In progress` → `Complete`
- **授權範圍：** [phases/phase-01-degradation-and-bicubic.md](phases/phase-01-degradation-and-bicubic.md)。
- **變更：** 新增四個模組與四個檢查模組於 `evaluation/`：`sources.py`（探索與解碼）、`degradation.py`（mod-crop、降採樣、PNG 寫出）、`bicubic.py`（從磁碟 LR PNG 放大）、`runs.py`（建立 run 目錄）。未動 `src/drone_sr/**`、`tests/**` 或任何受保護路徑。
- **驗證（聚焦，實際觀察）：**
  - `.venv/bin/python -m unittest discover -s evaluation` → **`Ran 24 tests` `OK`**。
  - `.venv/bin/python -W error::DeprecationWarning -m unittest discover -s evaluation` → **`Ran 24 tests` `OK`**（refactor 前為 `FAILED (errors=5)`，肇因於 Pillow 12 已棄用的 `Image.getdata`）。
  - `.venv/bin/python -m unittest discover -s tests` → **`Ran 33 tests` `OK`**，每一顆 commit 後皆重跑並通過。
- **驗證（較廣，真實資料，實際觀察）：** run 目錄 `evaluation/runs/20260918T171502Z/`（UTC 命名；當地時間 2026-09-19 01:15 CST），取 `input/` 前兩張。
  - `DJI_20230127115759_0001_W.JPG`：原始 `(4056, 3040)` → 裁切後 `(4056, 3040)`、裁掉 `(0, 0)` → LR `(1014, 760)` → bicubic `(4056, 3040)`。
  - `DJI_20230127115802_0002_W.JPG`：同上尺寸鏈。
  - **兩條線對等性的直接證據：** 兩張的 bicubic PNG 與「另外獨立 `Image.open(lr.png).convert("RGB").resize(cropped_size, BICUBIC)`」逐位元相同（`tobytes()` 相等）→ `True`。
  - 六個中間檔的檔頭皆為 `89504e470d0a1a0a`（PNG magic），逐檔列出，無一例外。
  - 端到端（解碼→裁切→降採樣→寫 LR→從 LR 放大→寫 bicubic）每張 **5.10 秒 / 4.24 秒**。**量測環境：沙箱 session、CPU。** 這是退化與 bicubic 線的診斷數字，不是交付用的資源量測；可對外引用的單張成本由 phase-03／05 在使用者 shell 量。bicubic 線依 `GOALS.md`「固定的度量約定」第 6 條恆為 Pillow CPU 實作。
- **驗證（不變式，實際觀察）：** 761 筆雜湊清單（`input/`、`output/`、`models/`、`src/**.py`、`tests/**.py`、`pyproject.toml`、`requirements-wsl.txt`）執行前後 `diff` **完全相同**。`git status --short` 仍只列十二個沙箱裝置檔，與 preflight 一致。`git check-ignore -v evaluation/runs/20260918T171502Z/report.md` → 命中 `.gitignore:15`，run 產物不進版本控制。
- **驗收條件對照：** 八項全部由上述觀察滿足——尺寸往返（含 203×101 非 4 倍數案例：裁切成 200×100、LR 50×25、bicubic 200×100）、覆寫 LR 檔使 bicubic 輸出改變、獨立重算逐位元相同、探索規則、MPO 可解碼與 16-bit 明確拒絕、真實 4056×3040 尺寸鏈、PNG magic、受保護路徑未變動。
- **限制：**
  - **PNG 原圖僅以合成 fixture 驗證，尚未在真實 PNG 資料上執行。** `input/` 仍為 0 張 PNG。
  - 16-bit 拒絕只實作並驗證 PNG 的 IHDR 位深；探索只收 png／jpg／jpeg，Pillow 的 JPEG 解碼為 8-bit，因此目前沒有其他能抵達此檢查的深色深來源。
  - 兩張來源檔名 stem 相同時（例如同時存在 `a.png` 與 `a.JPG`）會寫到同一個輸出路徑。目前 `input/` 738 張檔名皆唯一，未觸發；phase-04 的執行器需決定是要視為單張失敗排除還是中止。
  - 上述耗時為沙箱 CPU 數字，非交付環境。
- **阻塞：** 無。本階段不需要 GPU，未產生「待 GPU 補測」項目。
- **下一步：** phase-02（度量模組與 `lpips` 依賴）。它與 01 互相獨立，依賴皆已滿足。
- **證據位置：** 本筆記錄；run 目錄 `evaluation/runs/20260918T171502Z/`（未進版本控制）。本階段 commit 依序為 `05d3c9f`（`docs:` start）、`b48088a`（`test:` red，24 項、4 個 import 錯誤）、`ea72bc8`（`feat:` sources）、`8d9f910`（`feat:` degradation）、`1b7ac51`（`feat:` bicubic，本階段核心）、`e7f030a`（`feat:` runs）、`b61477b`（`refactor:` 移除已棄用 API），close 記錄本身另成一顆。

## 2026-09-19 01:22 (CST) — Phase 02: preflight

- **狀態：** `Not started` → `In progress`
- **授權範圍：** [phases/phase-02-metrics-and-lpips.md](phases/phase-02-metrics-and-lpips.md)「實作與驗證計劃 / Preflight」。
- **本階段範圍（複述）：** 以 torch 自行實作 PSNR 與 SSIM、安裝 `lpips` 並包成穩定介面、建立 `evaluation/requirements.txt`、六組性質檢查、真實尺寸 LPIPS 資源實測（可推遲至 GPU 清單）。
- **非目標（複述）：** 不做退化／SR／報告；不裝 `lpips` 以外的套件；不動 `pyproject.toml` 與 `requirements-wsl.txt`；不加 Y 通道或 MS-SSIM。
- **停止條件（複述）：** 網路取不到套件或權重；`lpips` 需要與現有 torch 衝突的相依；需要第二個新套件；LPIPS 在真實尺寸 OOM 或單張數分鐘。**不得**改用縮圖後再算 LPIPS。
- **驗證（實際觀察）：**
  - `.venv/bin/python -c "import lpips"` → `ModuleNotFoundError`。確認目前確實沒有。
  - 安裝前版本：`torch 2.11.0+cu128`、`torchvision 0.26.0+cu128`、`pillow 12.3.0`、`spandrel 0.4.2`、`numpy 2.5.3`。完整 `pip list --format=freeze`（37 筆）存於 `$TMPDIR/baseline/pip-before.txt`。
  - `scipy`、`tqdm`、`skimage` 皆 **MISSING**。
  - 網路可用：`curl https://pypi.org/simple/lpips/` → `http=200`（0.94 秒）。
  - **`pip install --dry-run --report - lpips` 在 180 秒後被 `timeout` 殺掉（exit 143），全程無輸出。** 未進一步重試；改以 PyPI JSON API 與 wheel 內容做唯讀確認，成本遠低於讓 pip 解析含 torch 的相依樹。
- **preflight 的實質發現一（`lpips` 的相依）：** PyPI metadata（`https://pypi.org/pypi/lpips/json`）顯示 `lpips 0.1.4` 的 `requires_dist` 為 `torch>=0.4.0`、`torchvision>=0.2.1`、`numpy>=1.14.3`、**`scipy>=1.0.1`**、**`tqdm>=4.28.1`**。前三者已滿足且版本遠高於下限，**安裝不會動到既有 torch／torchvision**；後兩者是 venv 內尚不存在的套件。
  - 檢查 wheel 原始碼確認這不是可繞過的軟相依：`lpips/__init__.py:10` 為模組層級的 `from lpips.trainer import *`，而 `lpips/trainer.py` 在模組層級 `from scipy.ndimage import zoom` 與 `from tqdm import tqdm`。因此 **`import lpips` 硬性需要 scipy 與 tqdm**。
  - `skimage`、`rawpy`、`cv2` 的 import 全部位於函式內（`__init__.py` 第 24、28、44、57、76、80、88 行皆有縮排），不影響 import。
  - **這觸及 `PLANS.md`「停止並取得所需授權」的「需要 `lpips` 以外的任何新依賴」。** 依該條停止並向使用者確認，不自行安裝。詳見下一筆記錄。
- **preflight 的實質發現二（LPIPS 權重的來源分兩處）：** `lpips-0.1.4-py3-none-any.whl`（53763 bytes、SHA-256 `fd537af5828b69d2e6ffc0a397bd506dbc28ca183543617690844c08e102ec5e`、BSD、`https://github.com/richzhang/PerceptualSimilarity`）**本身就內含線性層權重** `lpips/weights/v0.1/alex.pth`（6009 bytes）。因此需要另外下載的只有 torchvision 的 AlexNet backbone 權重。這使「權重取不到」的風險小於計劃撰寫時的預期。
- **限制：** 本筆為唯讀 preflight 與網路唯讀查詢，尚未安裝任何套件，`.venv` 未變動。AlexNet backbone 權重尚未下載，其 URL／大小／SHA-256 尚未記錄。
- **阻塞：** `lpips` 的安裝等待使用者對 scipy 與 tqdm 的決定。PSNR 與 SSIM 不依賴此決定，先行實作。
- **下一步：** 先完成 PSNR 與 SSIM 及其性質檢查（不依賴該決策），再就 scipy／tqdm 取得授權。
- **證據位置：** 本筆記錄；`$TMPDIR/baseline/pip-before.txt`。commit 見本階段 close 記錄的清單。

## 2026-09-19 02:00 (CST) — Phase 02: close

- **狀態：** `In progress` → `Complete`
- **授權範圍：** [phases/phase-02-metrics-and-lpips.md](phases/phase-02-metrics-and-lpips.md)，加上使用者於 2026-09-19 對 `scipy` 與 `tqdm` 的新授權（見下）。
- **使用者決定（新增授權）：** preflight 發現 `import lpips` 硬性需要 `scipy` 與 `tqdm`，觸及 `PLANS.md`「需要 `lpips` 以外的任何新依賴」的停止條件。已停下並詢問，使用者選定**授權 scipy 與 tqdm**，照一般方式 `pip install lpips`。三者釘版於 `evaluation/requirements.txt`，`pyproject.toml` 與 `requirements-wsl.txt` 不動。
- **變更：** 新增 `evaluation/metrics.py`（輸入轉換、PSNR、SSIM）、`evaluation/perceptual.py`（LPIPS 包裝）、`evaluation/requirements.txt`、`evaluation/gpu_checks/probe_lpips_full_size.sh`，以及四個檢查模組。未動任何受保護路徑。
- **驗證（聚焦，實際觀察）：** `TORCH_HOME=$TMPDIR/torch-home .venv/bin/python -m unittest discover -s evaluation` → **`Ran 52 tests` `OK`**（phase-01 的 24 項加本階段 28 項）。`.venv/bin/python -m unittest discover -s tests` → **`Ran 33 tests` `OK`**，每一顆 commit 後皆重跑並通過。
  - **沙箱注意事項：** 沙箱 session 的 `~/.cache/torch` 唯讀（`OSError: [Errno 30] Read-only file system`），需以 `TORCH_HOME` 指向可寫目錄；**使用者的一般 shell 不需要這個變數**。
- **六組性質檢查的實測數值（量測環境：沙箱 session、CPU）：**
  1. **同圖對自己：** PSNR `inf`；SSIM `1.0`（random 與 smooth 兩種輸入皆是）；LPIPS **`0.0`**（精確為 0，優於契約要求的 ≤1e-4）。
  2. **PSNR 手算對照：** 整張差 1 個位階 → `48.1308036086791` dB，與 `10*log10(255**2/1)` 的 `48.1308036086791` 每一位數字相同。
  3. **單調性：** PSNR 隨雜訊 1／2／4／8／16 為 `48.1826`／`42.1857`／`36.2214`／`30.2791`／`24.4198` dB（嚴格遞減）；SSIM 為 `0.991229`／`0.965856`／`0.876569`／`0.642243`／`0.313337`（嚴格遞減）；LPIPS 隨雜訊 2／6／18／54 為 `0.001369`／`0.021212`／`0.152412`／`0.636391`（嚴格遞增，方向正確：LPIPS 越低越像）。
  4. **值域：** SSIM 於 smooth 對反相為 `0.052895`、smooth 對 random 為 `0.010471`、random 對 random 為 **`-0.060878`**（落在 `[-1,1]`，且確認 SSIM 確實可為負，值域不是 `[0,1]`）。LPIPS 對真實 bicubic 4× 往返為 `0.118213`（160×128 合成圖）與 **`0.543673`**（真實 4056×3040 影像），皆嚴格落在 `(0,1)`。
  5. **決定性：** 三個度量連跑兩次數值完全相同（`==` 比較為 `True`），`torch.backends.cudnn.benchmark` 讀回 `False`。**此為 CPU 上的結果；GPU 上的同一檢查列入「待 GPU 補測」第 2 項。**
  6. **對稱性與尺寸檢查：** PSNR／SSIM／LPIPS 交換輸入後數值完全相同；尺寸不同一律拋 `ValueError` 並在訊息中列出兩個 shape，不靜默縮放；非 RGB BCHW 輸入亦拒絕。
- **SSIM 交叉核對（已做，但不是第三方實作）：** `scikit-image` 與 `torchmetrics` 不在授權內，因此改以**刻意寫慢的獨立重新推導**核對——明確走訪每個 11×11 視窗（不用 conv2d），並直接由各向同性二維高斯公式建窗（不是一維正規化後外積）。三組輸入的差距：random 對 random `4.163e-17`、smooth 對 smooth+12 `1.332e-15`、完全相同 `0`。**這涵蓋 `GOALS.md` 點名的失效模式（window 正規化、邊界處理、通道平均），但它不是第三方實作**，只能證明快速路徑算的是預期的定義，不能證明該定義與其他工具一致。**此限制必須寫進最終報告。**
- **兩個 SSIM 自由度已釘死並須寫進報告標頭：** 邊界處理為 `valid`（不補邊，SSIM map 為 `(H-10)×(W-10)`，沒有任何值由虛構像素算出）；變異數採 Wang et al. 的高斯加權**有偏**估計，不是 `scikit-image` 的樣本共變異修正。累加一律 float64。
- **依賴隔離（實際觀察）：** `pip list --format=freeze` 安裝前後 `diff` 僅三行新增：`lpips==0.1.4`、`scipy==1.18.1`、`tqdm==4.70.1`，無任何移除或版本變動。安裝後讀回 `torch 2.11.0+cu128`、`torchvision 0.26.0+cu128`、`Pillow 12.3.0`、`spandrel 0.4.2`、`numpy 2.5.3`，全部與安裝前相同。`pip check` → `No broken requirements found`。
- **LPIPS 權重（兩處來源）：**
  - 線性層：**隨 wheel 附帶**，`lpips/weights/v0.1/alex.pth`，**6009 bytes**，SHA-256 `df73285e35b22355a2df87cdb6b70b343713b667eddbda73e1977e0c860835c0`。wheel 本身 53763 bytes、SHA-256 `fd537af5828b69d2e6ffc0a397bd506dbc28ca183543617690844c08e102ec5e`、BSD、`https://github.com/richzhang/PerceptualSimilarity`。
  - AlexNet backbone：由 torchvision 下載，`https://download.pytorch.org/models/alexnet-owt-7be5be79.pth`，**244408911 bytes**，SHA-256 `7be5be791159472b1fbf3c69796f7cb30dca7ad8466c2df70058c37116cdee02`（torchvision 以 `check_hash` 自行驗證）。
  - `lpips.LPIPS(net='alex')` 在 torchvision 0.26 下可載入：`tv.alexnet(pretrained=True)` 的舊介面仍能解析，只發出 deprecation warning。
- **交接腳本（協定第 1 步，已完成）：** `evaluation/gpu_checks/probe_lpips_full_size.sh`。**已依「腳本的驗證責任」在沙箱內以 CPU 煙霧測試過**：exit 0，正確辨識並標示「CPU <-- not the delivery device」、VRAM 顯示 `n/a`。該次輸出：`DJI_20230127115759_0001_W.JPG`、真值 4056×3040、張量 `(1, 3, 3040, 4056)`、LPIPS `0.543673`、**耗時 4.74 秒、峰值 RSS 4325 MiB**。
  - **推翻了計劃的一項預期：** `GOALS.md`「未解問題」推測 LPIPS 在全尺寸上可能成為比 SR 推論更大的瓶頸。**CPU 上 4.74 秒**顯示耗時不是瓶頸。剩下的未知只有 VRAM 是否放得下 12227 MiB，由使用者的探測回答。此發現不改變任何固定約定，也不改變後續階段的設計，因此未建立 `context/phase-02-context.md`。
- **不變式（實際觀察）：** 761 筆雜湊清單執行前後 `diff` 完全相同。`git status --short` 除原有十二個沙箱裝置檔外，新增 `evaluation/.claude/`、`evaluation/gpu_checks/.claude/`（以及短暫出現的 `.mcp.json`），**與前十二個同類**，是 harness 隨工作目錄變動產生的沙箱 session 檔，**不清理、不提交**。
- **限制：**
  - 上列所有數值皆為**沙箱 session、CPU** 的觀察，不是交付環境的數字。
  - SSIM 沒有第三方交叉核對（見上）。
  - GPU 上的決定性與全尺寸資源量測尚未取得，列入「待 GPU 補測」第 1、2 項。
  - LPIPS 只驗證 `net='alex'`，未驗證其他 backbone（也不在範圍內）。
- **阻塞：** 無。依 `PLANS.md`「GPU 交接協定」，推遲的兩項都屬於協定列出的三類（GPU 資源數字、GPU 決定性檢查），**沒有任何正確性檢查被推遲**，因此本階段標 `Complete`，phase-04 可以開始。
- **下一步：** phase-03（SR 線接上未修改的 pipeline）。依賴 phase-01，已 `Complete`。同時請使用者在自己的 shell 執行 `bash evaluation/gpu_checks/probe_lpips_full_size.sh` 並貼回輸出。
- **證據位置：** 本筆記錄。本階段 commit 依序為 `1d38c33`（`docs:` start）、`10a0958`（`test:` PSNR／SSIM red）、`4a4424f`（`feat:` PSNR）、`f1b3404`（`feat:` SSIM）、`7daf46f`（`test:` SSIM 交叉核對）、`bfb546d`（`test:` 輸入轉換）、`d2e2107`（`chore:` 釘版 lpips）、`66e7415`（`refactor:` 共用 validate_pair）、`926e025`（`test:` LPIPS red）、`e655679`（`feat:` LPIPS 包裝）、`2b97d40`（`chore:` 探測腳本），close 記錄本身另成一顆。

## 2026-09-19 02:05 (CST) — Phase 03: preflight

- **狀態：** `Not started` → `In progress`
- **授權範圍：** [phases/phase-03-sr-line.md](phases/phase-03-sr-line.md)「實作與驗證計劃 / Preflight」。依賴 phase-01 已 `Complete`。
- **本階段範圍（複述）：** 以 import 重用 `read_image`／`load_model`／`upscale`／`write_png`，斷言 `descriptor.scale == 4`，斷言 SR 輸出尺寸等於真值，模型只載入一次，記錄 device／耗時／峰值 RSS。
- **非目標（複述）：** 不改 `src/drone_sr/**` 任何一行，不複製推論或分塊邏輯，不換模型、不調 tile，不算度量、不做報告。
- **停止條件（複述）：** 需要改 `src/drone_sr/**`；`descriptor.scale != 4`；小樣本預估超過約十分鐘。
- **驗證（實際觀察）：**
  - `models/model.pth` → symlink 指向 `realesr-general-x4v3.pth`（4885111 bytes）。
  - `load_model()` 回傳的 descriptor：architecture **`RealESRGAN Compact`**、**`scale = 4`**、`purpose = SR`、`input_channels = 3`、`output_channels = 3`、`tiling = ModelTiling.SUPPORTED`、`device = cpu`、`dtype = torch.float32`。倍率符合本計劃要求，仍會在實作中斷言。
  - `torch.cuda.is_available()` → **`False`。量測環境：沙箱 session。** 依 `GOALS.md`「授權限制」這是沙箱狀態，不是本機能力；因此本階段在沙箱量到的 device 為 `cpu`，所有耗時與記憶體數字都屬 CPU 批次。
  - `src/drone_sr/*.py` 與 `output/` 的雜湊快照沿用 preflight 階段建立的 761 筆清單（`$TMPDIR/baseline/manifest-before.txt`），結束時比對。
- **限制：** 本筆為唯讀 preflight，尚未寫任何 SR 程式或產物。
- **阻塞：** 無。
- **下一步：** 先寫失敗檢查（倍率斷言、尺寸對齊、輸入來源），再分兩顆實作。
- **證據位置：** 本筆記錄；commit 見本階段 close 記錄的清單。

## 2026-09-19 02:12 (CST) — Phase 03: close

- **狀態：** `In progress` → `Complete`
- **授權範圍：** [phases/phase-03-sr-line.md](phases/phase-03-sr-line.md)。
- **變更：** 新增 `evaluation/sr_line.py` 與 `evaluation/test_sr_line.py`。**沒有任何 commit 修改 `src/drone_sr/**`。**
- **驗證（聚焦，實際觀察）：** `TORCH_HOME=$TMPDIR/torch-home .venv/bin/python -m unittest discover -s evaluation` → **`Ran 60 tests` `OK`**（24 + 28 + 8）。`.venv/bin/python -m unittest discover -s tests` → **`Ran 33 tests` `OK`**。
  - **更正：** commit `fea3911` 的 body 誤記為「61 tests」，實際為 **60**。依 `PLANS.md`「不得用 `--amend` 改寫歷史」，在此以新記錄更正，不改該顆 commit。
- **三項必要檢查（實際觀察）：**
  1. **倍率斷言：** 以 scale 為 2／3／8 的 stub descriptor 取代 `load_model`，三種皆拋 `ValueError`，訊息同時含期望值 `4` 與實際值。不是靜默繼續。
  2. **尺寸對齊：** 合成 LR 50×25 → SR 200×100，與 mod-crop 後真值尺寸相同。另檢查給錯 expected size 時拋錯而非縮放。
  3. **輸入來源：** 覆寫 LR PNG 後重跑，SR 輸出位元組不同 → SR 線讀的是磁碟上的 LR 檔。
- **descriptor（實際觀察）：** `RealESRGAN Compact`、`scale = 4`、`purpose = SR`、`3 → 3`、`tiling = ModelTiling.SUPPORTED`、`device = cpu`、`dtype = torch.float32`。模型只在 `SuperResolutionLine.__init__` 載入一次，逐張重用。
- **驗證（較廣，真實資料）：** run 目錄 `evaluation/runs/20260918T180259Z/`，`input/` 前兩張。
  - 尺寸：hr `(4056, 3040)`、lr `(1014, 760)`、bicubic `(4056, 3040)`、sr `(4056, 3040)`。**SR 輸出尺寸等於真值，未經任何補縮放。**
  - **兩條線輸入同一檔案的直接證據：** `lr/DJI_20230127115759_0001_W.png` 的 SHA-256 為 `8ed6a0920044b58f...`，與 phase-01 run（`20260918T171502Z`）產生的同名檔**完全相同**，顯示退化流程跨 run 可重現；bicubic 線與 SR 線在本次 run 中都只讀這一個檔。
  - 八個中間檔檔頭皆為 `89504e470d0a1a0a`。
  - **目視檢查（實際看過）：** 取 `(1800, 1300, 2120, 1540)` 的 320×240 區域，以 100% 疊成 hr／bicubic／sr 對照圖檢視。SR 輸出是正常照片，**不是噪點、不是全黑、色彩正常**，且明顯比 bicubic 銳利。同時觀察到：SR 的細節是**重建**而非還原——浪花被畫成清晰的斑點，但斑點位置與真值的浪花不吻合，並有輕微色偏（SR 通道均值 `68.12 / 146.59 / 154.43` 對真值的 `67.04 / 145.31 / 151.71`）。通道標準差：真值 `61.17 / 34.84 / 32.99`、bicubic `55.74 / 27.11 / 24.88`、SR `61.26 / 30.54 / 25.72`。
    - **這正是 `GOALS.md`「已知會影響結論解讀的性質」預測的行為**（GAN 模型在乾淨 bicubic 退化上重建紋理），是評估設定的已知性質，不是實作錯誤。它**加強**了「PSNR／SSIM 可能輸給 bicubic、LPIPS 勝出」的預期。未推翻任何計劃假設，因此未建立 `context/phase-03-context.md`。
- **資源（量測環境：沙箱 session、CPU）：** 每張端到端 `16.33` 秒與 `15.96` 秒，拆解為退化 `2.24`／`2.34` 秒、bicubic `2.30`／`2.45` 秒、**SR `11.78`／`11.17` 秒**。整個程序峰值 RSS **1268 MiB**。
  - **對小樣本規模的建議（依 CPU 數字，保守上界）：** 加上 LPIPS 的 4.74 秒與 PSNR／SSIM，單張約 21–22 秒。十分鐘的授權上限對應約 **27 張**；GPU 上會更快。phase-04 的預設樣本上限應據此設定，並在交付裝置上重新量測後調整。
- **不變式（實際觀察）：** 761 筆雜湊清單 `diff` 完全相同；`src/drone_sr/*.py` 五個檔的 SHA-256 與 preflight 逐一相同（`image_io.py` `655b0da5…`、`inference.py` `87a4aada…`、`tiling.py` `faecfa0a…`、`__main__.py` `5da7a2de…`、`__init__.py` `f1d2e09e…`）；`git status --short src tests pyproject.toml requirements-wsl.txt models` **為空**；`output/` 未被寫入。
- **限制：**
  - 所有耗時與記憶體為**沙箱 CPU** 數字，不是交付環境。GPU 上的同一組量測列入「待 GPU 補測」第 3 項。
  - 逐張失敗隔離只做到「`run()` 拋出帶來源檔名的明確錯誤」；**包住它的 try／except 迴圈屬於 phase-04 的執行器**（見本階段文件「交接」：批次執行屬 phase-04）。
  - 目視檢查只看了一張影像的一個區域，不是全量品質評估。
- **阻塞：** 無。推遲的只有 GPU 資源數字（協定三類之一），沒有正確性檢查被推遲。
- **下一步：** phase-04（執行器、run 目錄與逐張＋平均報告）。依賴 01、02、03 全部 `Complete`。
- **證據位置：** 本筆記錄；run 目錄 `evaluation/runs/20260918T180259Z/`（未進版本控制）。本階段 commit 依序為 `c2c0e26`（`docs:` start）、`15e5431`（`test:` red）、`3800815`（`feat:` descriptor 與倍率斷言）、`fea3911`（`feat:` 從 LR PNG 執行 SR），close 記錄本身另成一顆。

## 2026-09-19 02:15 (CST) — Phase 04: preflight 與兩項待決事項的決定

- **狀態：** `Not started` → `In progress`
- **授權範圍：** [phases/phase-04-runner-and-report.md](phases/phase-04-runner-and-report.md)。
- **依賴確認：** phase-01、02、03 在本檔皆為 `Complete`，且各有觀察證據（尺寸鏈、六組性質檢查、SR 尺寸與 pipeline 雜湊不變）。**度量與退化的正確性已在前面階段驗證過，本階段不重新驗證，只做組裝。**
- **本階段範圍（複述）：** CLI 入口、取樣參數、run 目錄防覆蓋、逐張失敗隔離、平均的納入規則、`report.md` 完整內容、結束摘要與退出碼。
- **非目標（複述）：** 不改退化契約與度量約定、不加畫質優化或模型選項、不做圖表、不做 CSV／JSON、不跑全量 738 張。
- **停止條件（複述）：** 需要全量執行或預估超過十分鐘；**為了讓平均好看而改變納入規則**。
- **決定一（解決 Unresolved：樣本上限預設值）：** 預設 **5 張**，可由 `--limit` 覆寫。
  - **依據：** phase-03 在**沙箱 CPU** 實測單張端到端 16.0–16.3 秒，加上 phase-02 實測的 LPIPS 4.74 秒與 PSNR／SSIM，單張約 21–22 秒。5 張約 110 秒，遠在十分鐘授權內；CPU 上的十分鐘上限約 27 張。
  - **裝置綁定：** 這個上限是**沙箱 CPU** 的數字。GPU 上會顯著更快，實際上限待「待 GPU 補測」第 1、3 項回來後重估。**報告標頭必須寫明該預設值假設的裝置。**
- **決定二（解決範圍內待選：防覆蓋策略）：** 採用**加序號**，不是直接失敗。
  - **作法：** 目錄名為 UTC `%Y%m%dT%H%M%SZ`；若已存在則試 `<name>-2`、`<name>-3`…，直到成功建立為止。底層仍用 `mkdir(exist_ok=False)`，**任何情況下都不會寫進既有目錄**。
  - **理由：** 同一秒內連跑兩次是使用者會做的事（驗收條件就要求連跑兩次），直接失敗會讓第二次執行白跑。加序號同時滿足「絕不寫進既有目錄」與「連跑兩次都能成功」。
  - phase-01 的 `create_run_directory` 維持嚴格語意（已存在即 `FileExistsError`），新的 `allocate_run_directory` 建在它之上；嚴格版正是「不覆蓋」的保證所在，因此不改它的行為，也不改 phase-01 的檢查。
- **驗證（實際觀察）：** 目前 `evaluation/runs/` 下有兩個 run（`20260918T171502Z`、`20260918T180259Z`），合計 8 個 PNG。761 筆雜湊清單與 preflight 相同。
- **限制：** 本筆為唯讀 preflight 與兩項設計決定，尚未寫任何執行器程式。
- **阻塞：** 無。
- **下一步：** 依「Commit 切點」分四顆實作：run 目錄配置、批次執行、平均、報告。
- **證據位置：** 本筆記錄；commit 見本階段 close 記錄的清單。

## 2026-09-19 02:35 (CST) — Phase 04: close

- **狀態：** `In progress` → `Complete`
- **授權範圍：** [phases/phase-04-runner-and-report.md](phases/phase-04-runner-and-report.md)。
- **變更：** 新增 `evaluation/runner.py`、`summary.py`、`report.py`、`run_evaluation.py`（CLI），擴充 `runs.py`；四個新檢查模組。修正 `metrics.py` 的 SSIM 記憶體用量。新增 `context/phase-04-context.md`，並據新證據更新 `PLANS.md`「資源」與 `phases/phase-05`。
- **驗證（聚焦，實際觀察）：** `TORCH_HOME=$TMPDIR/torch-home .venv/bin/python -m unittest discover -s evaluation` → **`Ran 94 tests` `OK`**。`.venv/bin/python -m unittest discover -s tests` → **`Ran 33 tests` `OK`**，每顆 commit 後皆重跑。
- **五項必要檢查（實際觀察）：**
  1. **不覆蓋舊紀錄：** 連跑兩次 → `evaluation/runs/20260918T181724Z`（3 張）與 `evaluation/runs/20260918T182231Z`（1 張）。第二次之後，第一次的 **13 個檔案在大小、mtime 與 SHA-256 三項上全部相同**（`find -printf '%p %s %T@'` 加 `sha256sum` 的快照 `diff` 無差異）。
  2. **同名目錄：** 單元檢查以真實檔案系統驗證：同一時刻連續配置三次 → `20260919T023000Z`、`20260919T023000Z-2`、`20260919T023000Z-3`；先寫入第一個目錄的 `report.md` 在之後兩次配置後內容與 `mtime_ns` 未變；預先存在、內含外來檔案的同名目錄不被寫入，配置器跳到 `-2`。
  3. **單張失敗隔離：** `good1`／`bad`／`good2` 批次，模型拒絕 `bad` → 回傳 good1 與 good2 的成績，`bad` 進失敗清單（stage `sr`、原因為模型自己的訊息），批次未中斷；16-bit PNG 混入批次 → stage `decode`、原因含位深，其他圖照常量測。
  4. **PSNR `inf`：** 端到端以純色圖驗證——常數影像經降採樣與 bicubic 放大後完全相同，bicubic 線 PSNR 為 `inf`、SSIM 為 1.0（±1e-6）。平均層以 fixture 驗證：該張**只**被排除於 PSNR 平均（`counted 1`、`excluded_infinite 1`），SSIM／LPIPS 仍納入兩張；任一線 `inf` 即排除；全部 `inf` 時 `counted 0`、平均為 `None`、勝方 `n/a`，不編造數字。
  5. **報告完整性：** 33 個必填標頭欄位逐一以正規式檢查存在且非空；`render_report` 在缺欄時直接拋錯。逐張列數等於成功張數，平均列存在，失敗清單含環節與原因。`grep -E "\| *\||None|nan|NaN"` 在真實報告上**無命中**。
- **驗證（較廣，真實資料）：** `\.venv/bin/python evaluation/run_evaluation.py --limit 3`，run 目錄 `evaluation/runs/20260918T181724Z`，3 張、0 排除，耗時 256.5 秒。
  - **逐張（量測環境：沙箱 session、CPU）：**
    | 檔名 | SR PSNR | bic PSNR | SR SSIM | bic SSIM | SR LPIPS | bic LPIPS |
    |---|---|---|---|---|---|---|
    | `…0001_W.JPG` | 21.7416 | 22.0661 | 0.600584 | 0.599409 | 0.367362 | 0.543673 |
    | `…0002_W.JPG` | 21.9362 | 22.2449 | 0.598002 | 0.598057 | 0.364103 | 0.547136 |
    | `…0003_W.JPG` | 21.9264 | 22.2477 | 0.593815 | 0.594244 | 0.362619 | 0.548625 |
  - **平均：** PSNR SR `21.8681` vs bicubic `22.1862` → **bicubic 勝**（差 0.3182）；SSIM SR `0.597467` vs bicubic `0.597237` → SR 勝（差 **0.000230**，逐張為 1 勝 2 負，此差距不具實質意義）；LPIPS SR `0.364695` vs bicubic `0.546478` → **SR 勝**（差 0.181784）。
  - **這正是 `GOALS.md`「已知會影響結論解讀的性質」預告的組合**（PSNR 輸、LPIPS 明顯贏）。依該節規定如實記錄，**未回頭調整退化流程或度量約定**。
  - **重現性：** 第二次執行（`20260918T182231Z`、`--limit 1`）對同一張圖得到 PSNR `21.741615`、SSIM `0.600584`、LPIPS `0.367362`，與第一次逐位數相同。
  - 報告標頭的 `git HEAD` 為 `54a223e…`、`worktree 狀態` 為「追蹤檔全部乾淨」，追溯鏈成立。
- **兩項成本與正確性修正（詳見 [context/phase-04-context.md](context/phase-04-context.md)）：**
  - **全尺寸 SSIM 的成本：** 首次真實執行單張 85.5 秒，遠高於 preflight 推估的 21–22 秒。逐項實測（4056×3040、沙箱 CPU）：載入 0.40 s、PSNR 0.14 s、**SSIM 21.34 s**、LPIPS 3.09 s；每張需各算兩次。獨立程序量測三種 SSIM 形式：三通道 11×11 為 21.82 s／**15423 MiB**、逐通道 11×11 為 21.26 s／13269 MiB、**逐通道可分離為 4.33 s／3355 MiB**。改用第三種（commit `264c6b4`），值由 `0.599408548507597` 變為 `0.5994085485075943`，**差 `2.665e-15`**；phase-02 的 naive 逐視窗交叉核對（二維 kernel、獨立實作、容差 1e-9）改動後仍通過。依據 `AGENTS.md`「為避免記憶體不足…屬於讓流程可運行的工作」。**定義未變，分數未被調整。**
    - 修正後重測單張端到端：**30.3 秒、峰值 RSS 4287 MiB**（`/usr/bin/time -v`）。CPU 上十分鐘授權對應約 **20 張**，預設 `--limit 5` 約 150 秒。
  - **裝置歸屬：** PSNR 與 SSIM 的輸入來自 Pillow，**永遠在 CPU 以 float64 計算**，不隨 SR 裝置改變；只有 SR 線與 LPIPS 跟隨裝置。原報告只有一欄「度量 device」填 SR 的裝置，在沙箱 CPU 碰巧正確，**但在使用者的 GPU 執行會把四個實際在 CPU 算出的數字標成 GPU**。已拆成「PSNR／SSIM device」與「LPIPS device」兩欄並改寫「跨批次可比性」（commit `63d1e2c`）。這也降低了 GPU 的 VRAM 風險：float64 全尺寸 SSIM 從來不會被搬上 12227 MiB 的卡。
- **計劃更新（依 `PLANS.md`「新證據推翻後續假設時，先修計劃再繼續」）：** `PLANS.md`「已確認基線 / 資源」加入實測數字與裝置歸屬；`phases/phase-05` 的樣本規模改引 phase-04 實測、preflight 的磁碟檢查改用實測體積、新增「驗收時需確認標頭已分欄」。**`GOALS.md` 未變更**：沒有任何固定約定或成功條件被改動。
- **兩項設計決定的實際結果：** 樣本上限預設 5（見 02:15 記錄）；防覆蓋採加序號，底層仍 `mkdir(exist_ok=False)`。
- **產物體積（實測）：** 1 張 run 為 **53 MB**，3 張為 **159 MB**。目前 `evaluation/runs/` 共四個 run。
- **不變式（實際觀察）：** 761 筆雜湊清單 `diff` 完全相同；`git status --short src tests pyproject.toml requirements-wsl.txt models input output` **為空**；所有寫入都在 `evaluation/runs/<timestamp>/` 之下。
- **限制：**
  - 所有數字皆為**沙箱 session、CPU**，不是交付環境。
  - SSIM 平均的 SR 勝出僅 0.000230，逐張 1 勝 2 負，**不應解讀為 SR 在 SSIM 上勝出**。
  - 3 張樣本全部來自同一次飛行的連續影像，場景高度相似。
  - 同名目錄的防覆蓋只在單元檢查中以人為配置驗證，真實 CLI 兩次執行落在不同秒數，未觸發序號路徑。
- **阻塞：** 無。本階段未新增「待 GPU 補測」項目（清單仍為 3 項）。
- **下一步：** phase-05（真實小樣本驗收、GPU 交接腳本、成本估算與文件對齊）。
- **證據位置：** 本筆記錄；`context/phase-04-context.md`；run 目錄 `20260918T181724Z`、`20260918T182231Z`、`20260918T183156Z`。本階段 commit 依序為 `8c647f4`（`docs:` start 與兩項決定）、`68c7305`（`test:` red）、`874a4b7`（`feat:` run 目錄配置）、`0dfc5a7`（`feat:` 批次執行）、`06bb196`（`feat:` 平均）、`5db48db`（`refactor:` 共用勝方規則）、`46695c2`（`feat:` 報告）、`54a223e`（`feat:` GPU 記憶體釋放）、`51e487e`（`feat:` CLI）、`264c6b4`（`fix:` SSIM 記憶體）、`63d1e2c`（`fix:` 標頭裝置歸屬）、`787a0cd`（`docs:` context）、`51b4675`（`docs:` 計劃更新），close 記錄本身另成一顆。

<!-- 追加重要事件時用這個格式：

## <含時區的時間> — Phase <NN>: <事件>

- **狀態：** <原狀態> → <新狀態>
- **授權範圍：** 連結到該階段文件
- **變更：** 簡潔的實際變更
- **驗證：** 確切命令或程序與結果
- **審查：** 適用時的發現或簽核
- **限制：** 未測或已接受的限制
- **阻塞：** 目前阻塞或「無」
- **下一步：** 依 PLANS.md 的下一個可執行動作
- **證據位置：** context、review、log、產物或 commit
-->
