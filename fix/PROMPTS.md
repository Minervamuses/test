# fix — 啟動與續作提示

以下供使用者日後明確啟動實作時複製。建立計劃本身不會執行它們。

## 啟動／續作（Start / Resume）

~~~text
請開始或繼續專案根目錄 fix/ 的修正計劃。

先確認專案與執行環境，依序讀取：
1. 所有適用的 AGENTS.md。
2. fix/GOALS.md。
3. fix/PLANS.md。
4. fix/build-log.md。
5. 依 fix/PLANS.md 的順序，第一個狀態不是 Complete 且所有依賴都 Complete 的 fix/phases/phase-*.md。
6. 若存在，與該階段或其前置階段相關的 fix/context/、fix/code_review/ 文件。
7. 該階段實際相關的程式與測試：src/drone_sr/image_io.py、src/drone_sr/__main__.py、tests/test_image_io.py、README.md。

以 fix/build-log.md 為狀態唯一來源，對照 live repository 與使用者既有變更。實際觀察優先於過時敘述；矛盾先追加更正並恢復可驗證基線，不覆寫使用者修改。

依 fix/PLANS.md 的自主模式與授權範圍執行。本提示授權階段範圍內的程式、測試與文件修改；超出範圍的依賴、環境、介面或 Git 操作仍須另外取得授權。禁止修改任何 AGENTS.md。

每次只實作所選階段：
1. 唯讀 preflight，重述本階段範圍、非目標、預定檢查與停止條件，並確認前置為 Complete。
2. 缺必要決策或素材時記 Blocked 與最小缺項；先做不依賴缺項的準備，不得把未驗證標為通過。
3. 僅實作本階段。先寫最小失敗測試辨識問題，再做最小修正，不擴大重構。
4. 執行本階段必要的 focused 與較廣檢查；每條 acceptance 都要有觀察證據。
5. 先處理失敗再推進；必要檢查失敗或未完成不得進入依賴階段。遵守 fix/PLANS.md 的失敗次數與昂貴工作界線。
6. 在 fix/build-log.md 記錄實際命令、環境、輸入／輸出、結果、失敗與限制。
7. 重要發現才建立 fix/context/phase-NN-context.md；真正執行審查才建立 fix/code_review/phase-NN-review.md。
8. 新證據推翻後續計劃時，先修 fix/PLANS.md 與受影響的未開始階段文件，保留既有完成與失敗證據。
9. 完成並記錄本階段後，繼續下一個符合依賴條件的階段，直到整體完成或觸及 fix/PLANS.md 的停止條件。

特別注意兩件已知事項，preflight 時必須重新確認而不是照抄：
- ImageOps.exif_transpose() 會使 n_frames 失真，放錯位置會靜默破壞多頁 TIFF 拒絕。
- 來源位深必須在任何觸發解碼或轉換的操作之前讀取，否則資訊已遺失。

最後逐條核對 fix/GOALS.md 的成功條件與 fix/PLANS.md 的整體完成標準，回報實際結果與未驗證部分。不得把計劃、mock 或 skipped 檢查當作真實證據。
~~~

## 只執行單一階段

~~~text
請只執行 fix/ 計劃中我在本訊息指定的單一階段。採 fix/PROMPTS.md 啟動／續作的讀取順序，並確認 fix/build-log.md 中該階段的前置均為 Complete。未指定時，從 fix/PLANS.md 選第一個符合依賴條件的未完成階段。

先唯讀 preflight，再依 fix/PLANS.md 的授權做本階段必要的實作與驗證，更新 fix/build-log.md 與必要的 context。完成或遇停止條件即停，不展開後續階段。
~~~

## 驗證或審查

~~~text
請審查 fix/ 計劃的實際完成程度。先讀 fix/GOALS.md、fix/PLANS.md、fix/build-log.md、相關 fix/phases/ 與已存在的 context／code_review，再看 live files 與實際變更。

將每條 acceptance 對應到可重現的證據。特別檢查：
- 八個 EXIF 方向是否逐像素正確，而不只是尺寸正確；鏡像案例（2、4）與 180 度（3）不會被只比尺寸的斷言漏掉。
- 16-bit 彩色是否真的被拒絕，且 fixture 是真正的高位深檔案（回頭解析 PNG IHDR 或 TIFF BitsPerSample 確認），不是 Pillow 轉出來的 8-bit。
- 多頁 TIFF 與 float 拒絕是否仍然有效。
- 既有 29 個測試的斷言有沒有被放寬。

重用有效證據，只補必要且已授權的便宜驗證。這是審查，不授權修改程式。記錄實際 findings，區分「未通過」與「未執行」。
~~~

## 證據改變後修訂計劃

~~~text
請修訂 fix/ 中被新證據推翻的計劃。先讀 fix/GOALS.md、fix/PLANS.md、fix/build-log.md、受影響的階段文件、context 與 live repository。指出具體矛盾與下游影響，只改必要的 roadmap 與未開始階段，保留完成與失敗歷史。

除非使用者明確改變要求，保持 fix/GOALS.md 的穩定目標。追加更正，檢查連結與依賴，再依 fix/PROMPTS.md 的啟動／續作流程做一次唯讀 walkthrough。本次只修計劃，不開始實作。
~~~

## 最終整合驗收

~~~text
請把 live repository 與觀察證據直接對照 fix/GOALS.md 的每項成功條件與 fix/PLANS.md 的整體完成標準。

執行代表性的端到端檢查與既有 regression：完整 unittest suite、一次真實小批次 CLI（確認原始檔雜湊不變、Processed／Failed 與退出碼符合預期）。核對 README 敘述與實際行為逐條一致。

記錄未解限制（未壓縮 TIFF 的 Pillow 上游缺陷、輸出檔 0600 權限、任何未能在本機驗證的項目）。必要證據缺席時不得宣告計劃完成。
~~~
