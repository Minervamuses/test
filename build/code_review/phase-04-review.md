# Phase 04 實際審查

審查範圍：`src/drone_sr/tiling.py`、`inference.py`、`tests/test_tiling.py`，以及 GOALS 對最終證據／README 的要求。子代理唯讀檢查，主代理執行驗證；時間與結果見 build-log。

- core 區域互斥，halo 按原始座標乘 descriptor.scale 裁回；未見缺列／重疊拼回問題。
- 大圖及完整結果在 CPU，當前 prediction 立即搬回 CPU／刪除引用；direct 與 tile 共用 _upscale_direct → descriptor，沒有模型名稱分支。
- 發現新 descriptor test fixture 使用 0..10，但 Spandrel 合約要求 [0,1] 且會 clamp。已只將 fixture /10，production 未為此繞過正常行為；之後 focused tests 通過。
- 最終證據審查確認：既有 CLI／CPU 部分可沿用，仍須真實兩模型 tile、完整4K、圖片檢視、hash及全suite。後續已由主代理補足，完整結果以 build-log 為準。
- README 明確保留 SwinIR DISCOURAGED／僅小例、CPU RAM 和檢視工具限制，不以一次執行宣稱效能優化或任意尺寸支援。

未發現需要擴大實作的阻擋問題；這份審查不取代真實圖片驗收。
