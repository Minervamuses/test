# build — Build Log

本檔是階段狀態與觀察證據唯一來源；計劃描述預期工作，本檔只記實際實作／驗證。

## 階段摘要

| 階段 | 狀態 | 開始 | 完成 | 證據 | 阻礙 |
|---|---|---|---|---|---|
| 01 — 單張推論 | Complete | 2026-09-15 | 2026-09-17 | 真實 Compact GPU 512→2048 PNG／人工檢視／原始 hash／VRAM 通過；既有 13 tests 及負向 CLI 證據 | 無；4K 不屬本階段驗收 |
| 02 — 資料夾 CLI | Complete | 2026-09-17 | 2026-09-17 | CLI 12＋I/O 7 tests；預設／args 真實 GPU 批次 2 成功 1 壞圖，極小真實 CPU 通過 | 無 |
| 03 — 模型相容性 | Complete | 2026-09-17 | 2026-09-17 | 真實 SwinIR 512→2048、17×19／1×1、共用 CLI／FP32／GPU／圖片及 hash 通過 | 無；Compact 保持候選，SwinIR tiling metadata 交接 phase-04 |
| 04 — 分塊與驗收 | Not started | — | — | — | 尚未進入實作 preflight |

只使用 Not started、In progress、Blocked、Complete。Complete 必須有全部必要 acceptance／檢查證據。

## 證據規則

- 記實際命令／人工檢視步驟、工作目錄、環境、簡短結果、pass／fail／skipped／unavailable。
- 模型驗證記 checkpoint 身分、版本／來源或本機雜湊、scale、輸入／輸出尺寸與位置、裝置、大致耗時；不貼全部 console 或建立 benchmark。
- 每條 acceptance 可回指證據；原始檔保留與結果是否為本次產出應可確認。
- 未執行、缺材料、模擬分支與真實 CPU／GPU 推論分開記錄。
- 重大失敗與更正採追加，不抹除影響後續理解的歷史。
- context 只存重要發現，狀態／例行結果留在本檔，不寫敏感資料。

## 活動紀錄

尚無實作活動。初始計劃已撰寫；所有 application checks、模型推論與圖片驗收均未執行。計劃文件的結構檢查不算實作證據。

後續每筆包含時間與時區、階段、狀態變更、授權依據、實際變更、命令／結果、證據位置、限制／阻礙、下一個符合依賴條件的動作。


### 2026-09-15T17:32:56+08:00 — Phase 01 唯讀 preflight、基線更正與可審查依賴提案

- 授權：使用者啟動 build/ 實作，要求每步 commit；後續補充先建框架，圖片及權重稍後提供。只處理 phase-01，批次 args、第二模型與 tiling 尚未開始。
- 狀態：Not started → Blocked。唯讀準備已完成；環境／manifest 提案尚未批准。材料延後不構成 SR 驗收通過。
- 工作目錄：`/home/minervamuses/drone-image-analysis`。Windows PowerShell 僅呼叫 `wsl.exe -d Ubuntu-24.04`；所有專案 Shell、Git、Python、pip 均為 Linux。複雜唯讀 Python 查核以 stdin 傳給 WSL `python3 -`，未安裝套件。
- 依序讀取適用指引（使用者提供的 Personal Engineering Defaults 與根 AGENTS.md）、GOALS、PLANS、build-log、phase-01；無其他適用 AGENTS.md，無 context/、code_review/、程式、設定或測試可重用。
- **追加更正：** PLANS 的「非 Git repository」已過時。live repository 有 `.git`，分支 main 原先無 commit，9 個既有文件均已暫存，`git diff --exit-code` 無未暫存差異。已原樣提交 `d203598`（`docs: preserve initial SR goals and implementation plan`），未改 AGENTS.md。其 SHA-256 仍為 `7929b09ceb31e9703380e6225ef7aad9d9141ff6fc830949676f7f024daf7629`。

#### 已執行命令及觀察

下列命令在 WSL 專案根目錄執行；查核使用的資料沒有 SR 輸入／輸出。

~~~bash
pwd
uname -sr
cat /etc/os-release
id -un
find / /home /home/minervamuses -maxdepth 1 -name AGENTS.md -type f -print 2>/dev/null
find . -path ./.git -prune -o -name AGENTS.md -print
find . -maxdepth 3 -type f -not -path './.git/*' -print
command -v bash git python python3 uv pip pip3 docker
git --version
python3 --version
pip3 --version
python3 -m pip show torch spandrel Pillow setuptools
python3 -m venv --help
python3 -m ensurepip --version
git status --short
git branch --show-current
git diff --exit-code
git diff --cached --check
sha256sum AGENTS.md
nvidia-smi --query-gpu=name,driver_version,memory.total,memory.free --format=csv,noheader
nvidia-smi --query-gpu=compute_cap --format=csv,noheader
free -h
df -h .
~~~

- PASS：Ubuntu 24.04.2，WSL2 kernel 6.6.87.1，使用者 minervamuses；Bash/Git/Python3 為 `/usr/bin`，Git 2.43.0，Python 3.12.3，pip／ensurepip 24.0，x86_64、glibc 2.39。
- UNAVAILABLE：此專案尚無 .venv；系統 Python 未安裝 torch、spandrel、Pillow，只有 setuptools 68.1.2。`rg` 不存在，改以局部 find；沒有安裝搜尋工具。鄰近其他專案有 .venv，不借用或修改。
- PASS（資源快照，非 CUDA 框架驗證）：RTX 5070 Ti **Laptop**，driver 591.74，compute capability 12.0，VRAM 12227 MiB、當時空閒 10827 MiB；RAM available 約 30 GiB，swap 8 GiB，磁碟可用 842 GiB。
- UNAVAILABLE：真實圖片、Compact checkpoint、本機來源／使用條件與模型 descriptor 尚不存在。未下載 dataset 或權重。
- PASS：`git diff --cached --check`；初始 commit 成功。初查 `git log` 的 unborn main 報錯是已確認的基線狀態，不是程式測試失敗。

#### 依賴／環境提案（待批准，尚未執行）

沿用 Python 3.12、`python3 -m venv .venv`、venv 內 pip 24.0，新增最小 `pyproject.toml`、`setuptools.build_meta`（setuptools 81.0.0），採 `src/drone_sr/` editable 安裝。Python／系統套件與其他專案環境不變。

| 項目 | 提案版本／來源 | 理由 |
|---|---|---|
| torch | 2.11.0+cu128，官方 download.pytorch.org wheel | CUDA 12.8 Blackwell 路線；Python 3.12、manylinux 2.28 x86_64 |
| torchvision | 0.26.0+cu128，同一官方來源 | Spandrel 必需；官方配對 torch 2.11.0，也用於 RGB tensor／PIL 轉換 |
| spandrel | 0.4.2，PyPI | 使用 ImageModelDescriptor 統一載入／推論；內含 Compact、SwinIR |
| Pillow | 12.3.0，PyPI | 圖片解碼／RGB／PNG |
| setuptools | 81.0.0，PyPI | 標準 packaging；符合 torch 的 setuptools<82 約束 |

允許 pip 安裝以上套件宣告的必要傳遞依賴：numpy、safetensors、einops、typing-extensions、filelock、sympy、networkx、jinja2、fsspec，以及 CUDA 12.8.1 runtime 元件、cuda-bindings 12.x、cuDNN 9.19.0.56、cuSPARSELt 0.7.1、NCCL 2.28.9、NVSHMEM 3.4.5、Triton 3.6.0 及其必要依賴。實際解析版本安裝後記錄；不裝額外模型架構、音訊套件、測試框架或系統 CUDA Toolkit。

- 已唯讀取得 PyPI JSON、官方 wheel 目錄與 `.metadata`，核對 Python/ABI、torchvision 配對及傳遞依賴。官方 `download-r2.pytorch.org` 的 HEAD／metadata 回傳 HTTP 403；同一官方檔案位於 `download.pytorch.org` 的 metadata 與 HEAD 可讀，提案直接使用後者 URL。
- HEAD 實測 torch wheel 820,326,880 bytes，torchvision 8,057,226 bytes；PyPI 回報 Spandrel 320,811 bytes、Pillow 6,940,830 bytes。完整 CUDA 傳遞依賴尚未下載，**總下載暫估 3–5 GB、保留 15 GB 磁碟、一次性安裝約 5–20 分鐘（網速未知），無 API 費用**。批准上限提案為下載 6 GB／安裝 20 分鐘；如仍不足停止並回報，不擴大重試。
- 現有資源與 driver 版本沒有顯示小型軟體驗證必然不可行；**PyTorch CUDA kernel 實際可用性未驗證**。CUDA 12.8 對 Blackwell 的官方支持與 driver 向後相容是選型依據，不是本機驗收證據。
- 最小替代方案：只寫 phase-01 程式及標準庫語法檢查，將 runtime tests 記 unavailable；不能把它稱為可執行 SR 已完成。要跑 I/O／descriptor checks，仍需要批准以上環境。

可審查安裝命令（尚未執行；工作目錄為專案根目錄）：

~~~bash
python3 -m venv .venv
.venv/bin/python -m pip install --no-cache-dir --only-binary=:all: \
  'https://download.pytorch.org/whl/cu128/torch-2.11.0%2Bcu128-cp312-cp312-manylinux_2_28_x86_64.whl' \
  'https://download.pytorch.org/whl/cu128/torchvision-0.26.0%2Bcu128-cp312-cp312-manylinux_2_28_x86_64.whl' \
  'spandrel==0.4.2' 'Pillow==12.3.0' 'setuptools==81.0.0'
.venv/bin/python -m pip install --no-deps --no-build-isolation -e .
~~~

官方來源：[PyTorch 配對版本](https://pytorch.org/get-started/previous-versions/)、[CUDA 12.8／Blackwell](https://pytorch.org/blog/pytorch-2-7/)、[NVIDIA CUDA 12.8 driver 表](https://docs.nvidia.com/cuda/archive/12.8.0/cuda-toolkit-release-notes/index.html)、[Spandrel 0.4.2 metadata](https://pypi.org/pypi/spandrel/0.4.2/json)、[descriptor v0.4.2 實作](https://github.com/chaiNNer-org/spandrel/blob/v0.4.2/libs/spandrel/spandrel/__helpers/model_descriptor.py)。descriptor 已提供 padding／裁回，先沿用，尚未本機執行驗證。

#### 下一步與 acceptance

依賴批准後完成最小單張程式、RGB／clamp／PNG／descriptor 尺寸及載入失敗檢查；極小 CPU 與 GPU 軟體計算分開記錄。真實 Compact PNG 開啟、內容／色彩、scale、來源 hash、checkpoint 身分與耗時均仍 unavailable，等待使用者稍後提供材料；不以未訓練模型或 mock 取代。框架準備完成後 phase-01 仍 Blocked，phase-02～04 維持 Not started。


### 2026-09-15T17:40:34+08:00 — Phase 01 環境批准與框架準備

- 使用者批准前述 6 GB／20 分鐘範圍的隔離環境及極小 CPU／GPU 軟體檢查，並要求「把你採用的寫入 readme」。狀態 Blocked → In progress；checkpoint／資料驗收仍延後。
- 前一步 `cbd22ad` 已提交 preflight、環境提案及 PLANS 基線更正。每步 commit 授權沿用。
- 已新增 `.gitignore`，保護 input/、output/、models/ 的本機資產與 .venv；只版控 `.gitkeep`。採用 `src/drone_sr/`，職責為單張 CLI、I/O、共用 descriptor 推論；未建立空 model.py、tiling.py 或額外框架。
- 在等待依賴批准時，已用 WSL 系統 Python 的 `ast.parse` 對 4 個模組與 2 個 unittest 檔完成語法檢查（PASS）。沒有將依賴未安裝造成的 import failure 當成功能失敗測試；本次是新功能，runtime correctness checks 待環境可用後執行。
- 17:38:09 +08:00 在專案根目錄啟動已批准的 `python3 -m venv .venv` 與 `timeout 20m .venv/bin/python -m pip install --no-cache-dir --only-binary=:all: --progress-bar off`，完整參數沿用上方兩個官方 wheel URL 與三個 PyPI 固定版本。此筆記錄時仍在安裝，尚未記 PASS；未使用系統 pip 安裝。
- README 已列出採用的版本、來源、命令、資源估計與現階段限制；驗證區標成執行中，待實測更新。

- 提交前 `ast.parse`（6 個 Python 檔）與 `tomllib.load(pyproject.toml)` 通過；首次 `git diff --cached --check` 發現兩個新模組末尾多餘空行，已只移除這兩行，再執行相同 whitespace check。尚無 runtime 結果。


### 2026-09-15T17:52:10+08:00 — Phase 01 安裝來源修正（已另行批准一次重試）

- `a42eccb` 已提交單張框架、必要測試、pyproject 與 README；當時只有語法／diff 檢查，尚未有 runtime PASS。
- 初次安裝未完成：PyPI cuDNN 657,906,812 bytes，在 17:42:25 收到約 46.4 MB，17:44:23 為 76,933,120 bytes，約 0.26 MB/s；推估光該檔案剩餘即超過原 20 分鐘預算。沒有把下載等待當作推論或軟體測試失敗。
- 已唯讀確認 PyTorch 官方 wheel 目錄連向 NVIDIA 官方的同版本 cuDNN，SHA-256 與 PyPI 相同（`ac6ad90a075bb33a94f2b4cf4622eac13dd4dc65cf6dd9c7572a318516a36625`）；NVIDIA HTTP Range 讀 1,048,576 bytes 花 0.45 秒。這是連線觀察，不承諾完整下載速度。
- 使用者明確批准改官方來源重試一次，另外最多 20 分鐘，兩次累計下載仍限 6 GB。17:48:16 將完整 torch／torchvision wheel 以 hard link 保留到 `/tmp/drone-sr-install-8lniopxv/`（820,326,880 + 8,057,226 bytes）；驗證 pip PID 的 cwd 與 argv 後停止該程序。原程序回報 Terminated／exit 1；未完成 cuDNN 為 153,262,080 bytes，不拿來安裝。
- 唯讀來源核對中，PyTorch Triton wheel 的 SHA-256 與 PyPI 同名檔案不同，檢查正確拒絕該替換；Triton 保留 PyPI 3.6.0。第一次產生安裝清單因該 assertion 中止，尚未啟動重試；更正為只替換 SHA-256 相同的 15 個 NVIDIA wheel，沒有更換套件版本。清單核對失敗不是 application test。
- 新增 `requirements-wsl.txt`，集中已批准版本、PyTorch 官方 wheel 連結及 NVIDIA 官方 wheel URL／SHA-256，供 README 的 pip 命令使用；NVIDIA wheel 合計 2,927,580,737 bytes。來源清單是為解決本次安裝瓶頸，沒有新 backend 或自製下載器。
- 17:50:53 透過 `timeout 20m bash /tmp/drone-sr-install-8lniopxv/install.sh` 啟動唯一已批准重試：先 `.venv/bin/python -m pip install --no-deps --no-cache-dir --progress-bar off` 安裝上列兩個保留的 wheel，再 `.venv/bin/python -m pip install --no-cache-dir --only-binary=:all: --progress-bar off -r requirements-wsl.txt`，最後 `.venv/bin/python -m pip install --no-deps --no-build-isolation -e .`。此筆記錄時仍執行中。
- 等待期間以 `PYTHONPATH=src` 與 WSL 系統 Python 3.12 跑過 `python3 -m drone_sr --help`、空 input 的 `python3 -m drone_sr`，均 exit 0；暫存工作目錄缺 input 時 exit 1、未建立 output。三項 guard／help 觀察 PASS，不需 import 推論依賴，不等於 SR 完成。

- 重試的 pip 輸出確認 15 個 NVIDIA wheel 全部已下載；接著發現最初清單的兩個 `--find-links <單一 wheel URL>` 被 pip 當 HTML page 而跳過。已將清單改為要求先安裝 torch／torchvision，README 分成 `pip install --no-deps <兩個官方 wheel URL>` 與 `pip install -r requirements-wsl.txt`；本次實際重用的兩個本機 wheel 已安裝，故此警告未阻止續接依賴。不宣稱重跑過全新環境。


### 2026-09-15T18:07:40+08:00 — Phase 01 框架驗證完成，真實驗收維持 Blocked

#### 環境與必要軟體檢查

- 官方來源設定已提交 `35e4037`。唯一已批准的重試於 17:50:53 開始、18:02:06 成功（11 分 13 秒，exit 0）；drone-sr 0.1.0 editable 安裝完成。兩次下載依已知 wheel 大小及中止片段加總約 4.2 GB，低於累計 6 GB 上限；這是套件大小估算，未量測網卡總流量。
- `.venv` 實測 `du -sh .venv` 為 6.7G。Python 3.12.3／pip 24.0；torch 2.11.0+cu128、torchvision 0.26.0+cu128、spandrel 0.4.2、Pillow 12.3.0、setuptools 81.0.0。
- 傳遞依賴實際版本：numpy 2.5.3、safetensors 0.8.0、einops 0.8.2、triton 3.6.0、cuda-bindings 12.9.7、cuda-pathfinder 1.8.1、cuda-toolkit 12.8.1、typing_extensions 4.16.0、filelock 3.32.6、fsspec 2026.7.0、networkx 3.6.1、sympy 1.14.0、mpmath 1.3.0、Jinja2 3.1.6、MarkupSafe 3.0.3。15 個 NVIDIA runtime wheel 的實際版本與 SHA-256 已固定在 requirements-wsl.txt；不另建 lock 或環境管理工具。
- WSL 專案根目錄，啟用 `.venv` 後實際命令：

~~~bash
python -m pip check
python -m unittest discover -s tests -p 'test_image_io.py' -v
python -m unittest discover -s tests -p 'test_inference.py' -v
~~~

- PASS：`pip check` 回報 No broken requirements found；I/O 7/7，0.049 秒；inference 6/6，0.038 秒（unittest 本身計時，不含 interpreter/import）。沒有 skipped tests。測試中的 toy descriptor 與 mock 僅是 correctness 證據。
- I/O 證據包含已知 RGB 像素、float32／BCHW／[0,1]、灰階轉 RGB、PNG round trip、clamp／round、高位深拒絕、non-finite／編碼失敗保留既有結果、來源 path／symlink／hard link 拒絕。
- inference 證據包含真正 ImageModelDescriptor 對奇數尺寸 padding／裁回、錯誤輸出尺寸拒絕、缺模型、真正 ModelLoader 對壞 checkpoint 的錯誤、CPU／float32／eval 準備，以及非 RGB／非 image descriptor 拒絕。
- 同一 shell 呼叫尾端的唯讀 `du` 因 PowerShell stdin 結尾 CR 被誤當路徑字元而 exit 1；上述 13 項測試均已通過。改用 `wsl.exe -d Ubuntu-24.04 -- bash -lc` 的 `du -sh .venv` 得到 6.7G，沒有重跑已通過的 focused tests。

#### 代表整合：真正軟體執行，合成材料／未訓練權重

實際命令：

~~~bash
.venv/bin/python /tmp/drone-sr-install-8lniopxv/validate_phase01.py
.venv/bin/python -m drone_sr --help
.venv/bin/python -m drone_sr
.venv/bin/python -m pip list --format=json
~~~

- 整合 script exit 0。採 `torch.manual_seed(0)`、Spandrel 0.4.2 內建 Compact，num_in_ch=3、num_out_ch=3、num_feat=8、num_conv=1、upscale=2 的**未訓練**小模型，保存 state_dict 後交給真正 ModelLoader 載入；不是預訓練 checkpoint 相容性或畫質驗收。
- 合成 RGB 為 5×7：pixel(x,y) = (50x, 35y, 20(x+y))。證據保留於 `/tmp/drone-sr-phase01-6d4dh_hr/`；摘要為該目錄 `evidence.json`，script 位於上列暫存路徑。臨時 `models/model.pth` 僅在不存在時建立為此 checkpoint 的 symlink，測後移除；未留下模型作交付預設。
- 子程序實際執行 `.venv/bin/python -m drone_sr`，cwd 各為下表 cpu／cuda 目錄；CPU 子程序設定 `CUDA_VISIBLE_DEVICES=''`，實際跑 CPU 計算，沒有 mock torch 的 CUDA 判斷；GPU 子程序使用可見 GPU 自動選 cuda:0。兩者均只有一張輸入，Processed 1、Failed 0。
- CUDA 實測：torch.version.cuda=12.8；RTX 5070 Ti Laptop、capability (12,0)；wheel arch list 包含 sm_120；模型驗證前空閒 VRAM 10959 MiB。小型 GPU forward 成功，不以 nvidia-smi 代替 kernel 證據。

| 裝置 | 輸入 → 輸出 | 尺寸 W×H | CLI 耗時 | 結果 |
|---|---|---|---|---|
| cpu | `/tmp/drone-sr-phase01-6d4dh_hr/cpu/input/synthetic.png` → `/tmp/drone-sr-phase01-6d4dh_hr/cpu/output/synthetic.png` | 5×7 → 10×14（scale 2） | 2.029 秒 | PNG/RGB 可解碼、來源 hash 不變 |
| cuda | `/tmp/drone-sr-phase01-6d4dh_hr/cuda/input/synthetic.png` → `/tmp/drone-sr-phase01-6d4dh_hr/cuda/output/synthetic.png` | 5×7 → 10×14（scale 2） | 2.475 秒 | PNG/RGB 可解碼、來源 hash 不變 |

- checkpoint：`/tmp/drone-sr-phase01-6d4dh_hr/synthetic-untrained-compact.pth`；SHA-256 `51c68a5b69c1eaa2430dce43ae6b3dc28af7b8baedd1d174e3704e06131c9e12`。
- 兩份合成輸入 SHA-256 均為 `2dc8be744ea6c05a25a3d4a36b1ea099794efb52febd56f07c751c2bf7353a95`，執行前後相同；CPU／GPU 輸出 SHA-256 均為 `03ca13591bc4f1f73b5992de9961b367e900c1d83f23d797cc31634480167169`。此一致性只描述本次小案例。
- 透過 image viewer 開啟 cpu/input/synthetic.png 與 cuda/output/synthetic.png，確認是可顯示的彩色 PNG；尺寸與像素證據以解碼及 tests 為準。**沒有真實圖片的人工色彩／內容驗收**。
- 真正 CLI 負向：`corrupt/input/broken.PNG`（bytes `not an image`）→ exit 1，Processed 0／Failed 1，未建立 output；缺模型 → exit 1、`SR model not found: models/model.pth`；invalid checkpoint（bytes `not a checkpoint`）→ exit 1、`Unable to load SR model: invalid load key, 'n'.`。後兩者保留前述成功 PNG 的 hash。
- 安裝後再次執行 `--help` 與空 input 的預設命令：exit 0，分別正常顯示 help 與 No supported images found in input/。缺 input 先前用同一源碼在暫存 cwd 驗證 exit 1。
- `git check-ignore -v .venv/bin/python models/model.pth input/DJI.JPG output/DJI.png` 確认環境、權重、圖片與產出均排除；AGENTS.md 保持原 hash。沒有 push、切分支或 worktree 變動。

#### Phase 01 acceptance 核對

| Acceptance | 結果／證據 |
|---|---|
| 真實單張 Compact PNG 已開啟、內容尺寸正常、原圖不變 | **UNAVAILABLE**：使用者延後提供真實圖片及預訓練 checkpoint；上表只有合成材料 |
| Spandrel descriptor 載入／推論，無架構專屬 production flow | **PASS（框架）**：load_model → ModelLoader → ImageModelDescriptor → descriptor(tensor)；CPU／GPU 合成 Compact CLI 成功 |
| I/O、尺寸、載入失敗最小測試 | **PASS**：13/13 focused checks，另有真正 CLI 負向檢查 |
| 環境／checkpoint／命令／耗時可追溯 | **PASS（框架材料）**：本節版本、path、hash、尺寸、裝置、耗時；真實材料仍 unavailable |

#### GOALS.md 八項成功條件及 PLANS 整體完成標準核對

| GOALS 項次 | 已觀察／未完成 |
|---|---|
| 1 預設與指定資料夾、真實 PNG／摘要 | 單張預設合成 CLI 通過；指定資料夾／批次尚未實作，真實 PNG 未驗證 |
| 2 Compact＋SwinIR 預訓練 checkpoint、單一預設 | 共用 descriptor 框架已運行；兩個預訓練 checkpoint 均未提供，未選定交付預設 |
| 3 自動 GPU／CPU、明示裝置 | 極小合成模型兩個分支實際執行，CPU 以環境隱藏 GPU；真實預訓練模型仍待驗收 |
| 4 RGB／float／BCHW／dtype/device／嚴格尺寸 | focused checks 與 5×7 → 10×14 CPU/GPU 整合通過；無真實圖證據 |
| 5 自動 overlap tiling／全部邊界／無明顯接縫 | 尚未實作或驗證（phase-04） |
| 6 建立輸出、保留原始／其他輸出、成功才覆蓋 | 單張 I/O 與負向 CLI 證據通過；批次和自訂資料夾邊界尚待 phase-02 |
| 7 各錯誤／計數／壞圖繼續 | 缺輸入／空輸入／缺模型／載入失敗／單張壞圖有證據；批次繼續／總數對帳尚待 phase-02 |
| 8 correctness tests＋實測 README | 已寫採用版本與命令，13 項測試通過；明列合成／mock／真實未驗證，未重跑全新環境建置 |

- **整體未完成。** Phase-01 因真實驗收缺項 In progress → Blocked；phase-02、03、04 保留 Not started，未進入依賴階段。README 與 PLANS 已同步本輪批准及已驗證範圍，未降低 GOALS 的完成標準。
- 下一個符合依賴條件的動作仍為 phase-01：使用者提供一張真實小圖與來源／使用條件已確認的 Compact checkpoint 後，核對 descriptor 與原始 hash，執行真實單張及人工檢視；通過前不標 Complete。
- 沒有為 routine checks 建立 context／code_review 文件，未擴充其他階段或再跑 full suite／模型 sweep。

- 收尾已移除 `/tmp/drone-sr-install-8lniopxv/` 內兩個已使用的臨時 wheel（逐檔確認目錄及大小後 unlink，共約 828 MB），保留小型驗證 script／來源清單及合成證據目錄供追溯。確認專案 `models/model.pth` 已不存在；未留下未訓練模型作預設。

### 2026-09-16T21:56:24+08:00 — 取得使用者指定的單一 WhaleDrone 測試影片

- 使用者授權只下載指定 MP4，放入專案根目錄的新資料夾；沿用每一步需 commit 的指示。未下載同名 SRT、其他影片、模型或其他資料集檔案。
- 唯讀 preflight：專案 `/home/minervamuses/drone-image-analysis`，Ubuntu 24.04／WSL2，使用 WSL 的 Bash、Git 2.43.0、Python 3.12.3；Git 工作區原本乾淨，`test-data/` 原本不存在，磁碟可用約 835 GiB。重讀適用 AGENTS.md，未修改指引。
- 來源：[WhaleDrone](https://huggingface.co/datasets/LucieLprt-Dvldr/WhaleDrone)，資料集頁面標示 CC-BY-NC-4.0。對指定檔案 `resolve/main` 做 HEAD，取得 revision `e78c4db9b5e77a582fdac3cb24085c9d8286f818`、大小及 SHA-256；實際下載固定該 revision：
  `https://huggingface.co/datasets/LucieLprt-Dvldr/WhaleDrone/resolve/e78c4db9b5e77a582fdac3cb24085c9d8286f818/videos/Jan-14th-2026-06-15PM-Flight-Airdata/DJI_20260114193309_0004_V.MP4?download=true`
- 實際以 `wsl.exe -d Ubuntu-24.04 -- python3 -` 執行 stdlib `urllib.request.urlopen(..., timeout=30)`，每次讀取 1 MiB，exclusive 寫入新建 `test-data/` 中的 `.MP4.part`；設定 540 秒傳輸上限。下載過程計算 SHA-256，大小與 hash 正確才改名。52.16 秒完成，exit 0，沒有續傳或第二次下載。
- 本機檔案：`/home/minervamuses/drone-image-analysis/test-data/DJI_20260114193309_0004_V.MP4`；大小 **613,561,776 bytes**；SHA-256 **`8dddd14150efee239002d536fa33446629cbde3979ce4e76429a23a4c1f56fda`**，與來源 `X-Linked-Etag` 一致。
- 在 WSL 專案根目錄實際執行：

~~~bash
ffprobe -v error -show_entries format=duration,size:stream=index,codec_type,codec_name,width,height,avg_frame_rate,nb_frames -of json test-data/DJI_20260114193309_0004_V.MP4
sha256sum test-data/DJI_20260114193309_0004_V.MP4
find test-data -maxdepth 1 -type f -printf "%f\n"
git check-ignore -v test-data/DJI_20260114193309_0004_V.MP4
git diff --check
~~~

- PASS：ffprobe exit 0；主影像 stream 0 為 H.264、3840×2160、30000/1001 fps；容器 duration 56.656600 秒、nb_frames 1698（中繼資料，未逐幀解碼）。重新讀取本機檔案計算的 SHA-256 相符；資料夾只有上述一支 MP4，沒有殘留 `.part`。新增 `.gitignore` 的 `/test-data/`，ignore 核對與 diff whitespace 檢查通過；影片不納入 Git。
- **Phase 01 維持 Blocked，後續階段狀態不變。** 本次只取得影片素材，未抽幀、未取得預訓練權重、未跑 SR 或人工畫質驗收；不把檔案完整性與影片中繼資料檢查當成真實推論通過。未改程式，故未重跑軟體測試。

### 2026-09-17T20:14:13+08:00 — Phase 01 指定 Compact 真實驗證 preflight

- 使用者選定 `realesr-general-x4v3.pth`，要求判斷 VRAM 可行後採用並開始驗證。Blocked → In progress；PLANS 補充指定權重下載與既有影片抽取小裁切的授權，保留歷史缺材料證據。
- 依序重讀適用 AGENTS、GOALS、PLANS、build-log、phase-01、實際 CLI／I/O／inference／兩份 tests／pyproject；沒有 context 或 code_review 文件。live Git 為 main／`7fe2103`，`git status --short` 乾淨；models、input、output 各只有 `.gitkeep`，test-data 只有已授權 MP4。唯讀同階段程式審查未發現阻止本次驗證的問題。
- 環境：Windows 只呼叫 `wsl.exe -d Ubuntu-24.04`，專案 `/home/minervamuses/drone-image-analysis`，Linux kernel 6.6.87.1；`command -v bash git python3 ffmpeg ffprobe` 均為 `/usr/bin/`。實際 `nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version,utilization.gpu --format=csv`：RTX 5070 Ti Laptop，12227 MiB total／10633 MiB free、driver 591.74、GPU 6%；`free -h`：31 GiB RAM／30 GiB available；`df -h .`：842 GiB available。
- 唯讀 GitHub API `https://api.github.com/repos/xinntao/Real-ESRGAN/releases/tags/v0.2.5.0`：release id 65167840，指定 asset id 76259217，4,885,111 bytes，建立 2022-08-30T03:47:59Z、更新 03:48:07Z；`digest` 為 null，沒有來源公布的 SHA-256 可比對。只取此 asset，完成後記本機 hash，不冒稱已比對官方 hash。
- 指定來源：`https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth`。官方 repository [LICENSE](https://github.com/xinntao/Real-ESRGAN/blob/v0.2.5.0/LICENSE) 為 BSD-3-Clause；release tag 早於此 asset 加入時間，不把 tag 當作 checkpoint 建立日期。後續以實際 descriptor 確認 Compact／RGB／4×。
- 最小預定工作：只下載 4.89 MB 指定 checkpoint（下載上限 10 MB／120 秒）、從既有 MP4 第 10 秒抽一張 RGB PNG，再取有內容的 512×512 原尺寸裁切；單張 GPU 驗證採現有 float32 程式，每個推論程序上限 120 秒，預估全部數分鐘，無付費 API／新增套件。先視覺選裁切，保留來源與 provenance；不跑整段影片、模型 sweep、4K 全圖或提早實作 tiling。
- 預定 acceptance：真實 CLI 成功 PNG／scale 尺寸、來源 hash 不變、開啟原圖及結果檢查色彩內容；記錄 descriptor／device／耗時與峰值 PyTorch VRAM。既有程式未變，重用 13 項 focused tests 及真正缺／壞模型 CLI 負向證據，不重跑相同軟體 suite。任何必要失敗先處理，尚無真實推論 PASS。

### 2026-09-17T20:18:59+08:00 — Phase 01 權重與真實小圖就緒

- 前一步提交 `088bcb0`。使用 WSL `timeout 240 python3 -` 執行 stdlib 單檔下載及抽圖準備：指定權重一次下載 110.654 秒、4,885,111 bytes，大小符合官方 asset metadata；寫 `.pth.part` 完成後才改名。GitHub 連線慢但在 120 秒下載界線內，沒有重試或下載其他 checkpoint。
- 權重 `models/realesr-general-x4v3.pth`；SHA-256 `8dc7edb9ac80ccdc30c3a5dca6616509367f05fbc184ad95b731f05bece96292`（本機追溯值，官方 digest 未提供）。新建相對 symlink `models/model.pth → realesr-general-x4v3.pth`，沿用原本固定模型入口；未覆寫既有資產。provenance 保存於 `test-data/phase-01-compact-20260917/provenance.json`。
- 實際抽圖命令（cwd 專案根目錄；記錄 JSON 保存完整絕對路徑）：

~~~bash
ffmpeg -hide_banner -loglevel warning -nostdin -n -ss 10 -i test-data/DJI_20260114193309_0004_V.MP4 -map 0:v:0 -frames:v 1 -pix_fmt rgb24 -update 1 test-data/phase-01-compact-20260917/frame_seek10s.png
~~~

- ffmpeg exit 0；有 `stream 0, timescale not set` 容器警告，RGB PNG 實際可解碼且尺寸為 3840×2160。`-ss 10` 表示請求 seek 時間，未另聲稱精確源 frame index。抽圖前影片 hash 與下載紀錄一致；frame SHA-256 `0ca08a179e42c9917d1bab23ebc354d1a8791833b27e81a1dc2a58b662ad9f31`。
- 已開啟 full frame，再以 Pillow `Image.crop((1536,768,2048,1280))` 取得原尺寸 512×512 海面波紋／反光裁切，保存 `input/whaledrone_seek10s_x1536_y768_512.png`；SHA-256 `ad7d8815928ea78bb2243af8639541216e83a7444d78272d91451a2d7dd63faa`。已開啟裁切確認內容／RGB 色彩；此樣本没有可辨識鯨魚，不用來驗證動物細節。
- `.venv/bin/python -` 呼叫現有 `load_model()`：實際 descriptor architecture `Compact`／model class `SRVGGNetCompact`、scale 4、channels 3→3、1,213,296 parameters、`cuda:0`、float32、eval；size requirements minimum=0／multiple_of=1／square=False。PyTorch 2.11.0+cu128／CUDA 12.8，capability (12,0)，wheel 包含 sm_120。詳細值保存 `test-data/phase-01-compact-20260917/descriptor-and-crop.json`。
- 模型已載入但尚未 forward；本步只完成材料與 descriptor 核對。input／output／models／test-data 仍由既有 `.gitignore` 排除，不提交二進位檔。

### 2026-09-17T20:21:03+08:00 — Phase 01 真實 Compact GPU 驗收 Complete

- 前一步 `25ce46b` 已提交材料紀錄。沒有改 production code／環境；沿用既有 13 項 focused tests 與缺／壞 checkpoint 真正 CLI 負向證據，沒有把 mock 記為真實推論。
- 實際命令：WSL 專案根目錄 `timeout 260 .venv/bin/python test-data/phase-01-compact-20260917/validate_compact.py`，exit 0、共約 9.51 秒。此一次性紀錄 script 先以 subprocess 執行**未加 instrumentation 的** `.venv/bin/python -m drone_sr`（timeout 120 秒），再以 120 秒 alarm 呼叫相同 production `load_model/read_image/upscale` 測量 GPU；沒有更換 descriptor、mock、warmup 或參數 sweep。
- 真正 CLI：`Device: cuda:0`、`Model: loaded`、Images 1、Processed 1、Failed 0，exit 0；程序啟動至結束 5.902 秒。512×512 RGB → 2048×2048 RGB PNG，嚴格為 scale 4，輸出為 `output/whaledrone_seek10s_x1536_y768_512.png`，3,647,135 bytes，SHA-256 `db7142ab8ccb9797c411af711ddb44a3b26f45b4b35e30ca987cda810289a33a`。
- 額外一次量測同一 production 路徑（正式 Compact／float32／cuda:0）：以 `torch.cuda.synchronize()` 包住 CPU tensor 上傳＋upscale，0.219621 秒；模型載入＋讀圖＋上傳／推論共 0.386703 秒（不含 imports）。`torch.cuda.reset_peak_memory_stats()` 後，載入至 forward 結束 allocated peak 276,599,808 bytes（263.786 MiB）、reserved peak 297,795,584 bytes（284 MiB）；**不含 CUDA context、其他程序與後續輸出驗證／PNG 編碼的配置**，不冒稱整卡峰值或 steady-state benchmark。
- PASS：量測 tensor finite，shape `(1,3,2048,2048)`；依 production clamp／round 規則轉 uint8 後，與真正 CLI PNG 每個像素相同。來源裁切 SHA、614 MB 原影片 SHA、checkpoint SHA 均與準備時相同。完整命令／stdout／metrics 為該 evidence 目錄的 `validate_compact.py`、`cli.txt`、`validation.json`，所有圖片可回溯本節及上節 path／hash／crop box。
- 人工驗收：開啟 512×512 原圖及本次 2048×2048 PNG；海面波紋、反光相對位置及藍綠色一致，沒有旋轉、色彩通道錯置或空白輸出；SR 有明顯平滑細紋／強化局部邊緣。此觀察證明可用的單張輸出，不宣稱還原真實新增細節或畫質優於其他方法；此裁切無可辨識鯨魚。沒有 PSNR／SSIM、其他模型或 4K 全圖推論。
- Acceptance 逐項：真實 PNG 開啟／內容尺寸／原始保留 **PASS**；Spandrel descriptor 共用路徑 **PASS**；既有 I/O／尺寸／載入失敗 focused evidence **PASS**；環境、來源／權重、命令／耗時／VRAM 可追溯 **PASS**。Phase 01 In progress → Complete。
- 採用指定 checkpoint 作目前固定 `models/model.pth` 候選並寫入 README；此 512×512 case 的 VRAM 有餘裕，不能推定完整 4K 或最終 tiling 已驗收。整體 GOALS 尚未完成：#1 尚缺 args／批次，#2 尚缺 SwinIR，#3 真實 GPU 已補足、CPU 有既有極小合成執行，#4 真實尺寸／dtype 通過，#5 tiling 未實作，#6–7 尚缺批次完整行為，#8 README 已補實測、整體收尾仍待後續。
- 依既有自主計畫，下一個符合依賴條件為 phase-02。每步 commit 沿用；未批准其他 checkpoint 或資料下載。

### 2026-09-17T20:25:09+08:00 — Phase 02 唯讀 preflight

- Phase 01 已於 `15b63fe` Complete；依最初「繼續下一個符合依賴條件的階段」與 PLANS 自主模式進行本階段。重讀 phase-02；其前置／context 狀態與 live code 一致，無使用者新修改。
- 範圍：只擴充現有 __main__.py 的資料夾 args、第一層序列批次、逐圖失敗／計數與來源保護；必要時調整 I/O，不新增依賴、公開技術選項、模組或框架。先新增 tests/test_cli.py 觀察 Phase 01 缺少批次介面的預期失敗，再最小修改。
- 代表驗收使用既有影片 frame 的兩個小裁切及一份故意損壞檔，放於 test-data/phase-02-cli-20260917/ 的隔離資料夾；預設／指定含空白路徑各跑一次，覆蓋只涉及本次建立的驗收 output。CPU 只用約 32×28 真實裁切，以子程序 CUDA_VISIBLE_DEVICES=-1 隱藏 GPU；不使用 mock 冒充 CPU。每個程序上限 120 秒，預估全部約 1 分鐘內，無下載／付費工作。
- 預定檢查：focused test_cli、直接相關 image_io、--help；真實批次 Processed 2／Failed 1／非零退出、成功 PNG 開啟、原始／無關 output 保留，以及極小 CPU 4× PNG。既有 GPU／缺壞模型證據沿用 Phase 01。必要檢查失敗先處理；超出兩次聚焦修正／昂貴工作界線即停止，不進依賴階段。

### 2026-09-17T20:27:50+08:00 — Phase 02 最小失敗測試

- 新增 tests/test_cli.py，12 個 unittest 方法；真實暫存圖片 I/O，mock model／便宜 tensor 放大僅作 correctness checks。涵蓋獨立 args／空白路徑、五格式／大寫／非遞迴、壞圖繼續、同 stem 衝突、跨輸入 symlink／hardlink、防覆寫及儲存失敗；沒有新測試框架。
- 實際命令：WSL 專案根目錄 `.venv/bin/python -m unittest discover -s tests -p test_cli.py -v`。初跑 12 methods，1.331 秒、12 failures（含 subtests）；發現 directory-alias 測試可能誤接受 argparse 不支援參數，補上不得包含 unrecognized arguments 的 assertion，再跑 0.696 秒、15 failures（含 subtests）、exit 1。這是測試辨識能力修正，production 尚未修改。
- 失敗原因符合缺少功能：--input／--output 未提供、多圖被 Phase 01 guard 拒絕、output 是檔案的設定錯誤直到推論後才發現。缺／非目錄 input、致命模型與單張覆蓋保留原行為已通過。未把預期 red tests 標為驗收 PASS。
- 已於 test-data/phase-02-cli-20260917/ 準備隔離真實圖片；fixtures.json 記原 frame hash／裁切座標／格式／各輸入 hash。預設案例 129×97 JPEG、故意損壞 PNG、127×95 TIFF；CPU 僅 32×28 PNG。沒有新資料下載或改原影片。

### 2026-09-17T20:30:29+08:00 — Phase 02 CLI 實作與真實批次驗收 Complete

- 前一步 `3fe61ed` 保存預期失敗測試。第一個 production patch 只改 `src/drone_sr/__main__.py`：獨立 --input／--output、穩定第一層列舉、單次載入模型、逐張錯誤隔離／成功才計數、GPU 名稱；寫入前判斷輸出目錄、同 stem 衝突、所有輸入的 path／symlink／hardlink 別名，沿用原子 write_png。每張結束釋放 result，下一張不保留前張 GPU output。沒有修改模型、I/O、依賴或新增 production 模組。
- 實際 WSL 專案根目錄命令：`.venv/bin/python -m unittest discover -s tests -p test_cli.py -v` **PASS 12／12，1.310 秒**；`.venv/bin/python -m unittest discover -s tests -p test_image_io.py -v` **PASS 7／7，0.032 秒**；`.venv/bin/python -m drone_sr --help` 只列 help／input／output，exit 0；`git diff --check` PASS。無 skipped。唯讀同階段 diff review 未發現阻擋問題；沒有因審查再擴大功能。
- 真實整合命令：`timeout 400 .venv/bin/python test-data/phase-02-cli-20260917/validate_cli.py`，整體 exit 0、約 8.51 秒；script 對每個子程序設 120 秒 timeout，只執行下列三次真正 CLI，沒有 mock／改模型或掃描參數。

| 案例／cwd（相對專案） | 子程序實際參數 | 裝置／結果 | 含啟動耗時 |
|---|---|---|---|
| `test-data/phase-02-cli-20260917/default run` | `.venv/bin/python -m drone_sr`（Python 使用專案絕對路徑） | cuda:0；Processed 2／Failed 1；exit 1 為預期壞圖結果 | 3.253 秒 |
| `test-data/phase-02-cli-20260917/runner location` | 同一 Python `-m drone_sr --input '../default run/input' --output '/home/minervamuses/drone-image-analysis/test-data/phase-02-cli-20260917/custom output'` | cuda:0；Processed 2／Failed 1；exit 1 為預期壞圖結果 | 2.801 秒 |
| `test-data/phase-02-cli-20260917/cpu run` | 同一 Python `-m drone_sr`；子程序 env `CUDA_VISIBLE_DEVICES=-1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1` | 真實 CPU；Processed 1／Failed 0；exit 0 | 2.110 秒 |

- GPU 兩次都以 `a_good.JPG → m_broken.PNG → z_good.TIFF` 順序執行；壞圖顯示 cannot identify image file，沒有輸出檔，之後 TIFF 成功。JPEG 129×97 → 516×388；TIFF 127×95 → 508×380；兩次介面產出的各 PNG SHA 相同：a_good `7d4eeb5df66edac8715f9ff98610d610b4af8859d41e7aee8c757f3ad6141af5`、z_good `edf3dbea185b7df5ef7b1d0ce80716081de02632862407937422b6eb0f35939e`。CPU tiny 32×28 → 128×112，SHA `90fd404e1d56f8889633313ac8a5a41339fb2e6ea1aeac33bf1970737afe22e7`。
- 原始圖／壞圖均與 fixtures.json 中 SHA 相同，原 frame SHA 不變；GPU 兩個輸出資料夾內，為本次驗收建立的舊 a_good.png 已替換成新 PNG，untouched.txt 的前後 hash 相同。真正相同模型可在其他 cwd 運行，證明 checkpoint 不隨資料夾參數改變。CLI tests 另覆蓋 input-only／output-only、五格式大小寫、同 stem 全失敗／其他成功、別名、儲存失敗保留舊檔與後續繼續、致命模型先停止。
- 人工開啟 a_good 原圖及兩個 GPU 成功 PNG，海面內容、反光位置、RGB 色彩正常；CPU tiny PNG 可開啟。viewer 不支援直接開 TIFF（工具回報 unsupported image），已用 Pillow 解碼成 `test-data/phase-02-cli-20260917/z_good_source_preview.png` 並 assert RGB bytes 完全相同，再開啟比對；preview SHA `096fbf05df7ad227ec5c3a39bc4b963811985c514fbbd78079aa4dbd5198ac05`。這是檢視工具限制，原始 TIFF 的真正 application 解碼／推論已通過，未修改輸入。
- 每張圖的來源 frame、crop box、格式、input SHA 存於該 evidence 目錄 `fixtures.json`；輸出絕對路徑／SHA／尺寸／CLI argv／cwd／env／退出碼／耗時存於 `validation.json`，console 為 `default-cli.txt`、`custom-cli.txt`、`cpu-cli.txt`；一次性 script 為 `validate_cli.py`。沒有全套重跑或額外效能實驗。
- Acceptance：兩種介面與 help **PASS**；真實 2 成功 1 失敗跑到底 **PASS**；輸入／模型／空目錄／壞圖既有與新增 checks **PASS**；原始／無關輸出／衝突／儲存失敗保護 **PASS**；真實 GPU 與極小真實 CPU 自動分支 **PASS**。Phase 02 In progress → Complete；README 同步已驗證介面與限制。
- 下一個符合依賴條件為 phase-03，尚未宣稱第二個 checkpoint 或 4K／tiling 通過。

### 2026-09-17T20:34:47+08:00 — Phase 03 唯讀準備與本輪整體核對

- Phase 02 由 `26bce17` 完成。依順序讀 phase-03；前置已滿足，models/ 目前只有 `.gitkeep`、選定 Compact 原檔與 model.pth 相對 symlink，没有 SwinIR。既有授權只涵蓋這個 Compact 下載，不視為第二 checkpoint 下載批准。
- 唯讀檢查已安裝 Spandrel 0.4.2 的 `architectures/SwinIR/__init__.py`：存在 SwinIRArch 與 ImageModelDescriptor 回傳路徑，scale／channels／size requirements 由 state_dict 推導；這只是實作準備，沒有 checkpoint 可供實際 descriptor、奇數尺寸或真實 PNG 驗證。沒有下載第二模型、改 model.pth、跑模型 sweep 或合成資料冒充相容性驗收。
- Phase 03 Not started → **Blocked**。最小缺項：一個來源／使用條件可追溯的 SwinIR RGB SR checkpoint 本機路徑，或對具體檔案的下載授權。取得前不標 Complete、不開始依賴它的 phase-04；目前固定使用已選定並驗證過的 Compact。沒有要求新增套件／環境。
- 本輪收尾依 PLANS 執行一次便宜完整軟體 suite：WSL 專案根目錄 `.venv/bin/python -m unittest discover -s tests -v`，**25／25 PASS、0.155 秒（unittest 計時；程序含 imports 約 4.11 秒）、exit 0、無 skipped**。此 suite 包含 mock correctness tests，真實 GPU／CPU 證據仍以上兩階段獨立記錄為準。

| GOALS 成功條件 | 本輪核對／實際限制 |
|---|---|
| 1 預設與指定資料夾、真實 PNG／摘要 | PASS：兩種真實批次，各 2 成功／1 故意壞圖，成功 PNG 開啟及來源對帳 |
| 2 Compact＋SwinIR 共用流程、单一預設 | 部分：正式 Compact 通過且現為指定候選；SwinIR 缺權重，未驗收 |
| 3 自動 GPU／CPU、明示裝置 | PASS：實際 CUDA 與隱藏 CUDA 後的 32×28 正式權重 CPU 分支均成功 |
| 4 RGB／float／BCHW／dtype/device／嚴格倍率尺寸 | PASS：focused checks 及真實 Compact 512×512、奇數尺寸 129×97／127×95、極小 CPU 尺寸均正確 |
| 5 自動 overlap tiling、所有邊界、真實接縫 | 未完成：phase-04 尚未開始，未執行完整 4K |
| 6 建立 output、原始與無關輸出保留、成功才覆蓋 | PASS：真實批次來源／無關 output hash 及覆蓋通過；同 stem／別名／儲存失敗 correctness checks 通過 |
| 7 致命錯誤、空輸入、壞圖繼續與計數 | PASS：真實負向／新增 CLI tests 與 2 成功 1 失敗完整批次證據；舊檔未被冒充成功 |
| 8 correctness tests 與可追溯 README | 當前範圍 PASS：25 tests、真實執行、版本／權重／來源／命令／限制已記錄；整體最終驗收尚缺第 2／5 項 |

- PLANS 整體完成標準尚未達成：Phase 01／02 Complete，03 Blocked，04 Not started。沒有將計畫、mock、skipped 或尚未執行部分当作完成。此次沒有新 dependencies、其他資料下載、push、分支／worktree 變更，也沒有修改 AGENTS.md。


### 2026-09-17T21:27:32+08:00 — Phase 03 恢復 preflight 與下載時間界線

- 使用者指示「用512的，繼續」，沿用討論中的 SwinIR-M real-world 4×，批准此 checkpoint 與 512×512 驗證；先前「缺模型選擇／下載授權」已由本次決定補足。每步 commit 授權沿用；未批准其他資料／權重／依賴。
- 唯讀 gate：WSL Ubuntu 24.04，Linux Bash／Git 2.43.0／Python 3.12.3，專案 `/home/minervamuses/drone-image-analysis`；main HEAD `064170e`，工作區乾淨。依序讀適用 AGENTS、GOALS、PLANS、build-log、phase-03、相關 inference／I/O／CLI／test_inference／pyproject／README；build/ 沒有 context 或 code_review 文件。首次 cat 使用錯誤 phase 檔名回報不存在，find 確認後改讀實際 phase-03-model-compatibility.md；沒有略過階段文件。
- `nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version,utilization.gpu --format=csv`：RTX 5070 Ti Laptop，12227 MiB total／10520 MiB free、driver 591.74、utilization 6%；`free -h` 約 30 GiB available；`df -h .` 約 842 GiB available。先前 512 約 4–6 GB VRAM 是粗估，尚無此 checkpoint 的本機峰值證據。
- 官方 GitHub API `https://api.github.com/repos/JingyunLiang/SwinIR/releases/tags/v0.0`，WSL Python stdlib urllib 讀取指定 asset：release id 48474885，asset id 44142419，檔名 `003_realSR_BSRGAN_DFO_s64w8_SwinIR-M_x4_GAN.pth`，**67,129,861 bytes**，created 2021-09-06T09:58:38Z、updated 09:58:42Z；digest=null，下載後只能先記本機 SHA，不能聲稱官方 SHA 驗證。
- 精確來源：`https://github.com/JingyunLiang/SwinIR/releases/download/v0.0/003_realSR_BSRGAN_DFO_s64w8_SwinIR-M_x4_GAN.pth`；官方 repository 的 `https://raw.githubusercontent.com/JingyunLiang/SwinIR/main/LICENSE` 本次讀到 Apache-2.0。web reader 未能開啟 API，改以上述 WSL stdlib 得到真實 metadata；未增加套件。
- 單次唯讀測速：WSL `python3 -`，`urllib.request.Request(asset_url, headers={'Range':'bytes=0-1048575'})`、urlopen timeout=20，read(1048576) 後關閉；HTTP 206、讀取 **1,048,576 bytes／22.683931 秒**，內容僅在記憶體，未保存部分權重。以含連線的速度线性粗估全檔約 **24.2 分鐘**；不能保證全程維持此速度。尚未啟動完整下載。
- 唯讀檢查已安裝 Spandrel 0.4.2：SwinIR loader 宣告 minimum=16、multiple_of=start_unshuffle**2、supports_half=False、tiling=DISCOURAGED；具體值仍須載入檔案确认。descriptor 先 padding／裁回，極小輸入先有限 reflect 再 replicate，SwinIR 本體另處理 window multiple；現有 production upscale 未見需要預先修改的具體缺口。
- 可執行的最小方案：一次下載僅此約 67.13 MB checkpoint，總下載上限 70 MB／30 分鐘、無自動重試，`.part` 完成 size／本機 SHA 才改名；約需 135 MB 額外磁碟包含輸出，無付費服務或依賴。以既有 512 真實圖走真正 CLI 至獨立目錄，另以相同 production 路徑量測 VRAM；合成 17×19 與 1×1 tensors 只驗尺寸／padding。每個推論程序上限 120 秒，預估推論與檢查數分鐘內，不跑模型 sweep。暫時切換自有 model.pth symlink，finally 恢復 Compact，保留兩顆原始 checkpoint／Compact 既有輸出。
- 預定 acceptance：真實 512→2048 RGB PNG 開啟、原始 hash 不變；上述尺寸嚴格乘 scale、finite／無 padding 殘留；phase-03 指定 inference focused tests；共用 CLI／批次既有證據，無程式修改則不重跑 Compact。若都通過，以先前使用者指定且已驗證的 Compact 保持候選，不把海面觀察當畫質排名。
- **Phase 03 維持 Blocked，但最小缺項更正為下載時間授權**：AGENTS「預估超過約十分鐘的工作」及 PLANS「停止並取得所需決策／授權」要求先說明具體成本。上述材料與驗證方案已準備完成，等待是否批准最多 30 分鐘的單檔下載。Phase 04 仍 Not started，沒有把唯讀準備／估計記為實際 SwinIR 推論通過。沒有修改 production／測試，故本步只執行文件差異檢查。


### 2026-09-17T21:28:28+08:00 — Phase 03 不依賴下載的 focused check

- 前一步 preflight 提交 `ebe91c2`；已提出最多 30 分鐘／70 MB、只下載指定 checkpoint 一次的時間授權問題，回答前不啟動完整下載。
- 實際命令：WSL 專案根目錄 `.venv/bin/python -m unittest discover -s tests -p test_inference.py -v`；**6／6 PASS**，unittest 0.061 秒、程序含 imports 約 4.58 秒，exit 0、無 skipped。這是既有 toy descriptor／mock 的裝置與尺寸 correctness，加上真正壞 checkpoint loader 錯誤；不是 SwinIR 預訓練推論。沒有 production 修改或完整 suite 重跑。
- 本輪逐項沿用前次 GOALS 核對：#1 兩種批次真實輸出、#3 GPU／極小 CPU、#4 I/O 與 Compact 真實尺寸、#6 原始／其他輸出保護、#7 错誤與摘要均有既有 PASS 證據；#2 仍缺實際 SwinIR；#5 分塊未開始；#8 現階段測試／README 可追溯，但整體驗收仍未完成。PLANS 要求每階段 Complete 尚未滿足，Phase 03 Blocked／04 Not started。沒有新增圖片或新推論結果，Compact 現有證據保持有效。


### 2026-09-17T21:39:00+08:00 — Phase 03 下載與計劃內工作授權已確認

- 使用者批准最多 30 分鐘／70 MB 單次指定權重下載，並明確授權計劃內工作一律執行、不再詢問。PLANS 已記錄最新授權；仍保留階段依賴、失敗次數、資料保護及原非目標。Phase 03 Blocked → In progress。
- 新任務 gate：讀 root AGENTS，依序核對 GOALS／PLANS／build-log／phase-03 與實際 inference；main `03e1202`、git status 乾淨；WSL Linux shell／Git／Python 一致。GPU 12227 MiB total／10518 MiB free、driver 591.74；RAM 約 30 GiB available、磁碟約 842 GiB free。來源、大小、預定檢查與成本沿用上一節，沒有新材料矛盾；上輪 6／6 focused tests 有效，不無故重跑。
- 下一步只下載已選定 SwinIR-M 原檔至 models/，本次上限 1800 秒；每個真實推論程序上限 120 秒。已完成來源及共用路徑唯讀準備，現在可執行，不再以先前缺授權狀態停止。


### 2026-09-17T21:42:48+08:00 — Phase 03 指定 SwinIR 權重就緒

- 前一步 `432af28` 記錄完整計劃授權。WSL 專案根目錄實際執行 `python3 -u test-data/phase-03-swinir-20260917/download.py`，一次 HTTP 200 下載 **67,129,861 bytes／166.952 秒**、exit 0。前段慢，後段提速；先前約 24 分鐘只是小量測速估計，實際未超過 30 分鐘上限，也未重試。只取得指定 SwinIR checkpoint，沒有其他資料或權重。
- 本機 `models/003_realSR_BSRGAN_DFO_s64w8_SwinIR-M_x4_GAN.pth`；SHA-256 **`b9afb61e65e04eb7f8aba5095d070bbe9af28df76acd0c9405aeb33b814bcfc6`**，下載時計算後又重新讀檔核對相同；大小符合官方 API，官方 digest=null，未聲稱官方 hash 比對。`.part` 完成後改名，完整 provenance 在同目錄 provenance.json／download.py。
- 既有 Compact 原檔、model.pth 相對 symlink 保留；尚未模型 forward。一次性 validate_swinir.py 已準備、Python compile 語法檢查通過；採父程序 try/finally 管理模型切換，子程序各 timeout 120 秒，先真實 CLI 再獨立量測及兩個最小 tensor 尺寸案例。不把腳本準備記成驗收成功。


### 2026-09-17T21:46:04+08:00 — Phase 03 真實 SwinIR 相容性 Complete

- 前一步 `abb5c03` 保存官方權重來源與下載證據。真實驗證前審查一次性腳本，修正 symlink 切換／還原非原子、timeout console 未保存、還原確認前可能記 PASS 三項問題；production code／tests／依賴均未變。脚本由父層 try/finally、暫存相對 symlink＋os.replace 管理，僅還原仍指向本次模型的入口；子程序 timeout 保存可取得 console。這是驗證準備修正，未發生真實推論失敗。
- 實際命令：WSL 專案根目錄 `.venv/bin/python -u test-data/phase-03-swinir-20260917/validate_swinir.py`，exit 0。先真正 CLI：`.venv/bin/python -m drone_sr --input /home/minervamuses/drone-image-analysis/test-data/phase-03-swinir-20260917/input --output /home/minervamuses/drone-image-analysis/test-data/phase-03-swinir-20260917/output`，exit 0、Device cuda:0／RTX 5070 Ti Laptop、Processed 1／Failed 0，含啟動 **11.641 秒**。
- 模型身分由實際 descriptor 確認：SwinIR／model class SwinIR、SR／RGB 3→3／scale 4、11,715,559 parameters、minimum=16／multiple_of=1／square=False、tiling=DISCOURAGED、supports_half=False／supports_bfloat16=True；本次使用 cuda:0／float32／eval。詳見 descriptor.json。第三方 torch.meshgrid 發出未來需要 indexing 參數的 UserWarning，兩個程序都成功；沒有靜默抑制或為 warning 修改依賴。
- 同一 production load_model/read_image/upscale 的独立量測子程序 `validate_swinir.py --measure` exit 0、含啟動 9.467 秒。無 warmup／sweep：同步 GPU 計時的上傳＋推論 **3.242450 秒**，load/read/infer 不含 imports 6.127637 秒；載入至 forward 結束 PyTorch peak allocated **4,643,337,216 bytes（4.324 GiB）**、reserved **7,140,802,560 bytes（6.650 GiB）**。不包含 CUDA context／其他程序或後續 finite／PNG 編碼，不當作整卡 VRAM 峰值。先前 4–6 GB 僅粗估，本節實測替代。
- 輸入是 phase-01 同一真實 512×512 crop 的隔離副本，SHA `ad7d8815928ea78bb2243af8639541216e83a7444d78272d91451a2d7dd63faa`；輸出 `test-data/phase-03-swinir-20260917/output/whaledrone_seek10s_x1536_y768_512.png`，RGB PNG **2048×2048**、3,853,525 bytes，SHA **`11ba292b3382c55eca28e0edd6450277da512acbbd087a53702eb894db181f94`**。量測結果依 production clamp／round 得到的 uint8 與真正 CLI 每像素相同（max difference 0）。
- 同一正式 SwinIR／GPU／FP32 的兩個合成 tensor，只驗尺寸：H×W **17×19 → 68×76**（0.898 秒，奇數／非 window8 倍數，但符合 descriptor minimum／multiple）；**1×1 → 4×4**（0.103 秒，真正低於 minimum，reflect／replicate 補邊後裁回）。兩者 finite／dtype／device 正確，沒有殘留 padding；不以此宣稱 SR 畫質。
- 原始 crop、frame、Compact checkpoint／既有 PNG hash 前後相同；SwinIR hash 重核對一致；model.pth 已恢復 `realesr-general-x4v3.pth`。完整 argv、cwd、各 exit／elapsed、hash 為 validation.json，量測為 measurements.json，console 為 cli.txt／measure-console.txt；所有新圖可對應該目錄 input/output 與既有 crop 座標。
- 人工開啟原圖與本次 SwinIR PNG：波紋／亮點相對位置、藍綠色、朝向正常，無空白或殘留邊框；細紋平滑，沒有可辨識鯨魚，不宣稱還原真實新增細節／畫質排名。
- Acceptance：Compact 既有真實圖＋本次 SwinIR 同一路徑 **PASS**；不符尺寸要求／裁回 **PASS**；CLI 換模型成功且 production 未變，重用 phase-02 批次／錯誤及本階段 6／6 focused tests **PASS**；保持使用者先前指定、資源較低且已跑通的 Compact 作候選 **PASS**。Phase 03 In progress → Complete；phase-04 仍須驗兩模型最小 tiled 與候選大圖，未推定通過。
- 新 metadata 對下游有實質影響：Spandrel 的 DISCOURAGED 表示可分塊但可能受上下文影響，不能當 SUPPORTED。已記 context 並補 phase-04：查原因、兩模型最小 direct/tile 視覺確認，Compact 作大圖候選；不增加 architecture 分支或全圖 SwinIR sweep。
