# Audit Mode — 既有設計的暗區偵測

<!-- spec-sonar v1.0 設計文件 -->

## 定位

idea-to-spec 是「從零收斂」；Audit Mode 是「對既有設計跑同一套暗區偵測」。
兩者共用 dark-zone-baseline（含類型擴充維度），差別在輸入不是問答而是文件。

## 流程（A0–A5）

```
輸入（三種之一）
  ├── 自然語言描述（用戶口述現有專案）
  ├── 貼入文件（CLAUDE.md / PRD / README / 規格書）
  └── scan/project-fingerprint.md（tools/project-scanner.py 產出）
        │
A0 輸入正規化 → 統一成「主張清單」（claims）
A1 主張萃取   → 每條 claim = { 原文引述, 所屬維度候選, 來源位置 }
A2 維度對照   → 對基準 10 維 + 類型擴充維度逐一配對
A3 四態分類   → 每個維度判為：亮 / 灰 / 暗 / 衝突
A4 依賴衝突   → 驗收條件 × 不做清單交叉檢查；claim × claim 矛盾檢查
A5 輸出三檔   → dark-zone-findings.md / dependency-conflicts.md / remediation-goals.md
```

## A3 四態判準（Audit Mode 的核心，比二元亮暗更細）

| 態 | 判準 | 範例（mathdefense 案例） |
|----|------|--------------------------|
| 亮 | 有可執行的明確答案 | 「Session 資料不持久化」 |
| 灰 | 有提及但不可執行（無數值、無判準） | 單位有 hp/attackPower 欄位但無數值 |
| 暗 | 完全未提及 | 題庫量不足時的行為 |
| 衝突 | 兩處主張無法同時成立 | 向日葵產陽光（放在共享地圖）vs 資源個人制 |

## A4 兩種交叉檢查

1. **驗收條件 × 不做清單**：每條驗收掃一次「實現它是否隱性需要禁區功能」
   （mathdefense 案例：「斷線重連恢復狀態」隱性需要跨連線身份識別，
   與「不做帳號系統」相撞）。
2. **claim × claim**：共享同一實體/狀態的主張兩兩配對
   （mathdefense 案例：向日葵歸屬）。

## 輸出檔格式

### `audit/dark-zone-findings.md` — 每維度一節

必要欄位：狀態（四態）、嚴重度、證據（原文引述 + 位置）、問題描述、
建議追問、建議預設值。

```markdown
## [維度 4] 認證與權限 — 狀態：衝突 ⛔
- 嚴重度：blocker（阻擋模組四開工）
- 證據 1：「學生斷線重連後，地圖狀態自動恢復」（模組四驗收）
- 證據 2：「不做學生帳號系統（無 JWT）」（明確不做）
- 問題：重連恢復需要跨連線身份識別，規格未給機制
- 建議追問：「重連時你接受用『一次性房間 token』識別嗎？它只活到遊戲結束。」
- 建議預設：roomCode-scoped session token（理由：最小侵入）
```

嚴重度三級：
- `blocker`：某模組無法開工
- `major`：開工後必然返工
- `minor`：可先用預設值

### `audit/dependency-conflicts.md` — 每衝突一節

欄位：衝突 ID / 主張 A（引述+位置）/ 主張 B / 為何不能同時成立 /
解法選項（2–3 個，附建議）。

### `audit/remediation-goals.md` — finding 轉 goal stub

每個 blocker / major finding 轉成與 goal-decomposer 輸入相容的 stub：

```markdown
## R1：裁決向日葵資源歸屬
- type: clarify        # clarify（要用戶裁決）/ design（要設計產出）/ fix（要改現有碼）
- blocking: [G3]       # 不解決就不能開工的 goal
- 需要的決定：向日葵陽光歸個人 or 全隊（二選一）
- 建議預設：歸種植者個人（與「個人賺個人花」一致，且實作較簡單）
- 解決後產出：寫入 contracts/C2-unit-stats 的 sunflower.income.owner 欄位
```

`clarify` 類 goal 不分配給執行模型——它們是 goal-decomposer 跑之前
必須由人（或 idea-to-spec 問答）清掉的前置項。
