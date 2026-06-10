# Changelog

## [0.1.0] - 2026-06-10

### Added
- `skills/idea-to-spec` v1.1 — requirement-convergence engine
  - STATE schema 1.1: `bright` items carry id/round/depends_on; new `revision_log` and `pending_conflict` fields
  - Step 7.5 conflict protocols: retraction (with cascade re-darkening), contradiction (forced trilemma, no silent adjudication), late addition (impact-tiered)
  - Trigger exclusion clause vs the `goal` skill (conflict report C1)
- `skills/idea-to-spec/references/dark-zone-baseline.md` v1.1 — 5 product-type extension packs (Marketplace, B2B SaaS, Consumer App, Internal Tool, ERP), 2–3 dimensions each
- `skills/idea-to-spec/references/output-templates.md` v1.1 — STATE_FINAL formally adopts `tech_stack`, `known_risks`, `revision_log` (fixes schema drift found in self-audit)
- `skills/goal-decomposer` v1.0 — spec → goal-graph compiler: 4-type dependency inference with evidence, granularity rules, contract freezing, model-tier assignment, cold-start self-check
- `modes/audit-mode.md` — A0–A5 pipeline, four-state classification (bright/fuzzy/dark/conflict), three output file formats
- `modes/conflict-analysis-mode.md` — S1–S5 pipeline, conflict-report.md format
- `tools/project-scanner.py` — stdlib-only fingerprinter (tree, interfaces, imports, routes, socket events, data models, TODO stats; 3-level size degradation, <20 KB)
- `schemas/goal-graph.schema.json` — draft-07 schema v1.0
- `docs/` — output directory spec, adapter formats (Claude Code / Cursor / Copilot / generic agent), model-portability guarantees (8 mechanisms), review findings
- `examples/mathdefense` — real end-to-end case: spec, STATE_FINAL, goal-graph (7 goals, 2 contracts, 5 batches), G4a goal file
- `examples/conflict-report-sample.md`
- Bilingual README + CONTRIBUTING (en, zh-TW), MIT license
