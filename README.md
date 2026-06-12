# spec-sonar

> Find what you don't know you don't know — then let any AI model build it.

**[繁體中文版 README](README.zh-TW.md)**

spec-sonar is an open toolchain that turns vague product ideas into executable, model-agnostic specifications. One strong model (Claude Opus / Fable) does the deep design work **once**; the output is structured so that any cheaper model — Haiku, Sonnet, Cursor, Copilot, GPT — can execute it **reliably**.

## Why

AI coding agents rarely fail because they can't write code. They fail because of what nobody wrote down: the unstated requirement, the contradictory constraint, the dimension nobody thought to ask about. spec-sonar attacks that gap directly with three ideas:

1. **Dark-zone detection** — a structured inventory of the dimensions software specs systematically forget (11 baseline dimensions + per-product-type extension packs), driven through a 5–7 round Q&A engine that tracks what is known (*bright*) vs unknown (*dark*).
2. **Goal compilation** — specs are decomposed into a dependency graph of self-contained goal files. Every design decision is **pre-adjudicated** by the strong model at decomposition time, so weak executor models never have to guess.
3. **Adapters** — the same spec projects into `CLAUDE.md`, `.cursor/rules`, `copilot-instructions.md`, and a generic system prompt. Write the spec once, run it anywhere.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1 · idea-to-spec        (skill, done)                 │
│   vague idea ── 5–7 round Q&A ──► CLAUDE.md + STATE_FINAL   │
│   dark-zone tracking · conflict protocols · wheel-reinvention check
│   boundary scan · contradiction scan · undetermined-value rule (step 7-3)
│   journey coverage check · enterprise governance-SKILL recommendation
│   handoff requires boundary_scan = done                     │
├─────────────────────────────────────────────────────────────┤
│ Layer 2 · goal-decomposer     (skill, done)                 │
│   spec ── dependency inference ──► goal-graph.json          │
│        ── pre-adjudication   ──► goals/G*.md (self-contained)
│        ── interface freezing ──► contracts/C*.md            │
│   wiring matrix (orphan interface = compile error)          │
│   mandatory G0 / G-FINAL structural goals                   │
│   cross-end acceptance splitting · zero-context blind audit (step 7-2)
├─────────────────────────────────────────────────────────────┤
│ Layer 3 · execution           (any model)                   │
│   Haiku / Sonnet / Cursor / Copilot / GPT follow the graph  │
│   BLOCKED protocol instead of guessing                      │
└─────────────────────────────────────────────────────────────┘
```

## Three modes

| Mode | Input | Purpose |
|------|-------|---------|
| **From Zero** | a vague idea | converge to a spec in 5–7 rounds |
| **Audit** | an existing project description, docs, or a `project-scanner.py` fingerprint | find the holes in an existing design (bright / fuzzy / dark / conflicting, per dimension) |
| **Complex System** | ERP / multi-module SaaS | two-level decomposition with cross-subsystem contracts |

## Quick start

```bash
git clone https://github.com/<you>/spec-sonar
# install the skills into Claude Code
cp -r skills/idea-to-spec  ~/.claude/skills/
cp -r skills/goal-decomposer ~/.claude/skills/
```

1. Tell Claude about your idea — *"I want to build a booking system for my yoga studio"*. The idea-to-spec engine runs 5–7 focused rounds, tracking bright/dark zones in a `<STATE>` block, and hands off `README.md` + `CLAUDE.md` + `STATE_FINAL.json`.
2. Say *"decompose this spec"*. The goal-decomposer compiles it into `goal-graph.json` + self-contained `goals/G*.md` + frozen `contracts/C*.md` + four platform adapters.
3. Feed the goal files to **any** model, in dependency order (parallel within a batch). Each goal file passes the *cold-start test*: an executor with zero conversation context can answer — what to build, how to verify, what's forbidden, what to do when stuck.

For auditing an existing codebase:

```bash
python tools/project-scanner.py /path/to/project -o scan/project-fingerprint.md
# then hand the fingerprint to Audit Mode (modes/audit-mode.md)
```

## The portability guarantee

A goal file is not "a well-written task description" — it is a format that **removes the executor's degrees of freedom**. Eight mechanisms (see [docs/model-portability.md](docs/model-portability.md)):

self-containment · pre-adjudication · literal interface freezing (JSON instances, not schemas) · mechanical verification commands · a BLOCKED protocol instead of guessing · negative acceptance criteria (testable "don'ts") · a self-check footer · the cold-start test as the pass/fail bar.

## Repository layout

```
skills/
  idea-to-spec/            requirement-convergence engine (SKILL.md + references)
  goal-decomposer/         spec → goal-graph compiler (SKILL.md)
modes/
  audit-mode.md            dark-zone detection for existing designs
  conflict-analysis-mode.md  skill-ecosystem conflict analysis
tools/
  project-scanner.py       stdlib-only codebase fingerprinter (<20 KB output)
schemas/
  goal-graph.schema.json   JSON Schema for the dependency graph
docs/
  output-directory-spec.md · adapter-formats.md · model-portability.md
  review-findings.md · value-analysis.md
examples/
  mathdefense/             real end-to-end case study (spec → graph → goal file)
  conflict-report-sample.md
```

## Case study: mathdefense

A real classroom multiplayer tower-defense math game, converged from a vague idea through 6 rounds into a full spec, then decomposed into 7 goals + 2 contracts across 5 execution batches. The audit of its own output caught three genuine spec holes (missing unit stats, an undefined zombie movement model, and a reconnect-identity requirement that collided with the "no accounts" rule) — see [docs/review-findings.md](docs/review-findings.md).

## Ecosystem

spec-sonar is the **converge + decompose layer** (Layers 1–2) of an AI-dev toolchain — five public repos plus the author's private cross-project knowledge vault. Full map: [specmit/ECOSYSTEM.md](https://github.com/dragon375014/specmit/blob/main/ECOSYSTEM.md).

**One-command install** (drops every tool into the right place):
```bash
npx specmit init
```
Then, in Claude Code, say *"run the pipeline"* (「跑完整管線」) to execute the whole chain.

- **Downstream** — [`goal-workflow-designer`](https://github.com/dragon375014/goal-workflow-designer) owns the single-task shaping axis: its `goal` skill defines the five-element goal format this repo's goal files reuse, and its `workflow-shaper` handles homogeneous fan-out (the same check across N units), which is out of scope here.
- **At execution time** — [`specmit`](https://github.com/dragon375014/specmit) runs the decomposed goal graph; [`claude-skills-governance-meta`](https://github.com/dragon375014/claude-skills-governance-meta) guards the executor models; [`agent-work-board`](https://github.com/dragon375014/agent-work-board) coordinates parallel sessions.

## Language note

The skill instruction files are currently authored in **Traditional Chinese**. This does not limit usage: Claude follows the skill logic regardless of conversation language and responds in *your* language (the STATE carries a `lang` field). English-native skill files are on the roadmap — contributions welcome.

## Roadmap

- [ ] English-native versions of both SKILL.md files
- [ ] Eval harness: measure dark-zone coverage and goal cold-start pass rate
- [ ] Audit Mode and Conflict Analysis Mode packaged as runnable skills
- [ ] More end-to-end examples (B2B SaaS, marketplace, internal tool)
- [x] `goal-graph.json` execution runner (auto-dispatch batches to models) — shipped as [specmit](https://github.com/dragon375014/specmit)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The highest-value contributions are new dark-zone dimensions backed by real post-mortems, product-type extension packs, and adapter formats for additional platforms.

## License

[MIT](LICENSE)
