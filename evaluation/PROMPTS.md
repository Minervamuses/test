# evaluation — 可重複使用的提示

## 啟動或續作整體執行

請執行專案根目錄 `evaluation/` 的長期計劃。

動任何檔案之前，先讀：

1. 專案根目錄的 `AGENTS.md`；
2. `evaluation/GOALS.md`；
3. `evaluation/PLANS.md`；
4. `evaluation/build-log.md`；
5. 第一個狀態不是 `Complete`、且依賴階段皆為 `Complete` 的階段文件（`evaluation/phases/`）；
6. 若存在，該階段相關的 `evaluation/context/` 與 `evaluation/code_review/`；
7. 該階段實際會碰到的程式與既有測試。

把這些文件與 live repository、目前 worktree 對照。`build-log.md` 是執行狀態的唯一來源；實際觀察到的行為，證據力高於過期的計劃敘述。

依 `PLANS.md` 的執行模式與授權範圍工作。

每個可執行的階段：

1. 先做唯讀 preflight，複述本階段範圍、非目標、預定檢查與停止條件；
2. 補齊必要前提，或把階段標為 `Blocked` 並寫明缺哪個決策或證據；
3. 只實作選定的階段；
4. 適用時採 red、green、refactor、verify；
5. 跑完該階段所有可執行的聚焦與較廣檢查；
6. 有必要檢查失敗或未驗證時，不開始依賴階段；
7. 把確切的觀察證據寫進 `evaluation/build-log.md`；
8. 只有重要發現或決策才建立／更新 `evaluation/context/phase-NN-context.md`；
9. 新證據推翻後續工作時，先更新 `PLANS.md` 與受影響的未開始階段文件，再繼續；
10. autonomous 模式下接續下一個可執行階段。

只在整體完成或觸及 `PLANS.md` 記載的停止條件時停下。未取得所需授權，不得 push、merge、rebase、切換分支、使用 credentials 或執行外部／破壞性操作。

本計劃最容易被違反的界線如下，在開始前務必回頭確認其權威敘述，不要憑印象執行：

- 哪些路徑不得修改、產物只能寫在哪裡：`GOALS.md`「必須保留的行為與不變式」與 `PLANS.md`「停止並取得所需授權」。
- 退化與度量的固定約定，以及「不得為了讓分數好看而更動它們」：`GOALS.md`「固定的退化與放大契約」、「固定的度量約定」與 `PLANS.md`「計劃維護與失敗處理」。
- 結果該怎麼解讀、報告不得省略什麼：`GOALS.md`「已知會影響結論解讀的性質」。
- 哪些項目需要使用者的 GPU、如何交接、為什麼不標 `Blocked`：`PLANS.md`「GPU 交接協定」與 `build-log.md`「待 GPU 補測」。沙箱 session 看不到本機 GPU，這不是錯誤，是預期狀態。
- 該在哪些切點 commit、commit body 要記什麼：`PLANS.md`「版本控制節奏與可追溯性」與各階段文件的「Commit 切點」。不要把一個 phase 做成一顆 commit。

## 執行單一階段

讀與「啟動或續作」相同的來源文件。先在 `build-log.md` 確認指定階段的依賴皆為 `Complete`，才選它。

做唯讀 preflight，只實作該階段已授權的範圍，跑它要求的檢查，記錄觀察證據，只在有重要發現時寫 context，然後停在該階段結束處。不要提前開始後續工作。

## 驗證一個階段

對照該階段文件、實際 diff、相關 context 與 `GOALS.md` 審查指定階段。

跑或檢視可取得的最強觀察證據。質疑驗收條件是否真的由證據推得，特別針對本計劃最容易出錯的地方：

- bicubic 線是否真的只從磁碟上的 LR PNG 讀入，而不是任何原圖衍生物；
- 兩條線的輸入是否為同一個檔案，且中間沒有多出任何一次縮放或有損編碼；
- 真值是否為 mod-crop 之後的原圖，且 SR 與 bicubic 輸出尺寸與它完全相同；
- 平均是否只涵蓋兩條線都成功的圖片，排除項是否寫明；
- 度量實作是否通過性質檢查，而不是只有「跑得出數字」。

只有實際做了審查才把發現寫進 `evaluation/code_review/`。不要把實作者的敘述當成證明。

## 依相反證據修正計劃

讀 `GOALS.md`、`PLANS.md`、`build-log.md`、受影響的階段文件、相關 context 與 live repository。

指出哪一項原本的理解被推翻、哪些未開始的階段受影響。除非使用者改變決定，否則保留穩定目標與固定約定。只改需要改的路線圖與未開始階段文件，並把這次計劃變更追加到 `build-log.md`。這個提示是純規劃工作，不要在同一次執行中實作被修正的階段。

## 最終整合審查

把 live repository 與觀察到的證據，逐條對照 `GOALS.md` 的成功條件與 `PLANS.md` 的整體完成標準。

跑一次代表性的端到端小樣本，確認：連續兩次執行產生兩個獨立 run 目錄且舊紀錄未變；`src/`、`tests/`、`input/`、`output/`、`models/` 與相關 manifest 未變動；報告內含逐張成績、平均、執行環境與參數，以及三個指標各自的結論與其解讀前提。

確認 `build-log.md` 的「待 GPU 補測」清單已清空，每項都有在使用者 shell 量到的數字與量測環境標記。

記錄未解限制。缺必要證據時不得宣告計劃完成。
