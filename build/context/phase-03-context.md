# Phase 03 — SwinIR descriptor 與下游分塊

真實 checkpoint／測量／狀態以 [build-log](../build-log.md) 為準。

Spandrel 0.4.2 實測 SwinIR-M real-world x4 descriptor 為 minimum=16、multiple=1、FP16 不支援、tiling=DISCOURAGED。已安裝 `spandrel/__helpers/model_descriptor.py` 對 DISCOURAGED 的定義是可分塊但可能因全圖上下文而出現 artifacts；不是禁止，也不是一般 SUPPORTED。模型有 window8 padding，descriptor 另處理最低尺寸及裁回。512 真實圖與 17×19／1×1 已通過現有共用路徑，無需架構專用 padding。

Phase 04 必須保留 metadata 語義、查看 direct/tile 同位置真實輸出；不能從 512 direct 推定大型 SwinIR 無縫。採 Compact 作最終候選，不更換使用者選定模型或展開排名。兩模型各做最小 tiled 相容性，大圖只驗 Compact；固定參數是小樣本交付設定，不能承諾所有模型無縫。
