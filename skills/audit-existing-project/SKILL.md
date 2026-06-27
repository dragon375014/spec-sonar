---
name: audit-existing-project
description: 對「已經存在的專案」跑完備性 + 安全體檢，把缺的、薄的、危險的照出來，再接力修。當用戶說「幫我補全/補完這個專案」「體檢/健檢一下這個既有專案」「audit 這個專案」「掃一下哪裡沒做完 / 缺什麼」「這個網站缺哪些頁 / 後台進不去 / 有頁沒入口」「幫我做完備性掃描」「complete / audit this existing project」「what's missing in this codebase」時觸發。也在用戶 `npx specmit init` 裝完工具、回頭說「請幫我自動補全」時觸發。流程：偵測 project-scanner → 跑 Audit Mode（暗區四態 + archetype 完備性軸 + 網頁/Supabase 安全 lens）→ A7 triage（fix-now / roadmap / intentional）→ 問用戶要修哪幾個 → 寫 remediation-goals.md 接力 goal-decomposer。**讓位規則**：從零開始的新想法（還沒有 code）讓位給 idea-to-spec；單一任務打磨讓位給 goal；單一已知 bug 直接修不需這支。本 skill 是 brownfield（既有專案）入口，不是 from-zero。
---

# Audit Existing Project — 既有專案補全 / 體檢入口（brownfield）

<!-- spec-sonar v1.0 — brownfield「補全」入口（ECOSYSTEM connector-needed）。ADR-002 archetype 完備性軸 / ADR-005 安全 lens / ADR-006 audit→修 接力 的觸發前門。 -->

## 行為契約

你是 brownfield（既有專案）的**入口協調器**，不是掃描器、不是修法本身。
你的職責只有四件：**偵測能力 → 跑 Audit Mode → triage → 問用戶要修哪幾個並接力下游**。
所有實際的判準（暗區四態、archetype 完備性 baseline、安全 GOLD 清單、triage 三桶、blast-radius 閘）都**讀既有文件**，**不要在這裡重寫一份**（重寫 = 第二真相源 = 會漂移）。

讀這兩份當作業手冊（路徑為安裝後的相對位置；canonical 在 spec-sonar repo）：
- **`references/audit-mode.md`**（repo: `modes/audit-mode.md`）— Audit Mode A0–A7 完整流程。
- **`../idea-to-spec/references/dark-zone-baseline.md`**（repo: `skills/idea-to-spec/references/dark-zone-baseline.md`）— M0 modality / M0.5 archetype 分叉樁 / 類型 F 呈現型網站 baseline / L1-L2-L3 三層完備性階梯。**這是 A2 維度對照拿來當「尺」的 baseline。**

> from-zero（idea-to-spec）與 brownfield（本 skill → Audit Mode）**共讀同一份 dark-zone-baseline**，所以 archetype 完備性軸是「一處修、兩模式亮」。

## 何時觸發 / 何時讓位

| 情境 | 走哪 |
|---|---|
| 既有專案要找「缺什麼 / 沒做完 / 不完整 / 有頁沒入口 / 後台進不去」 | **本 skill** |
| 網頁 / Supabase 既有專案要順手掃安全 | **本 skill**（archetype 命中時 A6 安全 lens 自動加跑，warn-only） |
| 裝完 `specmit init` 後說「幫我自動補全」 | **本 skill** |
| 從零開始、還沒有 code 的新想法（「我想做一個 App」） | 讓位 **idea-to-spec**（from-zero 收斂） |
| 單一任務要打磨到位（「把這個功能做對」） | 讓位 **goal** |
| 單一已知 bug，根因清楚 | 直接修，不需這支 |
| 已經有 remediation-goals.md，只要分解排程 | 直接進 **goal-decomposer**（Audit 模式） |

## 步驟零：能力閘 + 載入（偵測「有沒有」，不是「是不是」）

同 ADR-001/003/005 的同一條法則——**偵測能力、不偵測身分**：

1. **AskUserQuestion 類工具有沒有** → 決定步驟四的提問走卡片或純文字（rich / text）。
2. **`tools/project-scanner.py`（Python 3.9+）跑不跑得動** → 決定步驟一用「掃描」還是「貼文件 / 口述」當輸入。
3. **本地 house-profile 有沒有**（讀順序 `./.reuse/house-profile.json` ▸ `$HOUSE_PROFILE`）→ 有 `security_context.intentional_exceptions_allowlist` 就拿去把安全 finding 分 🆕 / ✅（同 audit-mode.md A6）；沒有 → 全部當 🆕，照常 warn-only。**公開使用者沒有 house-profile 是正常路徑，不報錯、優雅降級。**

載入兩份手冊（上面〈行為契約〉列的）。

## 步驟一：輸入正規化 → claims（audit-mode.md A0）

把「現有專案的事實」收成 Audit Mode 吃得下的輸入，三選一（優先序由上而下）：

- **掃描（最佳）**：project-scanner 跑得動 → `python references/project-scanner.py <專案根> -o scan/project-fingerprint.md`（repo: `tools/project-scanner.py`），拿到 routes / exports / TODO / 結構指紋。
- **貼文件**：用戶貼 CLAUDE.md / README / PRD / 路由表。
- **口述**：用戶描述現有專案。

## 步驟二：跑 Audit Mode（A0–A6）

照 `references/audit-mode.md` 跑，**三條 lens 疊一起**：

1. **暗區四態（A0–A5）**：每個維度判 亮 / 灰 / 暗 / 衝突；A4 兩種交叉檢查（驗收 × 不做清單、claim × claim）。
2. **archetype 完備性軸（A2 拿 baseline 當尺）**：先定 archetype（M0.5：交易型 / 呈現型 / 混合，infer-first + 一行確認）→ 載對應 baseline（呈現型 = 類型 F）→ 用 **L1 存在 / L2 可達 / L3 充實** 照出「該有沒有」的面（缺關於我頁、有後台沒入口、有頁沒媒體槽 + 後台沒填料路徑 = 空殼）。**這一層補的正是「導航表通過 ≠ 前端完整」那個盲區**——導覽只驗「已宣告的都到得了」，baseline 驗「該有的有沒有」。
3. **安全 lens（A6，archetype = 網頁/Supabase/混合 才加跑；warn-only 只報不擋）**：掃 advisor 抓不到的 GOLD（RLS 鎖列不鎖欄自我提權、anon 可打無守門 SECURITY DEFINER RPC、金流信 client 金額/簽章 fail-open…）；house-profile allowlist 分 🆕 / ✅。

## 步驟三：A7 triage + blast-radius（照出 ≠ 全修）

每條 finding 自動分三桶（audit-mode.md A7）：

- **fix-now**：真要修、可動手（接圖槽、補 Cookie 頁、`REVOKE … EXECUTE`、wire 缺的入口）。
- **roadmap**：刻意延後的**功能**（go-live 模組、501 stub、mock 待接線）——**不自動建**（是路線圖不是 bug）。
- **intentional**：✅ 已做對 / 在 allowlist——跳過。

fix-now 內再分 **blast-radius**：low（UI/內容/加頁，可一路跑）/ high（安全·RLS·GRANT·金流，goal 寫「執行前人看 SQL 才 apply」、走 BLOCKED 回人，不自動 apply）。

## 步驟四：問用戶要修哪幾個（能力閘，kickoff offer — ADR-006）

**只列 fix-now**（roadmap / ✅ 不列），主動提議、**不自動修全部**：

- **有 AskUserQuestion** → 多選題：「Audit 完。fix-now 候選有 N 條（roadmap M 條已排除、✅ K 條跳過）。要修哪幾個？」high blast-radius 的選項標 ⚠️「執行前人審 SQL」。
- **沒有** → 文字列出 fix-now 候選，請用戶回「修 1,3,5」。

## 步驟五：寫 remediation-goals.md → 接力 goal-decomposer

用戶選好 → 把選中的（只選中的）寫成 `audit/remediation-goals.md`（格式見 audit-mode.md「remediation-goals.md」一節 + `triage`/`blast_radius` 兩欄）→ **主動提議接力**（同 ADR-004）：

- 有 AskUserQuestion → 問：「remediation 寫好了（N 條）。要現在分解成 goal 圖嗎？」選項：[建議 — 現在分解（goal-decomposer）] / [我先看 remediation] / [先停在這]。
- 用戶選「現在分解」→ 進 **goal-decomposer（Audit 模式）**，讀 `remediation-goals.md` + `scan/project-fingerprint.md`。goal-decomposer 跑完會再提議接 specmit（ADR-004 接力照常）。
- 選別的 → 停。

> **自動的是流程（照出 → 分類 → 提議 → 你選了就接力），不是判斷（修哪些、危險的要不要 apply 還是人拍板）。** high blast-radius 的安全/DB goal 永遠多一道人關（BLOCKED 回審 SQL）。

## ⚠️ 不要改回去

- **不要**在這支 skill 重抄一份暗區四態 / archetype baseline / 安全 GOLD 清單 / triage 規則——那會變第二真相源，baseline 改了這裡會漂掉。本 skill 只**讀**手冊、做編排。
- **不要**把這支拿去接 from-zero 的新想法——那是 idea-to-spec。本 skill 只認「已經有專案」。
- **不要**把 triage 的 roadmap / intentional 也丟進 kickoff——會提前蓋延後功能、改壞已對的。
- **不要**讓 high blast-radius 的安全/RLS goal 自動 apply——必須 BLOCKED 回人審 SQL。
- **不要**因為某平台沒 AskUserQuestion / 沒 house-profile 就讓流程壞掉——能力閘退文字 / 退「全 🆕 warn-only」是正常路徑。

## 參考

- Audit Mode A0–A7：`references/audit-mode.md`（repo: `modes/audit-mode.md`）。
- archetype 完備性 baseline：`../idea-to-spec/references/dark-zone-baseline.md`。
- 設計決策：spec-sonar `DESIGN-NOTES.md` ADR-002（archetype 軸）/ ADR-005（安全 lens）/ ADR-006（audit→修 接力）/ ADR-008（本入口的 wiring）。
- 生態系定位：specmit `ECOSYSTEM.md` 路由「complete an existing project」/「security-scan a Supabase/web project」。
