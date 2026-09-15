# build — Build Log

本檔是階段狀態與觀察證據唯一來源；計劃描述預期工作，本檔只記實際實作／驗證。

## 階段摘要

| 階段 | 狀態 | 開始 | 完成 | 證據 | 阻礙 |
|---|---|---|---|---|---|
| 01 — 單張推論 | Not started | — | — | — | 尚未進入實作 preflight |
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
