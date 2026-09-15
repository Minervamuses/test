# build — Build Log

本檔是階段狀態與觀察證據唯一來源；計劃描述預期工作，本檔只記實際實作／驗證。

## 階段摘要

| 階段 | 狀態 | 開始 | 完成 | 證據 | 阻礙 |
|---|---|---|---|---|---|
| 01 — 單張推論 | In progress | 2026-09-15 | — | 本檔 preflight、批准及框架準備 | 真實材料依使用者要求稍後補齊 |
| 02 — 資料夾 CLI | Not started | — | — | — | 尚未進入實作 preflight |
| 03 — 模型相容性 | Not started | — | — | — | 尚未進入實作 preflight |
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
