# Public-Flip Checklist

> Everything that must be settled before this repo goes public.
> Source: issue #2 (2026-06-10 ecosystem diagnosis) + the standing validation gate.
> Status legend: ✅ done · ⏳ pending · ❌ blocking (must be green before the flip)

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | GitHub repo description filled | ❌ blocking | Field is currently blank. Suggested: "Find what you don't know you don't know — idea-to-spec convergence + goal-graph decomposition, model-agnostic." One click in repo settings. |
| 2 | (D2) Five-element goal format points to its canonical definition | ✅ done | README `## Ecosystem` section (PR #1, merged 2026-06-10) names goal-workflow-designer's `goal` skill as the format owner. |
| 3 | (B2) Governance hook for executor models | ⏳ pending | Add a one-line slot to the goal-file template + 4 adapters: "before structural changes, check the host project's governance gates (CI guard / architecture gate skill)". Lets goal execution compose with claude-skills-governance-meta instead of silently bypassing it. |
| 4 | Real-usage validation gate | ❌ blocking | The standing rule for this repo: validated through real project use before publication — the reason it is private today. |
| 5 | Git history secret scan | ❌ blocking | Run gitleaks (or equivalent) over the full history before the flip — private-era commits become public retroactively. |
| 6 | LICENSE / README (EN + zh-TW) / CHANGELOG / CONTRIBUTING present | ✅ done | Already in the repo. |
| 7 | English-native SKILL.md files | ⏳ pending | Roadmap item, not blocking — README "Language note" already sets expectations. |

## How to use

- Work the ❌ rows first; flip to public only when no ❌ remains.
- When an item completes, change its status and append the commit / PR link in Notes.
- Topology context lives in [ai-dev-toolkit/ECOSYSTEM.md](https://github.com/dragon375014/ai-dev-toolkit/blob/main/ECOSYSTEM.md).
