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

**Note:** In Cursor or Claude, typing `/diagn…` finds slash commands quickly. In Codex, type `$forge:` or pick the skill — user-facing IDs match `$forge:<subcommand>` (same spelling as `/forge:<subcommand>`, with `$` instead of `/`).

---

## Overview

- **App-first:** Cursor and Claude Code use `/forge:…`; Codex uses `$forge:…`. See [OpenAI Codex](#openai-codex).
- **Session-safe:** Repo state lives under `.codex/forge/` by default. Older trees may still use `.codex/forge-codex/` until migrated. If `.codex` cannot be a directory, Forge falls back to `.forge/`. Stop anytime; continue with `forge resume`, `/forge:resume` (Cursor/Claude), or `$forge:resume` (Codex).
- **Handoffs:** On the last step, the numbered menu may show `forge: …` labels in the transcript. Reply `yes`, `1`, or `default`, or pick an option, then run the next step as `/forge:…` (Cursor/Claude) or `$forge:…` (Codex). Outside Codex, use the `forge …` command line from [Advanced: terminal and CI](#advanced-terminal-and-ci).
- **Integrations:** `forge install` and `forge uninstall` lay down Cursor, Claude, and Codex wrappers.

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

Or only what you use:

```bash
forge install --cursor
forge install --claude
forge install --codex
```

Options (defaults are usually fine): `--ref`, `--repo-url`, `--cursor-dir`, `--claude-dir`, `--codex-dir`.

**Note:** Running from Windows will install in the Windows Cursor/Claude/Codex locations, while WSL will use the WSL locations.

### 3. First run in the app (not in a terminal)

1. Check setup: `/forge:doctor` (Cursor/Claude), or `$forge:doctor` (Codex).
2. Start planning: `/forge:plan` (Cursor/Claude), or `$forge:plan` (Codex).
3. Follow the printed steps. Re-run the same slash command (Cursor/Claude), or the next `$forge:…` (Codex). If the transcript shows `forge: …`, treat it as a label and use the matching `/forge:…` or `$forge:…` as appropriate.

Work in another folder than the editor root only when your integration documents it (some flows pass a repo path through the launcher).

After a new `forge-next` release on PyPI, upgrade with `pipx upgrade forge-next` (or reinstall with `pipx install forge-next --force`).

---

## Commands in your apps

| Workflow | Cursor / Claude | Codex |
|----------|-----------------|-------|
| Investigation before plan | `/forge:develop` | `$forge:develop` |
| Check install / environment | `/forge:doctor` | `$forge:doctor` |
| Implementation plan | `/forge:plan` | `$forge:plan` |
| Plan / implementation review | `/forge:evaluate` | `$forge:evaluate` |
| Execute plan in waves | `/forge:implement` | `$forge:implement` |
| Structured code review | `/forge:code-review` | `$forge:code-review` |
| Tests or mock-flow authoring | `/forge:test` | `$forge:test` |
| Root-cause / incident analysis | `/forge:diagnose` | `$forge:diagnose` |
| Dashboard | `/forge:status` | `$forge:status` |
| Resume or cleanup | `/forge:resume` | `$forge:resume` |

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

## Workflows (what each one is for)

**Default linear delivery:** same order for Cursor, Claude (`/forge:…`) and Codex (`$forge:…` — see [Commands in your apps](#commands-in-your-apps)).

One nuance from the code: the **handoff menu** and `scripts/shared/skill_chain.py` often recommend using **evaluate** as a quality gate (for example, “evaluate pre” after plan), but the **no-active-sessions** resume helper (`scripts/shared/resume.py`) treats **evaluate as standalone** and does not include it in the hard-coded pipeline order. When in doubt, follow the last handoff menu you saw; use `forge resume`, `/forge:resume`, or `$forge:resume` to pick up an active session.

| Step | Cursor / Claude | Codex |
|------|-----------------|-------|
| 1 | `/forge:develop` | `$forge:develop` |
| 2 | `/forge:plan` | `$forge:plan` |
| 3 or As Needed | `/forge:evaluate` (e.g. --mode pre or --mode post) | `$forge:evaluate` |
| 4 | `/forge:implement` | `$forge:implement` |
| 5 | `/forge:code-review` | `$forge:code-review` |
| 6 | `/forge:test` | `$forge:test` |
| As Needed | `/forge:diagnose` | `$forge:diagnose` |

Evaluate and diagnose also run standalone. 

**Status:** `/forge:status` / `$forge:status`. 

**Resume:** `/forge:resume` / `$forge:resume`.

### Develop

- **Cursor / Claude:** `/forge:develop`
- **Codex:** `$forge:develop`

Investigate the problem or feature, explore options, converge before plan. Handoff often points to plan (`/forge:plan` or `$forge:plan`) or evaluate (`/forge:evaluate` or `$forge:evaluate`).

**Methodologies:** evidence-first investigation and git/history context; 5 Whys (`templates/five-why-protocol.md`); systematic debugging for defects (`templates/systematic-debugging.md`); brainstorming phased for requirements and solution families (`templates/brainstorming.md`, `brainstorming-gates.md`); How-Might-We framing; Pugh / weighted scoring and rubrics (`templates/scoring-rubric.md`); cross-review of investigation; user approval gates.

### Plan

- **Cursor / Claude:** `/forge:plan`
- **Codex:** `$forge:plan`

Turn an approved direction into an implementation plan. Handoff often points to evaluate pre (`/forge:evaluate` or `$forge:evaluate`) or implement (`/forge:implement` / `$forge:implement`).

**Methodologies:** architecture overview before task breakdown; INVEST-style tasks; parallelization / wave planning with explicit dependencies; interface contracts between tasks; risk register with mitigations; pre-mortem (`templates/pre-mortem.md`) before risks; concrete rollback steps (not “revert commits” only); plan review loop and skeleton markers through completion gates.

### Evaluate

- **Cursor / Claude:** `/forge:evaluate`
- **Codex:** `$forge:evaluate`

Structured review: --mode pre (before implementation), --mode post (after), or review. 

**Methodologies:** feasibility and step-level FEASIBLE/RISKY/BLOCKED rating; codebase alignment and risk/dependency surfacing; completeness audit (plan vs code: COMPLETE/PARTIAL/MISSING/EXTRA); correctness, code quality, performance, operational readiness lenses; structured findings JSON sidecars; team dispatch and remediation loops where enabled.

### Implement

- **Cursor / Claude:** `/forge:implement`
- **Codex:** `$forge:implement`

Execute the plan in waves; hands off toward code-review (`/forge:code-review` / `$forge:code-review`).

**Methodologies:** branch/setup and plan detection; wave dispatch with TDD expectations; per-task review loop (self-review, cross-review QA, critic, PM validation) per `templates/review-loop.md`; mutation-testing mental audit; performance and backward-compatibility checks; integration and documentation passes; handoff to review.

### Code review

- **Cursor / Claude:** `/forge:code-review`
- **Codex:** `$forge:code-review`

Deep, structured review; often feeds test (`/forge:test` / `$forge:test`).

**Methodologies:** mode selection (PR vs deep vs architecture): diff-centric, trace/deep-dive, or SOLID/coupling/cohesion; diff analysis; architecture and security passes; structured discussion and report with severities.

### Test

- **Cursor / Claude:** `/forge:test`
- **Codex:** `$forge:test`

Default run mode; flows mode for end-to-end mock flows. Handoff may push diagnose (`/forge:diagnose` / `$forge:diagnose`).

**Methodologies:** run mode — suite discovery (unit/integration/e2e/perf/property), coverage tooling, execution plan, failure analysis, coverage gaps, reporting. Flows mode — scored recommendation across flow types (scenario, BDD, HTTP-replay, workflow-dry-run); eight progressive quality criteria (realistic journeys, data packs, roles matrix, entry-point ladder, outcome validation, minimal mocking, failure paths, repeatable/double-run); scope, scaffold, author, execute, report phases.

### Diagnose

- **Cursor / Claude:** `/forge:diagnose`
- **Codex:** `$forge:diagnose`

Evidence-led root-cause analysis and reporting.

**Methodologies:** IS/IS-NOT matrix; Cynefin classification; change analysis (last known good, deltas); MECE cause tree; software fishbone (CODE/CONFIG/DATA/INFRA/DEPS/ENV); 5 Whys; FMEA RPN scoring; hypothesis test cycles; counterfactual (“but-for”) checks; Pareto; git hotspots and log patterns where applicable; solution options and structured report.

### Status

- **Cursor / Claude:** `/forge:status`
- **Codex:** `$forge:status`

Dashboard of handoffs and active sessions.

**Methodologies:** follows `skills/status/SKILL.md` — composite view from `memory/` handoffs, `state/` files, and findings; suggests next workflow from pipeline position (inspection-only).

### Resume

- **Cursor / Claude:** `/forge:resume`
- **Codex:** `$forge:resume`

Next step command(s) and cleanup; mirrors terminal `forge resume` when you need flags not exposed in the app.

**Methodologies:** active-session detection, conflict vs non-conflicting workflows, step inference from state, cleanup dry-run vs forced delete; operational, not domain-method heavy.

---

## OpenAI Codex

After `forge install --codex`, skills live under `~/.codex/skills/forge/<folder>/SKILL.md`. Folders use hyphenated names (`forge-develop/`, `forge-diagnose/`, …) because `:` is not valid in file paths. Each `SKILL.md` sets `name: forge:<subcommand>` (for example `name: forge:diagnose`), which Codex surfaces as `$forge:diagnose`. The body runs `forge …` via `<invoke cmd="…"/>`.

Invoke with `$forge:…` (mention / skill picker), `/use` with the skill name, `/skills`, or implicit matching on `description`. When transcript output shows `forge: …` handoff labels, your next step in Codex is the matching `$forge:…`. The `forge` binary is what skills run under the hood; you do not type `forge …` as the Codex-side workflow entrypoint ([Advanced](#advanced-terminal-and-ci) for shells and CI).

Optional `~/.codex/config.toml`: set `developer_instructions` so Forge workflows count as permission to dispatch the Forge agent team, including `spawn_agent` / `close_agent` lifecycle. Copy the full contract from [AGENTS.md](AGENTS.md) and `templates/codex-runtime.md`, not a one-line summary.

Evaluate note: the evaluate workflow persists a local `.evaluate-state.json` and step findings sidecars (`.evaluate-findings-step*.json`). Details live in [AGENTS.md](AGENTS.md).

---

## This repository vs PyPI

- `forge-next` on PyPI installs terminal `forge` and bundled orchestrators.
- This repo is the source for `skills/`, `prompts/`, `templates/`, `agents/`, `scripts/`.

PyPI: [pypi.org/project/forge-next](https://pypi.org/project/forge-next/)

Source: [github.com/mderganc/forge](https://github.com/mderganc/forge)

---

## Advanced: terminal and CI

Outside Codex chat, hooks and automation call `forge <subcommand>` with a space (e.g. `forge plan --step 1`). That is the same engine as `/forge:plan` (Cursor/Claude) and `$forge:plan` (Codex skills invoke this binary for you). `forge --help` lists flags.

---

## Contributing

Orchestration lives in `scripts/shared/` (`orchestrator.py`, `skill_chain.py`, `resume.py`). Keep [AGENTS.md](AGENTS.md) and `skills/` aligned with behavior.

**Versions:** Any change that affects the PyPI package or editor integrations must bump semver in **[`pyproject.toml`](pyproject.toml)** (and the Cursor plugin [`plugin.json`](integrations/cursor-plugin/.cursor-plugin/plugin.json) when that bundle changes). Follow **[Versioning](AGENTS.md#versioning)** in [AGENTS.md](AGENTS.md): use **patch** for narrow fixes, **minor** for additive behavior, **major** for breaking contracts.

**PyPI:** If you bump `project.version`, **[build and upload to PyPI](AGENTS.md#pypi)** the same release (`python -m build`, `python -m twine check dist/*`, `python -m twine upload dist/*`; or `scripts/release/publish_pypi.sh`). Users installing via `pipx install forge-next` must see the new version on PyPI (`pipx upgrade forge-next`).

**Integration bundles:** After changing `integrations/cursor-plugin/`, `integrations/claude/commands/`, or `integrations/codex/skills/`, run `pytest tests/test_integration_install_layout.py` (guards layout vs **[`integrations/spec/commands.json`](integrations/spec/commands.json)**).

Tests:

- `python -m pytest`
- `python scripts/smoke.py`
