# build — 執行計劃

## 概要

- 計劃根目錄：專案根目錄的 build/。
- 目標：[GOALS.md](GOALS.md)。
- 專案形態：minimal，單用途本機 CLI。
- 風險：medium；未知為 GPU／checkpoint 相容性與大圖分塊座標，無遠端服務。
- 執行模式：**Autonomous within authorization envelope**。使用者另行啟動實作後，在已批准範圍依序實作及驗證，不逐階段重複詢問普通可逆操作。
- 四階段分別關閉單張推論、批次介面、第二模型相容性、大圖與最終驗收；各階段立即驗證，不把測試全部留到最後。

## 資訊唯一來源

| 資訊 | 所屬檔案 |
|---|---|
| 目標、介面、限制、非目標 | GOALS.md |
| 順序、依賴、授權、停止與修訂 | PLANS.md |
| 啟動／續作提示 | PROMPTS.md |
| 各階段工作與預定檢查 | phases/phase-*.md |
| 實作狀態與觀察證據 | build-log.md |
| 重要實作發現 | context/phase-NN-context.md，必要時才建立 |
| 實際程式審查 | code_review/phase-NN-review.md，審查時才建立 |

採 phases/ 存放階段文件，避免 build/build/ 重複命名。初始不建立 context/ 或 code_review/。

## 已確認專案基線

以下是 2026-09-15 計劃撰寫的唯讀觀察，並非 SR 實作證據：

- /home/minervamuses/drone-image-analysis 只有 AGENTS.md；find . -maxdepth 3 -type f 也只有此檔。無程式、manifest、測試、圖片、權重或既有計劃。
- git status --short 回報非 Git repository；沒有 branch／worktree 或既有 diff。不得為計劃驗證而 git init。
- 透過 wsl.exe -d Ubuntu-24.04 進入 Linux，使用者 minervamuses；bash、git、python3 位於 /usr/bin。Python 3.12.3、系統 pip 24.0，未發現 uv；WSL 無 rg，可改用 find 局部搜尋。
- 此系統 Python 的 pip show torch spandrel Pillow 未找到三個套件；其他環境是否已有依賴未知。
- nvidia-smi：NVIDIA GeForce RTX 5070 Ti Laptop GPU，VRAM 12227 MiB，當時空閒 10854 MiB，driver 591.74。
- free -h：RAM 31 GiB、當時 available 約 30 GiB、swap 8 GiB。df -h .：可用約 842 GiB。這些會變動，推論前重查，不能據此宣稱 PyTorch CUDA 可用。
- 初始 AGENTS.md SHA-256：7929b09ceb31e9703380e6225ef7aad9d9141ff6fc830949676f7f024daf7629。本次只新增此計劃的 8 個 Markdown 檔。

2026-09-15 續作更正：live repository 已由使用者初始化於 main，原有 9 個暫存文件已依本輪「每一步皆需 commit」授權原樣提交為 `d203598`。上列「非 Git repository」是歷史觀察，續作基線與證據以 build-log.md 為準；不再初始化 Git。

官方專案列出兩個要求架構；descriptor 文件提供尺寸 metadata、自動 padding 與輸出裁回。因此優先使用 descriptor，實作時仍須核對安裝版本並實測。[Spandrel 官方專案](https://github.com/chaiNNer-org/spandrel)、[ImageModelDescriptor 文件](https://chainner.app/spandrel/spandrel.ImageModelDescriptor.html)。

## 授權與停止條件

### 本次授權

只建立四個核心文件及四個階段 Markdown。程式、測試、README、依賴、權重及環境均屬後續實作，不在本次執行。

### 2026-09-15 本輪實作授權補充

使用者已啟動實作並授權每個完成步驟 commit；未授權 push、切分支或 worktree 變更。使用者另要求「先跳過，把框架弄起來，我之後再補權重跟資料」：先完成 phase-01 不依賴真實材料的程式與 correctness checks。真實圖片／預訓練權重驗收延後，不以合成資料或 mock 取代 Complete；框架準備完成後記 Blocked，未滿足前置不進 phase-02。依賴／環境仍須按下節具體提案取得批准。

### 實作啟動後的常規範圍

- 修改當前階段必要程式，加入少量直接驗證需求的測試，跑便宜本機檢查。
- 建立 GOALS.md 已指定的資料夾介面、PNG 與簡潔摘要，依其規則覆蓋本次產出。
- 預計使用 src/drone_sr/，必要職責對應 __main__.py、model.py、image_io.py、inference.py、tiling.py 及 __init__.py；不要求空模組，按需要採最少檔案。
- 維護 build-log.md、必要 context 及被新證據影響的未開始階段；只使用局部暫存，不修改原始樣本。
- 測試優先標準庫 unittest，不建立自製框架。測試隨功能實作加入。

### 依賴與環境提案

最小提案是隔離 .venv、pip、pyproject.toml；正式依賴 torch、spandrel、Pillow，另有必要標準 packaging 建置依賴。phase-01 查核版本、PyTorch wheel 來源及建置 backend 後，提出一次具體清單及下載量、磁碟／安裝時間估計或未知。

計劃文件本身不是安裝批准。若後續啟動已明確批准該清單，沿用授權；否則依 AGENTS.md 在安裝或寫入環境／manifest 前取得確認。先做完唯讀查核與可審查清單，不逐個普通程式步驟重複提問。超出清單的新依賴／環境變更再取得所需授權。

### 停止並取得所需決策／授權

- 目標、非目標、公共介面或資料處理需超出已批准範圍。
- AGENTS.md 所列尚未批准的依賴／環境、服務／並行模型或重大架構變更。
- 缺真實樣本／權重／必要硬體證據，無法完成當前驗收：記錄缺項與最小下一步，不能標 Complete。
- 預期超過約十分鐘、全資料集、反覆完整 suite、模型／GPU 掃描、付費／雲端服務：先說明具體需求與成本。
- 兩次聚焦修正仍失敗，或一次昂貴嘗試無效：停止擴大，回報證據、未解原因與最小下一步。
- commit、push、merge、rebase、切分支、修改 worktree、外部寫入、credentials 或破壞資料，須額外明確授權。禁止修改任何 AGENTS.md。

使用者最新要求及既有授權優先，不把一般建議擴張成額外審批。

## 階段路線圖

| 階段 | 可觀察結果 | 依賴 | 階段文件 |
|---|---|---|---|
| 01 | 真實單張經 Compact／Spandrel 產生正確 PNG | 無 | [phase-01](phases/phase-01-single-image.md) |
| 02 | 預設與 args 批次、自動 device、錯誤隔離及摘要 | 01 | [phase-02](phases/phase-02-folder-cli.md) |
| 03 | 換 SwinIR 後同一流程可用，選定預設候選 | 02 | [phase-03](phases/phase-03-model-compatibility.md) |
| 04 | 自動 tile、邊界正確、真實驗收與 README | 03 | [phase-04](phases/phase-04-tiling-acceptance.md) |

狀態僅由 build-log.md 保存。phase-01 就採 descriptor；phase-03 驗證既有通路。phase-03 候選通過 phase-04 才成為交付預設。

## 預定驗證命令的地位

目前沒有已建立或已驗證的 application test／build 指令。各 phase 的 unittest 命令是**新專案預定介面**，不是從既有程式庫找到或已執行的命令。

phase-01 工具鏈建立後，根據實際 pyproject.toml、README、tests/ 確認並執行最小命令，再寫入 build-log.md。若佈局改變，先修受影響未開始 phase，不把不存在的命令當證據。

命令假設在專案根目錄，已啟用經批准的 Linux .venv；Windows Agent 透過 wsl.exe -d Ubuntu-24.04 -- bash -lc 進入此環境。使用者命令維持 python -m drone_sr。

## 計劃維護與失敗處理

- 開始／恢復先核對 live files、使用者變更與 build-log.md，不依賴前次聊天。
- 必要檢查失敗或缺證據，不開始依賴階段。先診斷，只修當前原因。
- 新證據推翻後續假設時，先修 PLANS.md 與受影響未開始 phase。已完成歷史保留，build-log.md 追加更正。
- 重要發現才建立 context/phase-NN-context.md，包含來源、理由及下游影響。
- GOALS.md 的穩定目標只依使用者明確新決定更新。恢復以修正局部變更為主，不清除使用者資料或整個 output。

## 整體完成標準

每階段在 build-log.md 均有 Complete 及 acceptance 對應證據。GOALS.md 每項成功條件均可驗證；真實圖片、兩 checkpoint、大圖視覺檢查不得標 skipped 後聲稱完成。

最小代表批次驗證預設／指定資料夾、原始檔保留、overwrite、錯誤隔離與摘要。便宜完整軟體 suite 收尾一次；模型驗收另用最小樣本，不能暗藏在每次 suite。README 只寫已驗證範圍，清楚記錄剩餘限制。完成即停止。
