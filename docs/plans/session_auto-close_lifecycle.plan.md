---
name: Session auto-close lifecycle
overview: "Add systematic session closure when starting a new Forge skill: auto-archive leaked JSON state when handoffs exist, when pipeline moves forward, or when sessions are abandoned at step 1; expand cleanup coverage and surface leaks in status/doctor."
todos:
  - id: orchestrator-auto-close
    content: Add PIPELINE_SKILL_ORDER, is_step1_abandoned, auto_close_superseded_sessions + FORGE_SKIP_AUTO_CLOSE in scripts/shared/orchestrator.py
    status: pending
  - id: wire-step1-handlers
    content: Call auto_close from handle_step_1 in plan, develop, implement, code_review, test, diagnose orchestrators
    status: pending
  - id: expand-cleanup-glob
    content: Align _all_state_files / _cleanup_candidates with _state_path_candidates (parallel + cwd custom state)
    status: pending
  - id: status-doctor-warnings
    content: Add leak detection warnings to forge status and forge doctor in forge_next/cli.py
    status: pending
  - id: tests-regressions
    content: Add regression tests for auto-close rules, opt-out, and expanded cleanup
    status: pending
  - id: docs-agents
    content: Update AGENTS.md, skills/resume/SKILL.md, and README state lifecycle section
    status: pending
isProject: false
---

# Forge session auto-close and leak prevention

## Problem (root cause)

Session JSON is **created on step 1** ([`save_state`](scripts/shared/orchestrator.py) in every skill's `handle_step_1`) but **deleted only on the final orchestrator step** (`clear_state_file` after `write_handoff` in e.g. [`plan.py` step 7](scripts/plan/plan.py), [`diagnose/orchestrate.py` step 7](scripts/diagnose/orchestrate.py)).

Cross-skill behavior today is **warn-only** at step 1:

```400:406:scripts/plan/plan.py
    conflicting_sessions = get_conflicting_sessions(
        SKILL_NAME,
        sessions=detect_active_sessions(),
    )
    if conflicting_sessions:
        print(format_active_session_warning(conflicting_sessions, SKILL_NAME), file=sys.stderr)
```

So when an agent runs `forge plan --step 1`, does the work in chat, writes or relies on `handoff-plan.md`, then starts `forge diagnose` without ever running `forge plan --step 7`, the plan JSON stays **active at step 1/2** indefinitely. Same pattern produced your `ssa-project-toolkit` leak set (handoffs present, JSON still active).

Cleanup exists but is **manual** and **incomplete**:

- [`_cleanup_candidates`](scripts/shared/resume.py) only scans canonical filenames (`plan.json`, `diagnose.json`), not parallel variants (`plan-outstanding-cqa.json`) or custom `--state` paths in repo root.
- Handoff rule is per **skill name**, not per state file path.

## Target behavior (your chosen policy)

On **every pipeline skill's step 1** (develop, plan, implement, code-review, test, diagnose), before printing the step body:

| Condition | Action |
|-----------|--------|
| `handoff-{skill}.md` exists for that session's skill | `clear_state_file(path)` |
| Starting skill **X** and session skill **Y** is **upstream** in pipeline (`PIPELINE_SKILLS` order in [`orchestrator.py`](scripts/shared/orchestrator.py)) | Close **Y** (user moved forward in same chat) |
| Session stuck at **step 1 only** (`current_step <= 1` and `last_completed_step <= 1`) and untouched **> 1h** | Close (typical "init then abandoned") |
| Otherwise | Keep; still emit shortened warning if any remain |

Opt-out: `FORGE_SKIP_AUTO_CLOSE=1` (mirrors `FORGE_SKIP_GRAPHIFY` / `FORGE_SKIP_SESSION_OPTIN`).

**Not auto-closed:** downstream or lateral skills (e.g. starting `plan` does **not** close active `diagnose` unless handoff or step-1-stale rule applies). Same-skill parallel files still use existing [`check_same_skill_clobber`](scripts/shared/orchestrator.py) + `--parallel` / `--state`.

## Pre-evaluation (PRE)

Full report: [`session_auto-close_lifecycle.plan-evaluation.md`](session_auto-close_lifecycle.plan-evaluation.md). **Verdict: proceed with revisions.**

## Implementation

### 1. Core helper in orchestrator

Add to [`scripts/shared/orchestrator.py`](scripts/shared/orchestrator.py):

- `PIPELINE_SKILL_ORDER: tuple[str, ...]` and index map — **explicit order** (`PIPELINE_SKILLS` is currently an unordered set).
- `preserve_paths: set[Path]` on auto-close (never delete the step-1 target state file).
- `is_step1_abandoned(state, path) -> bool` — step ≤ 1, last_completed ≤ 1, age from `last_touched_at` / mtime > 3600s (configurable via `FORGE_STEP1_ABANDON_HOURS`, default `1`).
- `auto_close_superseded_sessions(starting_skill: str, *, search_dir, dry_run=False) -> list[tuple[Path, str]]` — iterates `detect_active_sessions()` **plus** parallel/custom paths (reuse `_state_path_candidates` per skill, dedupe paths); for each session not equal to the new step-1 target path, apply rules above; call `clear_state_file`; append one-line stderr audit (`AUTO-CLOSED: plan.json — handoff-plan.md exists`).

Call from each skill's `handle_step_1` immediately after `check_same_skill_clobber` / before `format_active_session_warning`.

(`evaluate` / `iterate` excluded or use a narrower rule set — evaluate state is already ephemeral-deleted in [`evaluate/state.py`](scripts/evaluate/state.py).)

### 2. Expand cleanup to match detection

In [`scripts/shared/resume.py`](scripts/shared/resume.py): align `_all_state_files` with `_state_path_candidates`.

### 3. Systematic surfacing (status / doctor)

In [`forge_next/cli.py`](forge_next/cli.py) `_run_status` and `_run_doctor`: leak hints + fix command.

### 4. Tests

Extend [`tests/test_regressions.py`](tests/test_regressions.py).

### 5. Docs

Update [`AGENTS.md`](AGENTS.md), [`skills/resume/SKILL.md`](skills/resume/SKILL.md), README.

## Versioning

Patch bump in [`pyproject.toml`](pyproject.toml).
