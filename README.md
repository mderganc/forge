# Forge

Forge runs **multi-step, resumable workflows** for AI-assisted delivery: investigation, planning, plan and implementation review, implementation, code review, testing (including mock-flow authoring), and diagnostics.

The same install targets **Cursor**, **Claude Code**, and **OpenAI Codex**. Cursor and Claude Code use slash commands (for example `/forge:plan` and `/forge:doctor`). **Codex** uses `$forge:…` skills (for example `$forge:plan`, `$forge:diagnose`) installed under `~/.codex/skills/forge/` — the same workflows as [`integrations/spec/commands.json`](integrations/spec/commands.json). Skills ultimately call the `forge` CLI behind the scenes (via `<invoke cmd="…"/>`); in Codex chat you invoke workflows with `$forge:…`, not by typing `forge …` yourself. On disk, skill folders use hyphenated names (e.g. `forge-diagnose/`) because `:` is not allowed in paths; each `SKILL.md` sets `name: forge:…`, which Codex shows as `$forge:…`. For shells and CI without Codex, see [Advanced: terminal and CI](#advanced-terminal-and-ci).

Install once with `pipx install forge-next`, then run `forge install` to add the Cursor plugin, Claude command pack, and Codex skill pack. Use `--cursor`, `--claude`, or `--codex` if you only want one or two. Most of the time you stay in the app; use the terminal for `forge doctor`, CI hooks, or cleanup when that is easier.

This repository is the **source tree** for prompts, templates, agent briefs, and orchestrators bundled with that package.

---

## Command notation 

| Product | Form | Example |
|---------|------|---------|
| Cursor | `/forge:…` | `/forge:code-review` |
| Claude Code | `/forge:…` | `/forge:code-review` |
| Codex | `$forge:…` (mention / skill picker) | `$forge:code-review` |

**Terminal / CI** uses a space, not a colon: `forge plan`, `forge diagnose` (see [Advanced](#advanced-terminal-and-ci)).

**Note:** In Cursor or Claude, type `/forge:` then the subcommand (for example `/forge:diagnose`). In Codex, type `$forge:` or pick the skill — user-facing IDs match `$forge:<subcommand>` (same spelling as `/forge:<subcommand>`, with `$` instead of `/`).

**Slash command files:** Cursor and Claude command packs use `<subcommand>.md` under their install trees (plugin namespace `forge`), so the picker shows `/forge:<subcommand>`. Shorter aliases such as `/f:diagnose` or bare `/diagnose` are not provided — see [`integrations/README.md`](integrations/README.md).

---

## Overview

- **App-first:** Cursor and Claude Code use `/forge:…`; Codex uses `$forge:…`. See [OpenAI Codex](#openai-codex).
- **Session-safe:** Repo state lives under `.codex/forge/` by default. Older trees may still use `.codex/forge-codex/` until migrated. If `.codex` cannot be a directory, Forge falls back to `.forge/`. Stop anytime; continue with `forge resume`, `/forge:resume` (Cursor/Claude), or `$forge:resume` (Codex). Each skill save also updates **`state/resume-context.json`** (continuity snapshot for new chats) and **`memory/forge-memory-synthesis.md`** (rollup of `project.md`, `current-step.md`, and recent handoffs). Resume prints memory + optional **Graphify** codebase status; if the snapshot disagrees with live JSON state, output asks you to pick **state-based** vs **snapshot-based** continuation before auto-running the next step.
- **Handoffs:** On the last step, the numbered menu may show `forge: …` labels in the transcript. Reply `yes`, `1`, or `default`, or pick an option, then run the next step as `/forge:…` (Cursor/Claude) or `$forge:…` (Codex). Outside Codex, use the `forge …` command line from [Advanced: terminal and CI](#advanced-terminal-and-ci). Downstream step-1 intake consumes handoffs (read + close) so used handoffs do not stay active indefinitely.
- **Per-skill run memory:** Every workflow run appends an auditable entry to `memory/<skill>-runs.jsonl` (for example `plan-runs.jsonl`), retaining the most recent 30 entries with timestamp, phase/step, short summary, session linkage, and handoff linkage when present.
- **Integrations:** `forge install` and `forge uninstall` lay down Cursor, Claude, and Codex wrappers. Install output includes optional **Graphify** setup (CLI or `FORGE_GRAPHIFY_COMMAND`, `forge graphify refresh`, `install-hook` / `uninstall-hook`) for codebase context in `forge resume` — see [`docs/graphify.md`](docs/graphify.md).
- **Memory rollup:** each time skill state is saved, Forge refreshes **`memory/forge-memory-synthesis.md`** as an explicit merge of `project.md`, `current-step.md`, and recent handoffs so resume can open one synthesized narrative (see `templates/memory-protocol.md`).

---

## Optional: Beads (issue tracking)

Workflows can hook **[Beads](https://github.com/steveyegge/beads)** (`bd` CLI) so epics, findings, tasks, and dependencies stay in sync with Forge memory and handoffs. It is **optional**: if Beads is not available, prompts fall back to memory files and sequential IDs (see `templates/beads-integration.md`).

- **Canonical guide:** `templates/beads-integration.md` (epic layout, `bd` examples, degraded mode).
- **Cross-references:** `templates/memory-protocol.md`, `templates/handoff-protocol.md` (Beads section in status handoffs).
- **Runtime:** develop startup checks Beads (`prompts/develop/startup.md`). Skill state includes a `beads_available` flag in `scripts/shared/orchestrator.py`, but whether Beads is used is driven by prompts and `project.md` (“beads: available/unavailable”), not by automatic detection in the orchestrator.

---

## Requirements

- Python **3.10+** (required by `forge-next`)
- **pipx** recommended so `forge` is on your PATH — [pipx documentation](https://pipx.pypa.io/) (Windows: `py -m pip install --user pipx` then `pipx ensurepath` if needed)
- A **project** that is a git repo or contains `README.md` (the launcher uses that to find the target root)

---

## Installation

### 1. Install the launcher (once per machine)

```bash
pipx install forge-next
```

### 2. Install app integrations

```bash
forge install
```

`forge install` also installs structural probes for code-review / evaluate (**knip**, **madge**, **pyscn**, **skylos**) and prints warnings for any that could not be installed. To skip: `forge install --skip-structural-tools`. See [`docs/structural-quality.md`](docs/structural-quality.md).

Or only what you use:

```bash
forge install --cursor
forge install --claude
forge install --codex
```

Options (defaults are usually fine): `--ref`, `--repo-url`, `--cursor-dir`, `--claude-dir`, `--codex-dir`.

**After `forge install`:** the installer prints optional **Graphify** setup (install the Graphify CLI or set `FORGE_GRAPHIFY_COMMAND`, run `forge graphify refresh`, optionally `forge graphify install-hook` for post-commit refresh). Same hints appear in JSON output as `graphify_onboarding` when you pass `--json`. Details: [`docs/graphify.md`](docs/graphify.md).

**Note:** Running from Windows will install in the Windows Cursor/Claude/Codex locations, while WSL will use the WSL locations.

### 3. First run in the app (not in a terminal)

1. Check setup: `/forge:doctor` (Cursor/Claude), or `$forge:doctor` (Codex).
2. Start planning: `/forge:plan` (Cursor/Claude), or `$forge:plan` (Codex).
3. Follow the printed steps. Re-run the same slash command (Cursor/Claude), or the next `$forge:…` (Codex). If the transcript shows `forge: …`, treat it as a label and use the matching `/forge:…` or `$forge:…` as appropriate.

Work in another folder than the editor root only when your integration documents it (some flows pass a repo path through the launcher).

After a new `forge-next` release on PyPI, upgrade with `pipx upgrade forge-next` (or reinstall with `pipx install forge-next --force`). Pin a specific version when reproducibility matters, for example `pipx install 'forge-next==0.18.0'` (see `project.version` in `pyproject.toml`).

---

## Commands in your apps

All **14** workflows are defined in [`integrations/spec/commands.json`](integrations/spec/commands.json).

| Workflow | Cursor / Claude | Codex |
|----------|-----------------|-------|
| **Sketch** — organize intent before develop (optional) | `/forge:sketch` | `$forge:sketch` |
| **Develop** — discovery, requirements, options; medium/large scope may require a written design spec before handoff | `/forge:develop` | `$forge:develop` |
| Implementation plan | `/forge:plan` | `$forge:plan` |
| Plan / implementation review | `/forge:evaluate` | `$forge:evaluate` |
| Execute plan in waves | `/forge:implement` | `$forge:implement` |
| Structured code review | `/forge:code-review` | `$forge:code-review` |
| Tests or mock-flow authoring | `/forge:test` | `$forge:test` |
| Root-cause / incident analysis | `/forge:diagnose` | `$forge:diagnose` |
| Meta-workflow (chained loops) | `/forge:iterate` | `$forge:iterate` |
| **Ship** — finalize: commit, push, PR, publish | `/forge:ship` | `$forge:ship` |
| Check install / environment | `/forge:doctor` | `$forge:doctor` |
| Dashboard | `/forge:status` | `$forge:status` |
| Resume or cleanup | `/forge:resume` | `$forge:resume` |
| Optional Graphify (codebase map) | `/forge:graphify` | `$forge:graphify` |

**Terminal:** same subcommands as `forge graphify …` (see [`docs/graphify.md`](docs/graphify.md)).

**Codex:** `forge install --codex` installs skills under `~/.codex/skills/forge/` (see [`integrations/codex/README.md`](integrations/codex/README.md)). In the app you invoke `$forge:<subcommand>`; that matches `name: forge:<subcommand>` in each `SKILL.md` (aligned with [`integrations/spec/commands.json`](integrations/spec/commands.json)).

---

## Uninstallation

**Integrations (Cursor / Claude / Codex):**

```bash
forge uninstall
```

(or `--cursor`, `--claude`, `--codex`)

**Launcher:**

```bash
pipx uninstall forge-next
```

**Project state** (optional): `forge resume --cleanup` (terminal), or `/forge:resume` / `$forge:resume` with cleanup if exposed, or delete `.codex/forge/` (and legacy `.codex/forge-codex/` if present) and `.forge/` in that repo as needed.

---

## How skills work (in the apps)

1. You pick a command: `/forge:…` (Cursor/Claude), `$forge:…` (Codex), or `forge …` in a terminal when not using an editor integration ([Advanced](#advanced-terminal-and-ci)). That authorizes the multi-step flow. See [AGENTS.md](AGENTS.md).
2. **Steps:** Each run advances phase 1, 2, … Output is the prompt (and sometimes todos) for that phase, plus where state is stored.
3. **Roles:** Prompts reference architect, planner, implementers, critic, QA, security, doc-writer. Hosts with sub-agents should follow the skill dispatch pattern and close agents when a slice of work is done (especially on Codex).
4. **Handoff menu:** Last step lists options; transcript text may include `forge: …` labels. Your next command is `/forge:…` (Cursor/Claude) or `$forge:…` (Codex).
5. **Quick mode:** Where supported, integrations pass `--quick` through to the launcher; see `skills/`.

---

## Session + handoff audit lifecycle

**Primary layout** (new runs): under `.codex/forge/sessions/` each workflow gets a directory with `session.json`, optional `handoff.md`, and `sidecars/` for step artifacts. `index.json` lists active sessions; completed or auto-closed sessions move to `sessions/_archive/`. See [`docs/sessions.md`](docs/sessions.md).

**Legacy layout** (still supported): flat JSON under `.codex/forge/state/` (for example `plan.json`, `plan-foo.json`) and global `memory/handoff-{skill}.md`. Resume and cleanup understand both layouts.

- **Run memory files:** Each skill appends a short record on every step run to `memory/<skill>-runs.jsonl` and keeps only the last ~30 records.
- **Continuity snapshot:** On every skill state save (and evaluate saves), Forge writes **`state/resume-context.json`** with skill, steps, invocation hint, state path, and pointers to the latest handoff / `current-step.md` for `forge resume` and new chat pickup.
- **Memory synthesis:** The same saves refresh **`memory/forge-memory-synthesis.md`** — an explicit merge of `project.md`, `current-step.md`, and recent handoffs (see `templates/memory-protocol.md`). Resume prefers this file for the memory narrative when present.
- **Audit linkage:** Run-memory records include `state_path`/`session_ref` and `handoff_path`/`handoff_ref` (when a handoff exists), plus timestamp and summary.
- **Handoff closure:** Handoffs are consumed on step-1 intake of downstream skills (for example plan consumes develop handoff, code-review consumes implement handoff, test consumes code-review/implement handoffs).
- **Session completeness:** Active-session detection treats a run as complete when either `completed_at` is set or legacy state reached max step (`current_step >= max_step` and `last_completed_step >= max_step`).
- **Cleanup behavior:** `forge resume --cleanup` removes stale session directories and legacy flat state files (dry-run by default; `--force` to delete). Env: `FORGE_SESSION_MAX_AGE_DAYS` (default `7`), `FORGE_SKIP_SESSION_CLEANUP=1` to disable automatic archive of old sessions.
- **Auto-close on step 1:** Starting a pipeline skill removes superseded session JSON when a handoff exists, when you move forward in the pipeline, or when a step-1-only session was abandoned (see [AGENTS.md](AGENTS.md) State Lifecycle). `forge status` / `forge doctor` report remaining leaks.

---

## Workflows (what each one is for)

**Default linear delivery:** same order for Cursor, Claude (`/forge:…`) and Codex (`$forge:…` — see [Commands in your apps](#commands-in-your-apps)).

One nuance from the code: the **handoff menu** and `scripts/shared/skill_chain.py` often recommend using **evaluate** as a quality gate (for example, “evaluate pre” after plan), but the **no-active-sessions** resume helper (`scripts/shared/resume.py`) treats **evaluate as standalone** and does not include it in the hard-coded pipeline order. When in doubt, follow the last handoff menu you saw; use `forge resume`, `/forge:resume`, or `$forge:resume` to pick up an active session.

When intent is still fuzzy, run **sketch** before develop (see [Sketch](#sketch-before-develop)).

| Step | Cursor / Claude | Codex |
|------|-----------------|-------|
| 0 (optional) | `/forge:sketch` | `$forge:sketch` |
| 1 | `/forge:develop` | `$forge:develop` |
| 2 | `/forge:plan` | `$forge:plan` |
| 3 or As Needed | `/forge:evaluate` (e.g. --mode pre or --mode post) | `$forge:evaluate` |
| 4 | `/forge:implement` | `$forge:implement` |
| 5 | `/forge:code-review` | `$forge:code-review` |
| 6 | `/forge:test` | `$forge:test` |
| As Needed | `/forge:diagnose` | `$forge:diagnose` |
| Meta (full loop) | `/forge:iterate` | `$forge:iterate` |

Evaluate and diagnose also run standalone. **Iterate** chains the linear workflow with inner review loops and outer loops until a metric target is met or a max loop count (see [Iterate](#iterate)).

**Plan discovery:** For **evaluate** (`--plan`), **implement** (`--plan`), and **code-review** (`--plan`), Forge searches markdown plans in the repo and in native IDE plan folders — for example `<repo>/.cursor/plans`, `<repo>/.claude/plans`, `<repo>/.codex/plans`, and the same paths under your user home directory (`~/.cursor/plans`, …). Pass a path or keywords.

**Status:** `/forge:status` / `$forge:status`. 

**Resume:** `/forge:resume` / `$forge:resume`.

### Sketch (before develop)

- **Cursor / Claude:** `/forge:sketch`
- **Codex:** `$forge:sketch`

**Sketch organizes intent** when the problem, constraints, or terminology are still fuzzy: one question at a time with a recommended answer, logged in **`memory/sketch-decisions.md`**. It is **not** solution brainstorming (that is develop) and **not** the design spec file. Optional **`--with-domain-docs`** updates `CONTEXT.md` (glossary) and sparse `docs/adr/` per `templates/CONTEXT-FORMAT.md` and `templates/ADR-FORMAT.md`.

Default handoff: **develop**. Protocol: `templates/sketch-protocol.md`.

### Develop

- **Cursor / Claude:** `/forge:develop`
- **Codex:** `$forge:develop`

**Develop is a back-and-forth with you:** surface opportunities (not only bugs), brainstorm and refine requirements, and generate multiple solution directions before anything is “locked.” The step sequence structures that conversation—short rounds of questions, options, and gates—not a one-shot report.

If intent is still messy, run **sketch** first. Then investigate the problem or feature, explore and score options, and converge before plan. Handoff often points to plan (`/forge:plan` or `$forge:plan`) or evaluate (`/forge:evaluate` or `$forge:evaluate`).

**Design spec (develop owns this):** For **medium** and **large** scope, develop produces **`docs/forge/specs/YYYY-MM-DD-<slug>-design.md`** before handoff to plan — not sketch.

**Scope tiers and design spec:** Scope assessment can set **trivial / medium / large** (persisted as **`memory/develop-scope.json`** under the Forge runtime root, e.g. `.codex/forge/`). For **medium** and **large**, step 7 enforces a **design-spec gate**: `.develop-spec-gate.json` beside the develop state file must record a real spec path, completion booleans, and user approval. Strict bypass is opt-in via `forge develop --step 7 --allow-spec-incomplete` with **`--spec-override-reason`** and **`--spec-override-follow-up`** (optional **`--spec-override-requested-by`**). Template: `templates/design-spec.md`.

**Methodologies:** evidence-first investigation and git/history context; 5 Whys (`templates/five-why-protocol.md`); systematic debugging for defects (`templates/systematic-debugging.md`); brainstorming phased for requirements and solution families (`templates/brainstorming.md`, `brainstorming-gates.md`); How-Might-We framing; Pugh / weighted scoring and rubrics (`templates/scoring-rubric.md`); cross-review of investigation; user approval gates.

### Plan

- **Cursor / Claude:** `/forge:plan`
- **Codex:** `$forge:plan`

Turn an approved direction into an implementation plan. Handoff often points to evaluate pre (`/forge:evaluate` or `$forge:evaluate`) or implement (`/forge:implement` / `$forge:implement`).

**Methodologies:** architecture overview before task breakdown; INVEST-style tasks; parallelization / wave planning with explicit dependencies; interface contracts between tasks; risk register with mitigations; pre-mortem (`templates/pre-mortem.md`) before risks; concrete rollback steps (not “revert commits” only); plan review loop and skeleton markers through completion gates.

**Documentation planning (step 6):** audience applicability (`architect_expert`, `technical_operator`, `user`) with justification per tier — not all three required every time; Documentation Definition of Done table; wiki mirrors (`wiki/`, `.wiki/`, `docs/wiki/`) and external wiki checklist rows. Step 7 handoff is blocked until every `<!-- FORGE_SKELETON: … -->` marker is cleared in the plan file (including Documentation).

### Evaluate

- **Cursor / Claude:** `/forge:evaluate`
- **Codex:** `$forge:evaluate`

Structured review: --mode pre (before implementation), --mode post (after), or review. 

**Methodologies:** feasibility and step-level FEASIBLE/RISKY/BLOCKED rating; codebase alignment and risk/dependency surfacing; completeness audit (plan vs code: COMPLETE/PARTIAL/MISSING/EXTRA); correctness, code quality, performance, operational readiness lenses; structured findings JSON sidecars; team dispatch and remediation loops where enabled.

### Implement

- **Cursor / Claude:** `/forge:implement`
- **Codex:** `$forge:implement`

Execute the plan in waves; hands off toward code-review (`/forge:code-review` / `$forge:code-review`).

**Methodologies:** branch/setup and plan detection; wave dispatch with TDD expectations; per-task review loop (self-review, cross-review QA, critic, PM validation) per `templates/review-loop.md`; mutation-testing mental audit; performance and backward-compatibility checks; integration verification; documentation phase writes `.implement-documentation-gate.json` beside the implement state file and clears the plan **Documentation** skeleton marker.

**Documentation gate (step 8):** strict by default — validates gate JSON (`complete`, `audience_matrix` with per-tier justification and `delivery_evidence` when applicable, `external_wiki_checklist` array even if empty) and that the plan no longer contains `<!-- FORGE_SKELETON: DOCUMENTATION -->`. Override only with `--allow-docs-incomplete --docs-override-reason … --docs-override-follow-up …` (optional `--docs-override-requested-by`); override metadata is printed to stderr and embedded in `handoff-implement.md`.

### Code review

- **Cursor / Claude:** `/forge:code-review`
- **Codex:** `$forge:code-review`

Deep, structured review; often feeds test (`/forge:test` / `$forge:test`).

**Methodologies:** mode selection (PR vs deep vs architecture): diff-centric, trace/deep-dive, or SOLID/coupling/cohesion; diff analysis; architecture and security passes; structured discussion and report with severities.

### Test

- **Cursor / Claude:** `/forge:test`
- **Codex:** `$forge:test`

Default run mode; flows mode for end-to-end mock flows. Handoff may push diagnose (`/forge:diagnose` / `$forge:diagnose`).

**Methodologies:** run mode — suite discovery (unit/integration/e2e/perf/property), coverage tooling, execution plan, failure analysis, coverage gaps, reporting. Flows mode — scored recommendation across flow types (scenario, BDD, HTTP-replay, workflow-dry-run); eight progressive quality criteria (realistic journeys, data packs, roles matrix, entry-point ladder, outcome validation, minimal mocking, failure paths, repeatable/double-run); scope, scaffold, author, execute, report phases with pytest reliability checks (fixture teardown/isolation, `tmp_path` usage, deterministic assertions, strict markers, seam-first targeted runs before full sweeps).

### Iterate

- **Cursor / Claude:** `/forge:iterate`
- **Codex:** `$forge:iterate`

Runs **diagnose → plan → evaluate (pre) → implement → evaluate (post) → code-review → test** with **inner loops** until evaluate/code-review gates report no open findings, and **outer loops** until a **target metric** is satisfied or `--max-loops` is reached. Gate JSON files live under runtime memory **`.iterate-gates/`** (for example `diagnose.json`, `evaluate-pre.json`, `metric.json`) so progress stays auditable.

**CLI:** `forge iterate --step 1 --goal "…" --target "accuracy >= 0.9" --max-loops 5` or `--text "… until …, max loops N"`. Advance `--step` as each phase completes.

### Diagnose

- **Cursor / Claude:** `/forge:diagnose`
- **Codex:** `$forge:diagnose`

Evidence-led root-cause analysis and reporting. When the workflow classifies the fix as **`large`** (systemic / needs design before planning), the closing handoff menu defaults to **develop** first, then plan; for **`complex`** (broad but plannable), it defaults to **plan**.

**Methodologies:** Execution playbooks (`templates/diagnose-execution-playbooks.md`); Phase 2 **Reproduce & Observe** with `.diagnose-feedback-loop.json` (step-3 gate, template [`diagnose-feedback-loop.md`](templates/diagnose-feedback-loop.md)); JSON sidecars beside state (problem spec, feedback loop, first-principles, hypotheses, MECE tree, five-whys chains, 20-row technique coverage, barriers when high-severity); orchestrator gates at steps 3–5–7 with **DIAGNOSE ARTIFACT GATE** (override `repro_loop_override_reason` when no loop is possible); **symptom-level root causes rejected** at closure gates; IS/IS-NOT; Cynefin; change analysis; fishbone via hypothesis register (≥10 candidates, ≥4 categories); FMEA via `fmea_score.py`; but-for / Pareto; git hotspots and logs; solutions only for confirmed causes. Skill detail: [`skills/diagnose/SKILL.md`](skills/diagnose/SKILL.md).

**Graphify / architecture:** Historically only the hypothesis register was wired through `orchestrate.py` (graphify community 93); `technique_catalog.md` (community 153) fed the report phase but not decompose/analyze. Playbooks plus sidecar validators close that gap — see [AGENTS.md — Diagnose methodology sidecars](AGENTS.md#diagnose--methodology-sidecars-and-gates) and [`docs/graphify.md`](docs/graphify.md).

### Status

- **Cursor / Claude:** `/forge:status`
- **Codex:** `$forge:status`

Dashboard of handoffs and active sessions.

**Methodologies:** follows `skills/status/SKILL.md` — composite view from `memory/` handoffs, `state/` files, and findings; suggests next workflow from pipeline position (inspection-only).

### Resume

- **Cursor / Claude:** `/forge:resume`
- **Codex:** `$forge:resume`

**What it does:** discovers active workflow **JSON** sessions, prints **continuity** context from `resume-context.json`, a **memory** block (prefers `forge-memory-synthesis.md`, then `current-step.md`, then handoffs), and optional **Graphify** status plus a short **GRAPH_REPORT** excerpt when those files exist. Emits the next `forge <skill> --step … --state …` line when there is a single clear session; with **multiple** active sessions, the **menu is authoritative** and synthesis/Graphify are annotation only. If snapshot and JSON state **disagree**, output shows **two** resume options and asks which source to trust before treating the command as auto-run. **Cleanup** (`--cleanup`, `--force`, `--all-stale`) lists or deletes stale state files.

**Methodologies:** active-session detection, cross-session conflict warnings from other skills, step inference from state, retry guard after repeated same-step failures, cleanup dry-run vs forced delete; completion checks include both `completed_at` and legacy max-step states.

### Ship (finalize)

- **Cursor / Claude:** `/forge:ship`
- **Codex:** `$forge:ship`

**Ship** is not a delivery pipeline skill — it finalizes coding work: preflight, commit, push, open or update a PR, merge, and publish (PyPI/npm/etc.). Run **`forge ship --step 1`** (or `/forge:ship`) before commit/PR when `graphify-out/` exists; that step prints the **GRAPHIFY** banner and starts a background graph refresh (see [`docs/graphify.md`](docs/graphify.md)). Cursor also ships a dedicated skill at [`.cursor/skills/ship/SKILL.md`](.cursor/skills/ship/SKILL.md). Handoff menus after implement, code-review, and test often list **ship** as an alternative.

---

## OpenAI Codex

After `forge install --codex`, skills live under `~/.codex/skills/forge/<folder>/SKILL.md`. Folders use hyphenated names (`forge-develop/`, `forge-diagnose/`, …) because `:` is not valid in file paths. Each `SKILL.md` sets `name: forge:<subcommand>` (for example `name: forge:diagnose`), which Codex surfaces as `$forge:diagnose`. The body runs `forge …` via `<invoke cmd="…"/>`.

Invoke with `$forge:…` (mention / skill picker), `/use` with the skill name, `/skills`, or implicit matching on `description`. When transcript output shows `forge: …` handoff labels, your next step in Codex is the matching `$forge:…`. The `forge` binary is what skills run under the hood; you do not type `forge …` as the Codex-side workflow entrypoint ([Advanced](#advanced-terminal-and-ci) for shells and CI).

**Graphify + delegation:** `forge install --codex` merges **`developer_instructions`** into `~/.codex/config.toml` when empty or matching the prior Forge snippet. The text **leads with mandatory Graphify rules** (read `GRAPH_REPORT.md` before codebase search; run **`forge ship --step 1`** for the ship-time GRAPHIFY banner; background refresh may run on workflow `--step` without blocking), then Forge delegation (sub-agents + session opt-in). Source of truth: **`forge_next/graphify_policy.py`**.

**Sub-agents (delegation):** Forge workflows expect Codex to allow `spawn_agent` / `close_agent` without you typing extra “use sub-agents” wording. If you already customized `developer_instructions`, run **`forge codex-agents --force`** after upgrading **forge-next** so Graphify + delegation stay current. Restart Codex after changing config.

For agent lifecycle (every `spawn_agent` paired with `close_agent` across steps), follow [AGENTS.md](AGENTS.md) and `templates/codex-runtime.md` — that is separate from `developer_instructions`.

Evaluate note: the evaluate workflow persists a local `.evaluate-state.json` and step findings sidecars (`.evaluate-findings-step*.json`). Details live in [AGENTS.md](AGENTS.md).

---

## Claude Code

After `forge install --claude`, slash commands live under `~/.claude/commands/forge/`. The installer also runs **`forge claude-graphify`**, which merges **Graphify hooks** into `~/.claude/settings.json`:

- **SessionStart** — remind when `graphify-out/` exists  
- **PreToolUse** — **Grep**, **Glob**, **Read**, and search-like **Bash**  
- **UserPromptSubmit** — when the prompt mentions `forge:` / `$forge:`  

Re-run `forge claude-graphify` after `pipx upgrade forge-next` (hooks use your pipx Python path, not `/usr/bin/python`). Each workflow command includes a **Hard rule — Graphify** section (read the map before search; ship-time refresh via **`forge ship --step 1`**). Hooks may remind on search tools; workflow `--step` does **not** print per-step GRAPHIFY banners. See [`docs/graphify.md`](docs/graphify.md).

**Cursor sub-agents:** `forge cursor-subagent-hooks` writes `.cursor/hooks.json` for Task lifecycle. Suppress with `FORGE_SKIP_SUBAGENT_LIFECYCLE=1`. See [AGENTS.md](AGENTS.md).

---

## This repository vs PyPI

- `forge-next` on PyPI installs terminal `forge` and bundled orchestrators.
- This repo is the source for `prompts/`, `templates/`, `agents/`, `scripts/`, and **`integrations/`** (installable slash commands and Codex skills — exhaustive per `commands.json`).
- **`skills/`** holds agent-facing `SKILL.md` files for most workflows (not all 14: **ship** and **iterate** live under `integrations/` and `.cursor/skills/ship/`). Edit repo-root `prompts/` and `templates/` for orchestration content; `forge_next/assets/` mirrors them at release.

PyPI: [pypi.org/project/forge-next](https://pypi.org/project/forge-next/)

Source: [github.com/mderganc/forge](https://github.com/mderganc/forge)

---

## Advanced: terminal and CI

Outside Codex chat, hooks and automation call `forge <subcommand>` with a space (e.g. `forge plan --step 1`). That is the same engine as `/forge:plan` (Cursor/Claude) and `$forge:plan` (Codex skills invoke this binary for you). `forge --help` lists flags.

**Automation / CI:** Common flags:

| Variable | Effect |
|----------|--------|
| **`FORGE_SKIP_SESSION_OPTIN=1`** | Suppress step-1 **session opt-in** banner |
| **`FORGE_SKIP_GRAPHIFY=1`** | Disable ship GRAPHIFY banner and automatic background refresh |
| **`FORGE_SKIP_GRAPHIFY_REFRESH=1`** | Suppress background refresh only (keep ship banner) |
| **`FORGE_SKIP_AUTO_CLOSE=1`** | Disable step-1 auto-close of superseded sessions |

Full list: [`docs/environment.md`](docs/environment.md).

**Graphify (optional):** Build the graph with `forge graphify refresh` (or `FORGE_GRAPHIFY_COMMAND`); optional `forge graphify install-hook` for post-commit refresh. Workflow `--step` may spawn **debounced background** refresh when `graphify-out/` exists; the orchestrator **GRAPHIFY** banner prints on **`forge ship --step 1`** only. Claude hooks (`forge claude-graphify`) and Codex policy (`forge codex-agents`) enforce reading the map before search. After `pipx upgrade forge-next`, re-run those two commands. Full guide: [`docs/graphify.md`](docs/graphify.md).

---

## Contributing

Orchestration lives in `scripts/shared/` (`orchestrator.py`, `skill_chain.py`, `resume.py`, `session_store.py`). Keep [AGENTS.md](AGENTS.md), [`docs/README.md`](docs/README.md), and `skills/` aligned with behavior.

**Versions:** Any change that affects the PyPI package or editor integrations must bump semver in **[`pyproject.toml`](pyproject.toml)** (and the Cursor plugin [`plugin.json`](integrations/cursor-plugin/.cursor-plugin/plugin.json) when that bundle changes). Follow **[Versioning](AGENTS.md#versioning)** in [AGENTS.md](AGENTS.md): use **patch** for narrow fixes, **minor** for additive behavior, **major** for breaking contracts.

**PyPI:** If you bump `project.version`, **[build and upload to PyPI](AGENTS.md#pypi)** the same release (`python -m build`, `python -m twine check dist/*`, `python -m twine upload dist/*`; or `scripts/release/publish_pypi.sh`). Users installing via `pipx install forge-next` must see the new version on PyPI (`pipx upgrade forge-next`).

**Integration bundles:** After changing `integrations/cursor-plugin/`, `integrations/claude/commands/`, or `integrations/codex/skills/`, run `pytest tests/test_integration_install_layout.py` (guards layout vs **[`integrations/spec/commands.json`](integrations/spec/commands.json)**).

Tests:

- `python -m pytest`
- `python scripts/smoke.py`
