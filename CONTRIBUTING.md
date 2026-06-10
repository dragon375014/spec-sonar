# Contributing to spec-sonar

**[繁體中文版](CONTRIBUTING.zh-TW.md)**

Thanks for your interest! spec-sonar is a methodology project as much as a code project — the most valuable contributions are *distilled experience*, not features.

## What we want most

1. **New dark-zone dimensions** — a dimension belongs in `dark-zone-baseline.md` only if you can point to a real project that failed (or required major rework) because nobody asked that question. Include the post-mortem evidence in your PR description.
2. **Product-type extension packs** — we cover Marketplace / B2B SaaS / Consumer App / Internal Tool / ERP. New types (e.g. embedded, data pipeline, game) follow the same format: 2–3 dimensions, each with concrete questions and a 亮區條件 (bright-zone criterion).
3. **Adapter formats** — new target platforms (Windsurf, Aider, OpenHands…). Follow `docs/adapter-formats.md`: state the platform's *reading model* first (does it execute tasks, edit code, or autocomplete?), then derive the format from that.
4. **End-to-end examples** — a real idea converged through the engine, decomposed, and (ideally) executed. Redact anything private.
5. **Translations** — English-native versions of the SKILL.md files are the top roadmap item.

## Ground rules

- **Mergeable sections**: changes to SKILL.md files must keep the fixed-behavior-rules style (numbered protocols, tables, response templates). No roleplay language.
- **Evidence-based**: every dependency type, dimension, or protocol must come with at least one concrete example of the failure it prevents.
- **Self-containment is sacred**: anything that makes goal files depend on external context will be rejected — it breaks the cold-start test.
- **Bilingual docs**: README-level docs ship in English and Traditional Chinese. Deep design docs may ship in either language first; mark them for translation.
- `tools/project-scanner.py` must stay **stdlib-only** and its output under 20 KB.

## Workflow

1. Open an issue describing the gap before large PRs.
2. Branch from `main`, keep PRs focused on one concern.
3. For schema changes (`STATE`, `goal-graph`), bump the schema version and update `CHANGELOG.md`.
