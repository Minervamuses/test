# Phase 03 — SwinIR 共用流程驗證

## 目標與來源

開發者將 checkpoint 從 Compact 換為 SwinIR，沿用同一 I/O、device、inference、CLI，仍輸出正確圖片。依最小可運行證據選定單一交付候選。

依據 [GOALS.md](../GOALS.md) 及 [PLANS.md](../PLANS.md)。

## 範圍與非目標

只驗證第二 checkpoint、descriptor 尺寸要求及必要共用修正。不加 model factory、architecture if、第二 inference、使用者模型選擇、benchmark 或第三候選。

## 依賴與前置未知

- phase-02 Complete。使用者提供精確 SwinIR checkpoint，確認 RGB SR、來源／使用條件及 scale／size requirements／tiling metadata。
- 預期支援不等於該檔案已實測；查實際 Spandrel 版本及 checkpoint，不依名稱推論。
- 缺權重保持 Blocked，不以 mock 宣稱跑通，不下載 dataset。
- 依 PLANS.md 先估成本，只用同一真實圖的一個小裁切，不做模型／GPU sweep。

## 預期影響元件與授權

邊界為既有 model.py、inference.py、tests/test_inference.py 和 README 開發者設定。若 descriptor 已滿足要求，可只有驗證而不改 production。

保留兩個來源 checkpoint，開發者安排 models/model.pth，不能刪使用者唯一權重。額外依賴或介面變更按 PLANS.md 處理。

## 實作與驗證

1. **Preflight：** 讀既有證據及 descriptor 呼叫，核對官方文件與安裝版本，不先假定必須自行 padding。
2. **特徵化：** 少量合成 tensor 覆蓋小圖、奇數寬高、不符合 size requirements，確認輸出 W×scale、H×scale，包含極小圖 padding 行為。
3. **最小修正：** 只在真實失敗顯示缺口時補 metadata 驅動的共用處理，不能依架構名稱分支或硬寫倍率。
4. **真實驗證：** 用 phase-01 同一真實小圖／裁切，換 SwinIR checkpoint 後走完全相同 entry point，輸出到獨立驗證目錄；更換 checkpoint 不修改 inference pipeline。
5. **內容：** 開啟 PNG 確認內容／色彩、尺寸及裁回。Compact 證據仍有效；如 production 有共用修正，才重跑受影響最小 Compact 例。
6. **候選：** 兩模型均跑通後，依可運行性、資源限制和已看到輸出選單一候選。沒有差異證據就保持先跑通的 Compact；不宣稱畫質最優。phase-04 再確認大圖。

### 預定檢查

~~~bash
python -m unittest discover -s tests -p 'test_inference.py' -v
~~~

測試檔建立後才執行。真實 checkpoint 另以 phase-02 已驗證的 python -m drone_sr --input ... --output ... 執行，記實際本機路徑，不加 --model。真實權重驗證不隱藏進每次 unittest。

## 驗收條件

- Compact、SwinIR 各有真實 checkpoint／真實 SR 圖，經同一 production pipeline。
- 不符合 size requirements 的圖仍完整且尺寸正確，無殘留 padding。
- CLI、批次、錯誤處理不受換模型影響；必要修正後最小回歸通過。
- 預設候選與理由有證據，未擴張成畫質排名。

## 證據與交接

../build-log.md 記模型身分、descriptor 資訊、命令、尺寸、視覺檢查及已跑／未跑。重要版本差異與候選理由才寫 ../context/phase-03-context.md。

必要真實／尺寸驗收未過不進 phase-04，依 PLANS.md 停止條件處理；若影響 tiling 假設，先修未開始 phase-04 再交接。
