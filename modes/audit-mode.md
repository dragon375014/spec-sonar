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
- triage: fix-now      # fix-now（真要修）/ roadmap（刻意延後的功能,不自動建）/ intentional（✅已做對或 allowlist,跳過）— 只有 fix-now 進 kickoff（見 A7）
- blast_radius: low    # low（UI/內容,可一路跑）/ high（安全·RLS·GRANT·金流,執行前人看 SQL 才 apply）
- blocking: [G3]       # 不解決就不能開工的 goal
- 需要的決定：向日葵陽光歸個人 or 全隊（二選一）
- 建議預設：歸種植者個人（與「個人賺個人花」一致，且實作較簡單）
- 解決後產出：寫入 contracts/C2-unit-stats 的 sunflower.income.owner 欄位
```

`clarify` 類 goal 不分配給執行模型——它們是 goal-decomposer 跑之前
必須由人（或 idea-to-spec 問答）清掉的前置項。

---

## A6 安全 lens（archetype=網頁/Supabase 時加跑；**warn-only 只報不擋**）

<!-- 對應 governance-meta playbooks/supabase-web-security-gate.md。只在 archetype 命中時跑；不命中略過。能力閘讀本地 house-profile.security_context 的 allowlist。 -->

Audit 一個既有 Supabase/網頁專案時，除了暗區四態，**再加跑一遍安全閘**——但**只報不擋**：把 P0~P2 安全 finding 列進報告、**不阻斷**，由人決定要不要修、何時修。

**觸發**：archetype（M0.5）= 網頁 / Supabase / 混合。其他 archetype 略過本 lens。

**掃什麼**（canonical ruleset 在 governance-meta `playbooks/supabase-web-security-gate.md`；未安裝時至少掃下列 advisor 抓不到的 GOLD）：
- **P0**：RLS 鎖列不鎖欄自我提權（有權限欄的表 + 自更新 policy + 無欄級守衛）；anon 可打無守門 SECURITY DEFINER RPC（`has_function_privilege('anon',oid,'EXECUTE')` + body 無守門）。
- **P1**：金流信 client 金額 / 簽章 fail-open / supabase-js 寫入靜默失敗 / verify_jwt 沒寫 config.toml / secdef 寫入信 client 資源 id / 前端用 admin-only 資料覆寫 DB SSOT / RLS 用 `auth.uid()`（自訂 JWT）/ JWT secret fail-open。
- **commodity**：直接吃 Supabase advisor（rls_disabled / security_definer_view / public bucket listing…），**不重造**。

**能力閘讀 allowlist**（偵測有沒有、不是身分；讀順序同 goal-decomposer 步驟零之二：`./.reuse/house-profile.json` ▸ `$HOUSE_PROFILE`）：
- 有 house-profile 且含 `security_context` → 用 `intentional_exceptions_allowlist` 把命中的 finding 分兩堆：
  - **✅ 已知已接受**（在 allowlist，附 signed_by/signed_date/review_by）——照列但標明、不當新問題；`review_by` 已過 → 提示「該複查了」。
  - **🆕 要看一下**（不在 allowlist）——這才是真正要人看的。
- 沒有 house-profile → 全部當 🆕 列出（公開使用者走這條，照常 warn-only）。

**輸出**：併進 `audit/dark-zone-findings.md` 一個「## 安全 lens（warn-only）」節，每條 = `嚴重度 / 類別 / 證據(檔/表/RPC) / 修法 / 🆕|✅`。**不轉 blocking remediation-goal**——除非人主動把某條升級處理。

> 為什麼 warn-only（決策 2026-06-27）：安全閘第一版**只報不擋**，避免誤報擋流程；allowlist 因此從「擋/放」變成「分 🆕 新 vs ✅ 已決定」，讓人每次只看新出現的。升 fail-closed 是後續決策。

---

## A7 Audit→修 接力（kickoff；能力閘；triage + blast-radius 閘）

<!-- ADR-006。warn-only 的 finding 不是都要修：很多是 ✅ 已做對、或刻意延後的 roadmap。所以照出→分類→人選→才 kickoff，不是自動修全部。 -->

Audit 跑完、findings 出來後，**主動提議把「該修的」往下接成 goal 跑**——但**先 triage、人選、才 kickoff**（warn-only 的 finding 多數不該自動修）。

**1) triage（每條 finding 自動分三桶；A6 安全 lens 與暗區/archetype finding 共用）：**
- **fix-now**：真要修、可動手（接 PhotoFrame 圖槽、補 Cookie 頁、`REVOKE ... EXECUTE`、wire 缺的入口）。
- **roadmap**：刻意延後的**功能**（go-live 模組、501 stub、mock 待接線）——**不自動建**（是路線圖不是 bug；自動建＝提前蓋）。
- **intentional**：✅ 已做對 / 在 allowlist——跳過。

**2) blast-radius（fix-now 內再分；決定能不能一路自動跑）：**
- **low**（UI/內容/加頁）→ 選了可一路 kickoff 跑到底。
- **high**（安全·RLS·GRANT·金流）→ goal 寫「**執行前人看 SQL 才 apply**」，executor 跑到先輸出完整 SQL、走 BLOCKED 回人確認——**不自動 apply**。改錯一條 RLS 比漏一條更慘。

**3) kickoff offer（能力閘，同 ADR-004）：**
- 有 `AskUserQuestion` → 問：「Audit 完。fix-now 候選有 N 條（roadmap M 條已排除、✅ K 條跳過）。要修哪幾個？」**多選**（只列 fix-now；high blast-radius 標 ⚠️ 執行前人審 SQL）。
- 沒有 → 文字列出 fix-now 候選，請人回「修 1,3,5」。
- 選的 → 寫成 `remediation-goals.md`（只含選中的）→ 接 goal-decomposer（Audit 模式）→ specmit。下游 ADR-004 接力照常。
- 選 roadmap/✅ → 不進（要建 roadmap 功能請走正常 idea-to-spec/goal，不從安全/完備掃進）。

> **自動的是流程（照出→分類→提議→你選了就分解+跑），不是判斷（修哪些、危險的要不要 apply 還是人拍板）。** 安全與 DB 改動永遠多一道人關（high blast-radius 的 BLOCKED 回審）。warn-only + 本接力 = 你只看 🆕 fix-now、選了才動、危險的還會停下給你看 SQL。
