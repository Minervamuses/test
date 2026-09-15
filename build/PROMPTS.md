# build — 啟動與續作提示

以下供使用者日後明確啟動實作時複製。建立計劃本身不會執行它們。

## 啟動／續作（Start / Resume）

~~~text
請開始或繼續專案根目錄 build/ 的實作計劃。

先確認專案與執行環境，依序讀取：
1. 所有適用的 AGENTS.md。
2. build/GOALS.md。
3. build/PLANS.md。
4. build/build-log.md。
5. 依 build/PLANS.md 順序，第一個不是 Complete 且所有依賴都 Complete 的 build/phases/phase-*.md。
6. 若存在，與該階段／前置階段相關的 build/context/、build/code_review/ 文件。
7. 該階段相關的實際程式、設定、測試。

以 build/build-log.md 為狀態唯一來源，對照 live repository 與使用者既有變更。實際觀察優先於過時敘述；矛盾先追加更正並恢復可驗證基線，不覆寫使用者修改。

依 build/PLANS.md 的自主模式及授權範圍執行。本提示授權階段內程式、必要測試與文件實作；尚未批准的依賴／環境提案按該文件完成唯讀準備後處理，不自動當作已批准。

每次只實作所選階段：
1. 唯讀 preflight，核對材料、前置、範圍、非目標、預定檢查與停止條件。
2. 缺必要決策／材料時記 Blocked 及最小缺項；先做不依賴缺項的準備，不能將未驗證標為通過。
3. 僅實作本階段。適用時先用最小失敗測試辨識問題，再最小修正，不擴大重構。
4. 執行必要 focused、代表整合與人工驗收；每項 acceptance 都須有觀察證據。
5. 先處理失敗，再推進；必要檢查失敗或未完成不得進依賴階段，遵守 PLANS.md 的失敗次數與昂貴工作界線。
6. 在 build/build-log.md 記實際命令、環境、輸入／輸出、結果、失敗及限制，每張圖片與結果可追溯。
7. 重要發現才建立 build/context/phase-NN-context.md，真正審查才建立 build/code_review/phase-NN-review.md。
8. 新證據推翻後續計劃，先修 build/PLANS.md 與受影響未開始 phase，保留既有完成／失敗證據。
9. 完成並記錄本階段後，繼續下一個符合依賴條件的階段，直到整體完成或觸及 PLANS.md 停止條件。

最後逐條核對 build/GOALS.md 與 build/PLANS.md 整體完成標準，回報實際結果和未驗證部分。不得把計劃、mock 或 skipped 檢查當作真實推論完成。
~~~

## 只執行單一階段

~~~text
請只執行 build/ 計劃中我在本訊息指定的單一階段。採 build/PROMPTS.md 的啟動／續作讀取順序，確認 build/build-log.md 的前置均 Complete。未指定時，從 build/PLANS.md 選第一個符合依賴的未完成階段。

先唯讀 preflight，再依 build/PLANS.md 授權做本階段必要實作與驗證，更新 build/build-log.md 與必要 context。完成或遇停止條件即停，不展開後續。
~~~

## 驗證或審查

~~~text
請審查 build/ 計劃實際完成程度。先讀 build/GOALS.md、build/PLANS.md、build/build-log.md、相關 build/phases/ 與已存在 context／code_review，再看 live files 和實際變更。

將 acceptance 逐條對應可重現證據，特別檢查模型真實推論與 output 圖片，不只相信 log。重用有效證據，只補必要且已授權的便宜驗證；昂貴／不可用檢查按 PLANS.md 處理。這是審查，不授權修改程式。記錄實際 findings，區分未通過與未執行。
~~~

## 證據改變後修訂計劃

~~~text
請修訂 build/ 中被新證據推翻的計劃。先讀 build/GOALS.md、build/PLANS.md、build/build-log.md、受影響 phase、context 與 live repository。指出具體矛盾及下游影響，只改必要 roadmap 和未開始 phase，保留完成與失敗歷史。

除非使用者明確改變要求，保持 GOALS.md 穩定目標。追加更正，檢查連結與依賴，再依 build/PROMPTS.md 的啟動／續作流程唯讀 walkthrough。本次只修計劃，不開始實作。
~~~
