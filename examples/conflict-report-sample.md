# Skill Conflict Report（範例）

<!-- 由 Conflict Analysis Mode 產出的範例報告，掃描對象為一個真實的 skill 生態 -->

掃描 4 個 skills @ 2026-06-10 ｜ 發現 4 項衝突：critical 1, high 1, medium 2

| # | A | B | 類型 | 嚴重度 |
|---|---|---|------|--------|
| C1 | idea-to-spec | goal | trigger-overlap | high |
| C2 | idea-to-spec | goal-decomposer(adapters) | namespace-pollution | critical |
| C3 | graphify | （全體） | trigger-overlap | medium |
| C4 | workflow-shaper | goal-decomposer | logic-contradiction | medium |

---

## C2：idea-to-spec × goal-decomposer — CLAUDE.md 覆蓋 ⛔ critical

- 證據 A：idea-to-spec 步驟八「輸出三個檔案：…CLAUDE.md」
- 證據 B：goal-decomposer 輸出 adapters/CLAUDE.md 並部署到專案根目錄
- 影響：用戶若在 idea-to-spec 產出後手改了 CLAUDE.md，decomposer 重新生成
  adapter 時會無警告覆蓋手改內容
- 建議：(1) adapter 生成前 diff 檢查，發現非生成內容 → 中止並要求確認；
  (2) 兩者產出的 CLAUDE.md 統一加 provenance 標頭以便識別來源

## C1：idea-to-spec × goal — 觸發重疊 high

- 證據 A：idea-to-spec「用戶說『我想做一個 App/系統/平台』…就主動使用」
- 證據 B：goal「用戶說『我想做一個目標』『幫我寫個 goal prompt』」
- 測試句：「我想做一個幫我追蹤目標的 App」→ 兩者皆命中
- 影響：模型隨機選一，同句不同 session 行為不一致
- 建議：idea-to-spec 加排除句「若意圖是設計單一任務的 goal prompt 而非
  完整軟體產品，讓位給 goal skill」；goal 加正向限定「目標指 prompt 設計，
  非軟體產品」
- 處置狀態：✅ 已套用於 spec-sonar v1.1 的 idea-to-spec description

## C3：graphify — 貪婪觸發 medium

- 證據：description「any input to knowledge graph」——「any input」使任何
  含「圖」「整理」的語句都可能誤觸
- 影響：與所有 skill 形成低度觸發競爭
- 建議：限定為顯式 /graphify 觸發，移除隱式觸發描述

## C4：workflow-shaper × goal-decomposer — 分解語意撞域 medium

- 證據：兩者都回應「把任務拆開/分解」類語句
- 邊界裁定建議：同質單元 fan-out（同一檢查跑 N 個檔案）→ workflow-shaper；
  異質模組帶依賴圖 → goal-decomposer。把這條邊界句寫進雙方 description。
- 處置狀態：✅ 已套用於 spec-sonar v1.0 的 goal-decomposer description
