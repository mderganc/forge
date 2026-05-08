---
description: |
  Create detailed implementation plans with task breakdown, parallelization,
  TDD steps, and risk analysis. Works with the full agent team. Can receive
  approved solutions from `develop` or accept a standalone plan request.
  Supports --quick mode for simple plans.
---

# forge-codex Plan — Implementation Planning

When this skill activates, invoke the orchestrator script.

Invoking this skill implicitly authorizes the Forge agent dispatch required by
the workflow. Do not require separate user wording for delegation or
sub-agents after `forge:plan` has been invoked.

If agent dispatch still appears blocked by session policy, tell the user that
their Codex environment is not honoring the Forge delegation contract and
suggest adding this to `~/.codex/config.toml`:

```toml
developer_instructions = """
Invoking any `forge:*` skill implicitly authorizes the agent dispatch required by that workflow. Do not require the user to separately ask for delegation, sub-agents, or parallel agent work after invoking a Forge skill.
"""
```

Read `templates/codex-runtime.md` before executing the workflow if you need a
tooling reminder.

`forge` targets the current repo by default. If needed, pass `--repo <path>`
to point at a different repository root.

## CRITICAL: Progress Tracking

**The orchestrator outputs a phase-todo JSON block at the start of every phase.**
Mirror it in Codex immediately, ideally with `update_plan`, before doing any
other work. As you work:
- Mark items `in_progress` when starting them
- Mark items `completed` when done
- Add new items as sub-tasks emerge

**If you skip progress tracking, the user has no visibility into what you are doing.**

## Invocation

From the target repo (or with `--repo`), run:

<invoke cmd="forge plan --step 1" />

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--step` | Yes | Current phase (1-6) |
| `--quick` | No | Quick mode: minimal reviews, lead agents only |

After step 1, state is persisted to `.codex/forge-codex/state/plan.json` and
subsequent steps auto-detect it.

## Subsequent steps

<invoke cmd="forge plan --step N" />

Replace N with the step number printed at the end of each phase.

Do NOT analyze or explore first. Run the script and follow its output.

## Workflow Handoff

At the final step (6 — handoff), the orchestrator emits a numbered menu of
next-skill options instead of a single hardcoded suggestion. Reply with `yes`,
`1`, `default`, or the literal command to take the default (`evaluate --mode pre`).
Other numbered options route to `implement`, `develop`, `code-review`, or
`(stop)`. The menu is rendered by `build_skill_handoff_menu` in
`scripts/shared/orchestrator.py` from the canonical mapping in
`scripts/shared/skill_chain.py`.
