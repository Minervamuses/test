# evaluation — 執行計劃

## 概要

- **計劃根目錄：** 專案根目錄的 `evaluation/`。
- **目標：** [GOALS.md](GOALS.md)。
- **路線：** 先把不需要任何新依賴、也不需要模型的退化與 bicubic 基線做對並可觀察（01），再處理唯一的外部風險：`lpips` 依賴、權重下載與自行實作的度量正確性（02）。兩者都站穩之後才接上未修改的 SR pipeline（03），把三者組成每次新建紀錄的執行器與報告（04），最後用真實小樣本驗收、量成本、對齊文件（05）。
- **專案形態：** minimal。單用途本機 CLI，本次新增一個位於 `evaluation/` 的獨立工具，不動既有套件。
- **風險：medium。** 改動面積小且與主 pipeline 隔離，但有三個真實風險：（a）新依賴與需要下載的預訓練權重；（b）自行實作的 PSNR／SSIM 可能算出看似合理卻系統性偏差的數字；（c）評估流程最容易犯的錯是「兩條線其實不對等」——例如 bicubic 偷用到原圖、或某一邊多了一次縮放——而這種錯誤不會讓程式崩潰，只會讓結論失真。驗收設計以（c）為首要防線。
- **執行模式：Autonomous within authorization envelope。** 使用者啟動實作後，在下列授權範圍內依序實作與驗證，不為一般可逆操作重複詢問。

## 資訊唯一來源

| 資訊 | 所屬檔案 |
|---|---|
| 目標、成功條件、固定約定、限制、非目標 | `GOALS.md` |
| 順序、依賴、授權、停止條件、修訂規則 | `PLANS.md` |
| 啟動／續作提示 | `PROMPTS.md` |
| 各階段工作與預定檢查 | `phases/phase-*.md` |
| 實作狀態與觀察證據 | `build-log.md` |
| 重要實作發現 | `context/phase-NN-context.md`，必要時才建立 |
| 實際程式審查 | `code_review/phase-NN-review.md`，審查時才建立 |

沿用 `fix/` 的慣例，以 `phases/` 存放階段文件，避免 `evaluation/evaluation/` 重複命名。初始不建立 `context/` 或 `code_review/`。

## 已確認基線

以下為 2026-09-18 在專案 `.venv`（Python 3.12.3、Pillow 12.3.0、torch 2.11.0+cu128、numpy 2.5.3、spandrel 0.4.2）的**唯讀調查觀察**，不是本計劃的實作證據。未修改任何專案檔。

### 既有 pipeline 的可重用介面

- `src/drone_sr/image_io.py:24` `read_image(path) -> Tensor`：mode 白名單 → `n_frames` 檢查 → 容器層級位深檢查 → `ImageOps.exif_transpose` → `convert("RGB")` → float32 `[0,1]` BCHW。
- `src/drone_sr/image_io.py:41` `write_png(tensor, destination, source)`：驗證 BCHW／有限值、拒絕覆寫來源、`clamp(0,1)` 後轉 uint8，以暫存檔＋`os.replace` 原子寫入。輸出權限 0600。
- `src/drone_sr/inference.py:14` `load_model()`：固定讀 `models/model.pth`，驗證是 RGB SR 且 `scale > 1`，依 `torch.cuda.is_available()` 選 device。
- `src/drone_sr/inference.py:44` `upscale(image, descriptor)`：任一邊 > 512 走 `tiling.upscale_tiled`（核心 512、halo 32），否則整張推論。
- 以上四個函式可直接 import 使用，**評估工具靠 import 重用即可，不需要也不得修改它們**。

### 模型

- `models/model.pth` 是指向 `realesr-general-x4v3.pth` 的 symlink。實際 descriptor：`RealESRGAN Compact`、**scale = 4**、purpose `SR`、RGB 3→3、`tiling = SUPPORTED`。倍率符合本計劃要求的 4×，但仍須在執行時斷言，不可假定。

### 真實輸入

- `input/` 有 **738 張 `.JPG`、4 個 `.json`、2 個 `.txt`、0 張 PNG**，沒有子資料夾。
- 取樣三張皆為 **4056×3040、RGB、format `MPO`、EXIF Orientation = 1**。4056 與 3040 都是 4 的倍數，這批資料的 mod-crop 實際裁切量為 0。
- **關鍵發現：** MPO 的 `n_frames = 2`，實測 `drone_sr.read_image()` 對這批 JPG 全部拋出 `ValueError: Only single-frame images are supported`。
  - **後果：** 評估工具的「原圖讀取」**不能**直接呼叫 `read_image()`，否則現有 738 張全數被拒、樣本歸零。必須依 `GOALS.md`「固定的退化與放大契約」第 1 條，自行以 Pillow 讀取並取第一影格。
  - **這不是 pipeline 的缺陷，也不需要修它：** 本計劃中 pipeline 只會拿到步驟 3 產生的單影格 LR PNG，`read_image()` 的嚴格檢查在它該把關的地方仍然成立。

### 度量依賴

- `.venv` **沒有** `lpips`、`torchmetrics`、`scikit-image`、`piq`。`numpy 2.5.3` 與 `torchvision 0.26.0+cu128` 已存在。
- 因此 PSNR／SSIM 必須自行實作，LPIPS 需要安裝套件並取得預訓練權重（需網路）。

### 資源

- **裝置可見性（2026-09-19 修正）：** 使用者的一般 WSL shell `torch.cuda.is_available()` 為 **True**（`NVIDIA GeForce RTX 5070 Ti Laptop GPU`）；coding agent 的沙箱 session 內為 **False**（`nvidia-smi` → `GPU access blocked by the operating system`、`/dev/dxg` 不存在、`device_count()` 為 0）。2026-09-18 記錄的 False 是沙箱結果，不是本機能力。權威敘述見 `GOALS.md`「授權限制」。
- 沙箱 CPU 上單次 512×512 → 2048×2048 的 Compact forward 量測為 **2.26 秒**。`README.md:122` 記錄同類案例的 **GPU** 上傳＋推論為 **0.220 秒**（PyTorch 峰值 allocated 約 264 MiB），約快一個量級。
- 推估（**未實測，僅供排程參考，不得當成證據**）：4056×3040 原圖 → LR 1014×760 → 分成 4 塊推論。**依裝置分兩套：** CPU 路徑 SR 線每張約十餘秒；GPU 路徑顯著更快，實際數字由 phase-03 在交付裝置上量測。LPIPS 在 4056×3040 全尺寸影像上的成本完全未知，由 phase-02 在交付裝置上實測；GPU 路徑的主要風險是 12227 MiB VRAM 而非耗時。
- **所有可對外引用的耗時、峰值 RSS、峰值 VRAM 與 device 都必須在使用者的 shell 量測。** 沙箱 session 內量到的是 CPU 數字，只能當成下限參考，不得當成交付環境的證據。

### 版本控制與既有狀態

- 分支 `main`，追蹤檔全部乾淨。`git status --short` 僅列出十二個沙箱裝置檔（`.bashrc`、`.claude/`、`.mcp.json` 等），與本計劃無關，**不得清理或提交**。
- `.gitignore:15` 已加入 `/evaluation/runs/`（2026-09-18 經使用者同意時套用），因此 run 產物不進入版本控制，而 `evaluation/` 的計劃文件與程式仍可被追蹤。實測 `git check-ignore -v evaluation/runs/<ts>/report.md` 命中該規則，`evaluation/GOALS.md` 未被忽略。
- 專案已有明確且**比「每階段一顆」更細**的 commit 慣例，實測自 `git log 5c4406a~1..8c1801b`（`fix/` 計劃的完整歷程）：
  - 每個 phase 的節奏是 `docs: start phase NN with <preflight>` → `test: define <acceptance>` → `fix:`／`feat:` 實作 → `docs: close phase NN with <evidence>`。
  - **一顆 commit 只碰一個關注點**：實測 `d5e87ca` 只動 `fix/build-log.md`、`01b982b` 只動 `tests/test_image_io.py`、`534e6eb` 只動 `src/drone_sr/image_io.py`、`05baa41` 只動 `fix/build-log.md`。
  - commit body 記當下的觀察數字，而非意圖：`01b982b` 寫「Red: 14 subtests fail」，`534e6eb` 寫「32 tests pass (29 existing plus 3 new)」與「byte-identical to pre-fix」。
  - 前綴採 Conventional Commits（`docs:`／`test:`／`feat:`／`fix:`／`chore:`），結尾帶 `Co-Authored-By` trailer。

## 執行授權

### 啟動後的常規範圍

使用者啟動實作後，下列動作不需重複詢問：

- 在 `evaluation/` 之下新增或修改評估程式、`evaluation/requirements.txt`，以及 `evaluation/runs/` 的產物。
- 安裝 `lpips` 到既有 `.venv`（使用者已於 2026-09-18 授權此單一套件），並把釘住的版本寫進 `evaluation/requirements.txt`。
- 下載 LPIPS 所需的預訓練權重（AlexNet backbone 與 lpips 線性層），並依專案既有慣例記錄來源 URL、檔案大小與 SHA-256。
- 在 `$TMPDIR` 或 `evaluation/runs/` 之下建立 fixture 與暫存檔。
- 執行本機便宜檢查，以及預估十分鐘以內的有界小樣本。
- `.gitignore` 的 `/evaluation/runs/` 忽略規則**已於 2026-09-18 經使用者明確同意並套用**（`.gitignore:15`），不需重做。這是本計劃唯一授權的 `evaluation/` 之外檔案變更；除此之外不得再改 `.gitignore`。
- 維護 `evaluation/build-log.md`、必要的 `evaluation/context/`，以及被新證據影響的未開始階段文件。
- 依「版本控制節奏與可追溯性」一節的切點 commit 到目前分支（不 push／merge／rebase／切分支）。

### 停止並取得所需授權

- 目標、成功條件、`GOALS.md` 的固定退化契約或固定度量約定需要改變。
- 需要修改 `src/drone_sr/**`、`tests/**`、`pyproject.toml`、`requirements-wsl.txt`、`models/**`、`input/**`、`output/**`。
- 需要 `lpips` 以外的任何新依賴。
- 需要對全量 738 張執行，或任何預估超過約十分鐘的工作。
- 網路無法取得 LPIPS 權重，或需要 credentials、付費服務、其他外部寫入。
- 需要 push、merge、rebase、切換分支或其他 worktree 變更。
- 兩次聚焦修正仍失敗，或一次昂貴嘗試無效：停止擴大，回報證據、未解原因與最小下一步。
- 缺必要證據而無法完成當前驗收：記 `Blocked` 與缺項，**不得標 `Complete`，也不得改用較弱的替代度量來讓階段看起來通過**。**唯一例外**是「GPU 交接協定」列出的三類項目（GPU 資源數字、GPU 決定性檢查、產生可引用數字的真實執行）：那些推遲到「待 GPU 補測」清單，不標 `Blocked`。正確性檢查缺證據一律不適用此例外。
- **禁止修改任何 `AGENTS.md`。**

### 專案指引

所有適用的 `AGENTS.md` 始終權威，本計劃不取代它。

## GPU 交接協定

交付裝置是 GPU，但 coding agent 的沙箱 session 看不到它（見 `GOALS.md`「授權限制」）。使用者於 2026-09-19 選定**批次交接**：沙箱內把所有能做的做完，需要 GPU 的項目集中成一次交接，而不是每個階段各自停下來等。

### 分工原則

- **正確性檢查全部在沙箱內完成。** 退化契約、兩條線對等性、PSNR／SSIM／LPIPS 的性質檢查都不需要 GPU；真實尺寸影像的正確性與目視檢查在成本允許時也應在沙箱內以 CPU 做完，只是那些數字屬於 CPU 批次。
- **只有三類項目需要使用者的 shell：** GPU 上的資源數字（耗時、峰值 RSS、峰值 VRAM）、GPU 上的決定性檢查、以及最後那次產生可對外引用數字的真實執行。
- 這三類項目**不標 `Blocked`**。`Blocked` 保留給真正無法推進的情況；等待一次預期中的交接不是被擋住。

### 待 GPU 補測清單

`build-log.md` 維護一份「待 GPU 補測」清單，每筆記：來源階段、確切要量什麼、沙箱內為何做不到、對應的驗收條件、狀態。

- 階段的沙箱部分全部通過時，該階段標 `Complete`，並在同一筆活動記錄裡列出它推遲到清單上的項目。**標 `Complete` 的前提是：推遲的只有上述三類項目，沒有任何正確性檢查被推遲。**
- 依賴階段可以在這種情況下開始。這是本計劃對「必要檢查未驗證時不開始依賴階段」的唯一例外，範圍僅限上述三類。
- 清單清空前，計劃**不得**標為整體完成（見「整體完成標準」）。

### 交接程序

1. **phase-02 結束時先給一支探測腳本**（約 30 秒）：只確認 LPIPS 在 4056×3040 上跑不跑得動與峰值 VRAM，不做完整量測。目的是不把資源風險留到最後才發現。使用者跑完貼回輸出。
2. **phase-05 產生一支自足腳本** `evaluation/gpu_checks/run_on_user_shell.sh`：一次做完清單上的所有項目——GPU 決定性檢查（含 `torch.backends.cudnn.benchmark = False`）、資源量測、小樣本真實執行與 `report.md` 產生。
3. 腳本必須**自足，且對專案既有檔案唯讀**：自行啟用 `.venv`、自行印出所用 device 與 `torch.cuda.get_device_name(0)`、把輸出同時寫到 stdout 與 run 目錄下的一份 log；不得修改 `src/`、`tests/`、`input/`、`output/`、`models/` 或任何 manifest。
4. 使用者在自己的終端機執行一次，把輸出貼回。
5. 由 agent 把數字寫進 `build-log.md`，每筆標明 **量測環境：使用者 shell**，並勾掉清單上對應項目。沙箱的 CPU 數字若同時存在，兩筆都保留並各自標明環境，不得互相取代。

### 腳本的驗證責任

交接腳本要先在沙箱內以 CPU 小尺寸跑過一次，確認不會出錯、輸出格式可讀。**不得把沒跑過的腳本交給使用者。** 沙箱那次執行不是交付證據，只是腳本的煙霧測試。

## 版本控制節奏與可追溯性

使用者於 2026-09-18 要求比「每階段一顆」更細的 commit，理由是出事時要能回溯與追查。以下規則取代任何「一個階段一顆 commit」的做法。

### 切點

每個 phase 至少拆成四段，實作本身再依該階段文件的「Commit 切點」繼續拆：

1. `docs: start phase NN — <preflight 觀察>`：只動 `evaluation/build-log.md`。preflight 沒產出值得記的觀察就跳過這顆。
2. `test: <定義驗收>`：只動該階段的檢查檔。body 記 red 的實際結果（幾項失敗、失敗原因）。
3. 一顆或多顆 `feat:`／`fix:`／`chore:`：**每個可獨立檢查的單元各一顆**，不是每階段一顆。切點見各階段文件。
4. `docs: close phase NN with <evidence>`：只動 `evaluation/build-log.md`（必要時加 `evaluation/context/`）。

### 規則

- **一顆 commit 只做一件事，且不跨邊界。** 評估程式、既有專案檔（`README.md`）、設定檔（`.gitignore`）各自成顆，不混在一起。這樣 revert 單一顆不會牽連無關的東西。
- **每顆 commit 後 repo 必須處於可檢查狀態**：`.venv/bin/python -m unittest discover -s tests` 仍通過。否則 `git bisect` 失去意義，也就達不到「出事能追查」的目的。
- **commit body 記當下觀察到的數字**，沿用既有慣例：red 記失敗數與原因，green 記通過數與關鍵量測（耗時、尺寸、雜湊是否一致）。不要寫打算做什麼。
- **`build-log.md` 每筆活動記錄要寫下對應的 commit hash**，讓文字證據與程式狀態能互相對照。
- **不得用 `--amend`、`rebase`、`squash` 改寫歷史。** 更正一律用新的 commit，保留失敗與修正的過程——那正是事後追查要看的東西。
- **commit 訊息用英文**（與 repo 既有歷史一致），計劃文件維持繁體中文。
- 產物不會污染歷史：`.gitignore:15` 已排除 `evaluation/runs/`。

### 本計劃的核心追溯鏈

phase-04 要求每份 `report.md` 的標頭記錄 `git rev-parse HEAD`。配合上述切點，任何一個可疑的數字都能沿著

`report.md 的 commit hash` → `git show` 該顆 → `build-log.md` 同 hash 的活動記錄 → 該 phase 的驗收條件

追回到「是哪一段程式、在哪個觀察證據下產生了這個數字」。這條鏈是本節規則存在的理由；任何讓它斷掉的 commit 方式都不符合要求。

### 尚未提交的既有工作

計劃 bundle（`evaluation/` 九個檔案）與 `.gitignore` 的一行修改目前**還在 worktree 未提交**。依上述規則，它們應是分開的兩顆：一顆 `docs:` 放 bundle，一顆 `chore:` 放 `.gitignore`。

## 階段路線圖

| 階段 | 可觀察結果 | 依賴 | 階段文件 |
|---|---|---|---|
| 01 | 從原圖產生 LR PNG 與 bicubic PNG，尺寸精確對齊，且 bicubic 可觀察地來自磁碟上的 LR 檔 | 無 | [phase-01](phases/phase-01-degradation-and-bicubic.md) |
| 02 | PSNR／SSIM／LPIPS 三個度量可用，且各自通過性質檢查與決定性檢查 | 無 | [phase-02](phases/phase-02-metrics-and-lpips.md) |
| 03 | SR 線由未修改的 `drone_sr` 從同一個 LR PNG 產出，尺寸等同真值，pipeline 逐位元未變 | 01 | [phase-03](phases/phase-03-sr-line.md) |
| 04 | 一次執行產生一個新的 run 目錄與一份逐張＋平均的 `report.md`，舊紀錄不受影響 | 01、02、03 | [phase-04](phases/phase-04-runner-and-report.md) |
| 05 | 真實小樣本跑完並目視檢查，成本已量測，文件與實際行為一致 | 04 | [phase-05](phases/phase-05-acceptance-and-docs.md) |

狀態僅由 `build-log.md` 保存。

## 依賴與排序說明

- **01 與 02 彼此獨立**，可任一先做。預設依編號順序，因為 01 不需要網路也不需要新依賴，能最快確立整個比較的骨架；若 01 卡住而網路可用，先做 02 是合理的調整，在 `build-log.md` 記明即可。
- **03 依賴 01**，因為 SR 線的輸入就是 01 寫出的 LR PNG。在 01 的尺寸與來源證據成立之前接 SR，會讓「兩條線是否對等」無法被單獨診斷。
- **04 依賴 01、02、03 全部完成。** 04 只做組裝、run 目錄管理與報告，不得在 04 才第一次驗證度量或退化是否正確；那樣一旦數字有問題，將無法判斷是哪一層出錯。
- **05 依賴 04**，且是唯一會產生「可對外引用的數字」的階段。全量執行不在 05 的授權範圍內。

## 計劃維護與失敗處理

- 開始／恢復先核對 live files、使用者既有變更與 `build-log.md`，不依賴前次對話。
- 必要檢查失敗或缺證據，不開始依賴階段。先診斷，只修當前原因。
- 新證據推翻後續假設時，先修 `PLANS.md` 與受影響的未開始階段文件，再繼續實作。
- 已完成歷史保留，`build-log.md` 以追加方式更正，不抹除影響後續理解的失敗紀錄。
- 重要發現才建立 `context/phase-NN-context.md`，包含來源、理由與下游影響。
- `GOALS.md` 的穩定目標與固定約定只依使用者明確新決定更新。**特別是：若實測數字不如預期，不得回頭調整退化流程或度量約定來改善分數**；那是改變實驗，不是修 bug。

## 整體完成標準

- [ ] 五個階段在 `build-log.md` 均為 `Complete` 且有對應觀察證據。
- [ ] `build-log.md` 的「待 GPU 補測」清單已清空：每項都有在使用者 shell 量到的數字，且標明量測環境。
- [ ] `GOALS.md` 每項成功條件都有觀察依據。
- [ ] 兩條線對等性有直接證據：bicubic 輸出可被獨立從 LR 檔重算出來，且 SR 與 bicubic 的輸入為同一個檔案。
- [ ] 一次真實小樣本執行完成，逐張與平均數字、執行環境與參數都在 `report.md` 內。
- [ ] 連續兩次執行產生兩個獨立 run 目錄，先前紀錄內容未變。
- [ ] `src/drone_sr/`、`tests/`、`pyproject.toml`、`requirements-wsl.txt`、`input/`、`output/`、`models/` 經雜湊或 `git status` 確認未變動。
- [ ] `README.md` 中「不計算 PSNR／SSIM」的範圍敘述與實際情況一致。
- [ ] 剩餘限制明確記錄：全量資料集未跑、GPU 路徑未驗證、真值來自 JPEG、RGB 而非 Y 通道、SSIM 交叉核對狀態。
- [ ] 完成即停止，不展開後續畫質優化或模型比較。
