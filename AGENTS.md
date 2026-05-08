# Forge Codex Project Instructions

## Skill Handoff Menu

When a skill completes its final step, instead of printing a single hardcoded next-skill recommendation, the footer now displays a numbered menu of available workflow options. Users can reply "yes", "1", "default", or a literal command to select their next action.

**Menu format:**
```
WORKFLOW HANDOFF — <skill> complete
==================================
Default next: forge:<skill> <args>

Reply "yes" or "1" to continue with the default. Or pick a number:
  1. forge:<default-skill> <args>    (default — description)
  2. forge:<alt-1> <args>           (rationale)
  3. ...
  N. (stop)                         (exit the workflow here)

State file: <path>  —  resume any time with `python3 scripts/shared/resume.py`.
```

The canonical skill-chain mapping lives in `scripts/shared/skill_chain.py` as the `SKILL_CHAIN` dict, mapping current skill to `SkillTransition(default, alternatives)`. The renderer `build_skill_handoff_menu(current_skill, state)` in `scripts/shared/orchestrator.py` produces the numbered output. Per-skill context-aware injection is supported — e.g., when `forge:test` detects failures, `diagnose` can be prepended as the top alternative.

The `(stop)` option is always last. The state file persists, and workflows can resume with `python3 scripts/shared/resume.py` at any time.

## Forge Skill Delegation Contract

Invoking a Forge workflow skill is itself permission to dispatch the Forge agent team required by that workflow.

- `forge:develop`, `forge:plan`, `forge:implement`, `forge:code-review`, `forge:test`, and `forge:diagnose` imply automatic delegation to the relevant Forge agents.
- `forge:evaluate` implies automatic delegation when team/review mode is active.
- The user should not have to separately say "use sub-agents", "delegate", or "parallelize" after invoking a Forge skill.
- If the active Codex session policy still blocks `spawn_agent`, surface that as an environment-policy limitation rather than silently falling back to single-agent execution.
- **Agent lifecycle is part of the delegation contract.** Every `spawn_agent` must be paired with a `close_agent` as soon as the agent reports its result or is no longer useful. Never carry an open agent across a wave, step, or phase boundary — Codex caps concurrent agents and leaked sessions block later dispatch. See `templates/codex-runtime.md` → *Parallel work* for the required spawn → wait → capture → close pattern.

## Documentation

When editing this repo's user-facing documentation, keep the role names aligned with the current agent set. Use `doc-writer`, not the legacy `tech-writer`.

## State Lifecycle

The skill orchestrators handle state-file lifecycle so workflows are interruptible and resumable:

- **Step 1 of any skill** refuses to silently overwrite an in-progress same-skill session. To intentionally restart, delete the state file or pass `--force` (where supported, e.g., `plan.py`). To continue, use `python3 scripts/shared/resume.py` or invoke the skill with `--step N --state <path>`.
- **Cross-skill conflicts** still emit a stderr warning but do not block — multiple skills can run in parallel as long as they don't share a state file.
- **`scripts/shared/resume.py --cleanup`** removes state files left behind by completed or abandoned sessions. Defaults to dry-run; pass `--force` to delete. Pass `--all-stale --force` to clear every state file regardless of age (one-time migration after the lifecycle fixes landed).
- **Plan files** are now created by `scripts/plan/plan.py` itself with section-marker placeholders; agents replace markers rather than create the file. The step-6 completion gate refuses to mark the workflow complete while any markers remain.
- **Evaluate findings** persist between phases via per-step sidecar files at `<state-dir>/.evaluate-findings-step<N>.json`. Each phase's prompt instructs the LLM to write findings there; the orchestrator ingests them on the next step.

### Test Skill — Flows Mode State

When `--mode flows` is used in `forge:test`, additional state keys are persisted to `state.custom`:
- `mode` (default `"run"`, set to `"flows"` when `--mode flows` is invoked)
- `flow_type` (default `None`, set by recommendation phase or `--flow-type` override)
- `flow_files` (list of created flow file paths, empty until scaffold phase)
- `flow_scope` (structured dict capturing journey, entry-point, roles, external services, and sample inputs from scope phase)
- `framework` (detected framework, e.g., "pytest"; overridable via `--framework`)
- `entry_point` (detected entry point: "ui" | "http" | "cli" | "module" | "none")
- `roles` (project-discovered role names, defaults to `["anonymous"]` if none found)
- `criteria_audit` (dict tracking qual-criteria pass/fail/partial status, populated at report phase)

All reads use `.get(key, default)` pattern for backward compatibility with legacy state files lacking these keys.

The recommendation sidecar persists at `<state-dir>/.test-recommendation-step2.json` (step-numbered, mirrors evaluate's findings sidecar convention). Schema: `{"chosen": "<type>", "reasoning": "...", "confidence": 0.0-1.0, "alternatives": [...]}`. Ingested at step 3; malformed sidecar aborts with `sys.exit(1)` and stderr message.

The scenario-index update at `<scenarios_dir>/README.md` is parser-gated; on parse failure, report step aborts and leaves file unchanged. Backup written to `.codex/forge-codex/memory/scenario-index.bak` before any rewrite.
