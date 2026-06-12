# Public-Flip Checklist

> Everything that must be settled before this repo goes public.
> Source: issue #2 (2026-06-10 ecosystem diagnosis) + the standing validation gate.
> Status legend: ✅ done · ⏳ pending · ❌ blocking (must be green before the flip)
> **Honesty note:** the repo was flipped public *before* this checklist was fully green; the green statuses below were back-filled after the fact (2026-06-12).

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | GitHub repo description filled | ✅ done | Filled 2026-06-12. |
| 2 | (D2) Five-element goal format points to its canonical definition | ✅ done | README `## Ecosystem` section (PR #1, merged 2026-06-10) names goal-workflow-designer's `goal` skill as the format owner. |
| 3 | (B2) Governance hook for executor models | ⏳ pending | Add a one-line slot to the goal-file template + 4 adapters: "before structural changes, check the host project's governance gates (CI guard / architecture gate skill)". Lets goal execution compose with claude-skills-governance-meta instead of silently bypassing it. |
| 4 | Real-usage validation gate | ✅ done | Validated end-to-end on the MathBattle pipeline run + 12-section external audit, 2026-06-11~12. |
| 5 | Git history secret scan | ✅ done | Regex-based full-history scan across all 6 repos 2026-06-12, zero hits (pattern classes: GitHub/AWS/OpenAI/Anthropic/Google tokens, private keys, JWT, credentialed connection strings); entropy-based gitleaks pass still recommended. |
| 6 | LICENSE / README (EN + zh-TW) / CHANGELOG / CONTRIBUTING present | ✅ done | Already in the repo. |
| 7 | English-native SKILL.md files | ⏳ pending | Roadmap item, not blocking — README "Language note" already sets expectations. |

## How to use

- Work the ❌ rows first; flip to public only when no ❌ remains.
- When an item completes, change its status and append the commit / PR link in Notes.
- Topology context lives in [specmit/ECOSYSTEM.md](https://github.com/dragon375014/specmit/blob/main/ECOSYSTEM.md).
