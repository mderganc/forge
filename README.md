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
- **Session-safe:** Repo state lives under `.codex/forge/` by default. Older trees may still use `.codex/forge-codex/` until migrated. If `.codex` is a file, read-only (common in Codex sandboxes), or otherwise not writable, Forge falls back to `.forge/`. Stop anytime; continue with `forge resume`, `/forge:resume` (Cursor/Claude), or `$forge:resume` (Codex). Each skill save also updates **`state/resume-context.json`** (continuity snapshot for new chats) and **`memory/forge-memory-synthesis.md`** (rollup of `project.md`, `current-step.md`, and recent handoffs). Resume prints memory + optional **Graphify** codebase status; if the snapshot disagrees with live JSON state, output asks you to pick **state-based** vs **snapshot-based** continuation before auto-running the next step.
- **Handoffs:** On the last step, the orchestrator emits a **`handoff-multiselect`** block (for Cursor/Claude **AskQuestion** with `allow_multiple: true`) plus a text fallback. Labels use `/forge:…` (Cursor/Claude) or `$forge:…` (Codex). Reply `yes`, `1`, or pick options; see [AGENTS.md](AGENTS.md). Downstream step-1 intake consumes handoffs (read + close).
- **Per-skill run memory:** Every workflow run appends an auditable entry to `memory/<skill>-runs.jsonl` (for example `plan-runs.jsonl`), retaining the most recent 30 entries with timestamp, phase/step, short summary, session linkage, and handoff linkage when present.
- **Integrations:** `forge install` and `forge uninstall` lay down Cursor, Claude, and Codex wrappers. Install output includes optional **Graphify** setup (CLI or `FORGE_GRAPHIFY_COMMAND`, `forge graphify refresh`, `install-hook` / `uninstall-hook`) for codebase context in `forge resume` — see [`docs/graphify.md`](docs/graphify.md).
- **Memory rollup:** each time skill state is saved, Forge refreshes **`memory/forge-memory-synthesis.md`** as an explicit merge of `project.md`, `current-step.md`, and recent handoffs so resume can open one synthesized narrative (see `templates/memory-protocol.md`).

---

## Optional: Beads (issue tracking)

Workflows can hook **[Beads](https://github.com/steveyegge/beads)** (`bd` CLI) so epics, findings, tasks, and dependencies stay in sync with Forge memory and handoffs. It is **optional**: if Beads is not available, prompts fall back to memory files and sequential IDs (see `templates/beads-integration.md`).

- **Canonical guide:** `templates/beads-integration.md` (epic layout, `bd` examples, degraded mode).
- **Cross-references:** `templates/memory-protocol.md`, `templates/handoff-protocol.md` (Beads section in status handoffs).
- **Runtime:** design startup checks Beads (`prompts/develop/startup.md` — legacy prompt path). Skill state includes a `beads_available` flag in `scripts/shared/orchestrator.py`, but whether Beads is used is driven by prompts and `project.md` (“beads: available/unavailable”), not by automatic detection in the orchestrator.

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

After a new `forge-next` release on PyPI, upgrade with `pipx upgrade forge-next` (or reinstall with `pipx install forge-next --force`). Pin a specific version when reproducibility matters, for example `pipx install 'forge-next==0.19.2'` (see `project.version` in `pyproject.toml`).

---

## Commands in your apps

All **14** workflows are defined in [`integrations/spec/commands.json`](integrations/spec/commands.json). Each command below uses the same layout: **invoke table**, purpose, when to use, artifacts, and methodologies.

**Terminal:** `forge <subcommand> …` (for example `forge design --step 1`, `forge graphify refresh`). **`forge develop`** is a **deprecated alias** for **`forge design`** (stderr warning).

**Sessions:** steps 2+ accept **`--session <id>`** when multiple active sessions exist — see [`docs/sessions.md`](docs/sessions.md).

**Codex:** `forge install --codex` installs skills under `~/.codex/skills/forge/` — see [`integrations/codex/README.md`](integrations/codex/README.md).

### Quick index

| Command | Anchor |
|---------|--------|
| sketch | [Sketch](#sketch) |
| design | [Design](#design) |
| plan | [Plan](#plan) |
| evaluate | [Evaluate](#evaluate) |
| implement | [Implement](#implement) |
| code-review | [Code review](#code-review) |
| test | [Test](#test) |
| diagnose | [Diagnose](#diagnose) |
| iterate | [Iterate](#iterate) |
| resume | [Resume](#resume) |
| status | [Status](#status) |
| doctor | [Doctor](#doctor) |
| ship | [Ship](#ship) |
| graphify | [Graphify](#graphify) |

### Delivery pipeline

Default linear order (evaluate and diagnose also run standalone):

| Step | Cursor / Claude | Codex |
|------|-----------------|-------|
| 0 (optional) | `/forge:sketch` | `$forge:sketch` |
| 1 | `/forge:design` | `$forge:design` |
| 2 | `/forge:plan` | `$forge:plan` |
| 3 (as needed) | `/forge:evaluate` | `$forge:evaluate` |
| 4 | `/forge:implement` | `$forge:implement` |
| 5 | `/forge:code-review` | `$forge:code-review` |
| 6 | `/forge:test` | `$forge:test` |

Handoff menus may recommend **evaluate** as a quality gate; **`forge resume`** treats evaluate as standalone when no session is active — follow the last handoff menu when in doubt. **Ship** is a finalize utility (not a pipeline step); handoff menus after implement, code-review, and test often list it.

When intent is fuzzy, run [sketch](#sketch) before [design](#design).

**Plan discovery:** For **evaluate** (`--plan`), **implement**, and **code-review**, Forge searches markdown plans in the repo and native IDE plan folders (`.cursor/plans`, `.claude/plans`, `.codex/plans`, and `~/.cursor/plans`, …).

---

### Sketch

| | Cursor / Claude | Codex | Terminal |
|--|-----------------|-------|----------|
| Invoke | `/forge:sketch` | `$forge:sketch` | `forge sketch --step 1` |

**What it does:** Organizes intent when the problem, constraints, or terminology are still fuzzy — one question at a time with a recommended answer.

**When to use:** Before design when requirements are unclear. Optional **`--with-domain-docs`** updates `CONTEXT.md` and sparse `docs/adr/`.

**Artifacts:** `memory/sketch-decisions.md` under `.codex/forge/memory/`.

**Default handoff:** [design](#design). Protocol: `templates/sketch-protocol.md`.

---

### Design

| | Cursor / Claude | Codex | Terminal |
|--|-----------------|-------|----------|
| Invoke | `/forge:design` | `$forge:design` | `forge design --step 1` |

**What it does:** Back-and-forth discovery — surface opportunities, brainstorm requirements, explore and score solution directions before planning.

**When to use:** After sketch (if needed) or when you have a defined feature/problem. Read-only on the codebase unless the user explicitly allows edits.

**Artifacts:** Session memory under `.codex/forge/memory/`; **`memory/design-scope.json`** (legacy `develop-scope.json` still read); for **medium/large** scope, named spec **`docs/forge/specs/YYYY-MM-DD-<slug>-design.md`** and gate **`.design-spec-gate.json`** (legacy `.develop-spec-gate.json` still read).

**Notable flags:** `--quick`; step 7 bypass: `--allow-spec-incomplete` with override reason/follow-up.

**Deprecated:** `forge develop` / `/forge:develop` / `$forge:develop` alias design for one release cycle.

**Default handoff:** [plan](#plan) or [evaluate](#evaluate).

**Methodologies:** evidence-first investigation; 5 Whys; systematic debugging; brainstorming gates; HMW framing; Pugh scoring; cross-review; user approval gates. Template: `templates/design-spec.md`.

---

### Plan

| | Cursor / Claude | Codex | Terminal |
|--|-----------------|-------|----------|
| Invoke | `/forge:plan` | `$forge:plan` | `forge plan --step 1` |

**What it does:** Turns an approved direction into a concrete implementation plan with waves, tasks, and documentation sections.

**Artifacts:** Plan file under `memory/plans/`; `memory/planner.md`.

**Default handoff:** [evaluate](#evaluate) (pre) or [implement](#implement).

**Methodologies:** architecture overview; INVEST tasks; parallelization map; risk register; pre-mortem; skeleton markers through step 7. Documentation step 6: audience matrix and wiki checklist.

---

### Evaluate

| | Cursor / Claude | Codex | Terminal |
|--|-----------------|-------|----------|
| Invoke | `/forge:evaluate` | `$forge:evaluate` | `forge evaluate --step 1 --mode pre` |

**What it does:** Structured plan critique — **`--mode pre`** (before implementation) or **`--mode post`** (after). For full-team code review, use [code-review](#code-review) (`evaluate --mode review` is deprecated).

**Artifacts:** `.evaluate-state.json` and `.evaluate-findings-step<N>.json` sidecars.

**Methodologies:** feasibility ratings; completeness audit; correctness, quality, performance, operational readiness lenses; team dispatch when enabled.

---

### Implement

| | Cursor / Claude | Codex | Terminal |
|--|-----------------|-------|----------|
| Invoke | `/forge:implement` | `$forge:implement` | `forge implement --step 1` |

**What it does:** Executes the plan in waves with per-task review loops.

**Artifacts:** `handoff-implement.md`; `.implement-documentation-gate.json` at step 8.

**Default handoff:** [code-review](#code-review).

**Methodologies:** branch setup; wave dispatch; review loop per `templates/review-loop.md`; integration check; documentation gate (step 8).

---

### Code review

| | Cursor / Claude | Codex | Terminal |
|--|-----------------|-------|----------|
| Invoke | `/forge:code-review` | `$forge:code-review` | `forge code-review --step 1` |

**What it does:** Structured PR/diff/architecture review with Pass A (spec) and Pass B (engineering quality).

**Artifacts:** `memory/code-review-report.md`; step 3 runs structural probes (pyscn/skylos on Python repos) — see [`docs/structural-quality.md`](docs/structural-quality.md).

**Default handoff:** [test](#test) or [ship](#ship).

**Methodologies:** mode selection (PR / deep / architecture); two-pass framework; team dispatch; discussion and report.

---

### Test

| | Cursor / Claude | Codex | Terminal |
|--|-----------------|-------|----------|
| Invoke | `/forge:test` | `$forge:test` | `forge test --step 1` |

**What it does:** Run test suites (**run** mode) or author mock flows (**`--mode flows`**).

**Artifacts:** `memory/test-report.md`; flows mode updates scenario index when parseable.

**Default handoff:** [diagnose](#diagnose) on failures, or [ship](#ship).

**Methodologies:** discovery, execution, failure analysis, coverage gaps; flows mode — eight quality criteria and pytest reliability checks.

---

### Diagnose

| | Cursor / Claude | Codex | Terminal |
|--|-----------------|-------|----------|
| Invoke | `/forge:diagnose` | `$forge:diagnose` | `forge diagnose --step 1` |

**What it does:** Evidence-led root-cause analysis with gated JSON sidecars.

**When to use:** Incidents, regressions, flaky failures. Handoff for **`large`** fixes defaults to [design](#design); **`complex`** defaults to [plan](#plan).

**Methodologies:** playbooks in `templates/diagnose-execution-playbooks.md`; 5 Whys; hypothesis register; technique coverage. Detail: [`skills/diagnose/SKILL.md`](skills/diagnose/SKILL.md).

---

### Iterate

| | Cursor / Claude | Codex | Terminal |
|--|-----------------|-------|----------|
| Invoke | `/forge:iterate` | `$forge:iterate` | `forge iterate --step 1 --goal "…"` |

**What it does:** Meta-workflow chaining diagnose → plan → evaluate → implement → code-review → test with inner and outer loops until metrics or max loops.

**Artifacts:** `.iterate-gates/` under runtime memory.

**CLI:** `--target "accuracy >= 0.9" --max-loops 5` or `--text "… until …, max loops N"`.

---

### Resume

| | Cursor / Claude | Codex | Terminal |
|--|-----------------|-------|----------|
| Invoke | `/forge:resume` | `$forge:resume` | `forge resume` |

**What it does:** Discovers active sessions, prints continuity from `resume-context.json` and memory synthesis, suggests the next `forge <skill> --step …` line.

**When to use:** After interruption; use **`--cleanup`** (dry-run) or **`--cleanup --force`** to remove stale state.

**Behavior:** With multiple active sessions the menu is authoritative. Snapshot vs JSON disagreement offers two resume paths. See [`skills/resume/SKILL.md`](skills/resume/SKILL.md).

---

### Status

| | Cursor / Claude | Codex | Terminal |
|--|-----------------|-------|----------|
| Invoke | `/forge:status` | `$forge:status` | `forge status` |

**What it does:** Dashboard of handoffs, active sessions, and suggested next workflow (inspection only).

**Behavior:** Composite view from `memory/`, `sessions/`, and legacy `state/`. See [`skills/status/SKILL.md`](skills/status/SKILL.md).

---

### Doctor

| | Cursor / Claude | Codex | Terminal |
|--|-----------------|-------|----------|
| Invoke | `/forge:doctor` | `$forge:doctor` | `forge doctor` |

**What it does:** Checks installation, PATH, encoding, runtime root, and common misconfiguration.

**When to use:** First run in a repo; after `pipx install forge-next` or integration install.

---

### Ship

| | Cursor / Claude | Codex | Terminal |
|--|-----------------|-------|----------|
| Invoke | `/forge:ship` | `$forge:ship` | `forge ship --step 1` |

**What it does:** Finalizes coding work — preflight, commit, push, PR, merge, publish (PyPI/npm). **Not** a delivery pipeline step.

**When to use:** After implement, code-review, or test when you are ready to land changes. Run step 1 before commit/PR when `graphify-out/` exists (GRAPHIFY banner + background refresh). Cursor skill: [`.cursor/skills/ship/SKILL.md`](.cursor/skills/ship/SKILL.md).

---

### Graphify

| | Cursor / Claude | Codex | Terminal |
|--|-----------------|-------|----------|
| Invoke | `/forge:graphify` | `$forge:graphify` | `forge graphify refresh` |

**What it does:** Optional codebase knowledge graph — refresh index, install/uninstall post-commit hook.

**When to use:** Setup and troubleshooting; agents read `graphify-out/GRAPH_REPORT.md` before broad search. Full guide: [`docs/graphify.md`](docs/graphify.md).

**Note:** CLI-only helpers `forge structural-tools` and `forge structural-probes` are documented in [`docs/structural-quality.md`](docs/structural-quality.md) (not slash commands).

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
- **Handoff closure:** Handoffs are consumed on step-1 intake of downstream skills (for example plan consumes design handoff, code-review consumes implement handoff, test consumes code-review/implement handoffs).
- **Session completeness:** Active-session detection treats a run as complete when either `completed_at` is set or legacy state reached max step (`current_step >= max_step` and `last_completed_step >= max_step`).
- **Cleanup behavior:** `forge resume --cleanup` removes stale session directories and legacy flat state files (dry-run by default; `--force` to delete). Env: `FORGE_SESSION_MAX_AGE_DAYS` (default `7`), `FORGE_SKIP_SESSION_CLEANUP=1` to disable automatic archive of old sessions.
- **Auto-close on step 1:** Starting a pipeline skill removes superseded session JSON when a handoff exists, when you move forward in the pipeline, or when a step-1-only session was abandoned (see [AGENTS.md](AGENTS.md) State Lifecycle). `forge status` / `forge doctor` report remaining leaks.

---

## OpenAI Codex

After `forge install --codex`, skills live under `~/.codex/skills/forge/<folder>/SKILL.md`. Folders use hyphenated names (`forge-design/`, `forge-diagnose/`, …) because `:` is not valid in file paths. Each `SKILL.md` sets `name: forge:<subcommand>` (for example `name: forge:diagnose`), which Codex surfaces as `$forge:diagnose`. The body runs `forge …` via `<invoke cmd="…"/>`.

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
