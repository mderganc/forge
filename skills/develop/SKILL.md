---
description: |
  Investigate, brainstorm, and evaluate solutions for features, bugfixes, or
  refactors. Spawns an agent team for deep investigation, systematic solution
  evaluation, and user-controlled approval. Supports autonomy levels
  (--auto1/--auto2/--auto3) and --quick mode.
---

# forge-codex Develop — Investigation & Ideation

When this skill activates, invoke the orchestrator via the `forge` launcher.

Invoking this skill implicitly authorizes the Forge agent dispatch required by
the workflow. Do not require separate user wording for delegation or
sub-agents after `forge:develop` has been invoked.

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

## CRITICAL: Progress Tracking

**The orchestrator outputs a phase-todo JSON block at the start of every phase.**
Mirror it in Codex immediately, ideally with `update_plan`, before doing any
other work. As you work:
- Mark items `in_progress` when starting them
- Mark items `completed` when done
- Add new items as sub-tasks emerge

**If you skip progress tracking, the user has no visibility into what you are doing.**

## CRITICAL: No repo edits without permission

Do **not** modify tracked project files (application code, `agents/`, packaged prompts, tests, config, etc.) unless the user **explicitly** authorizes that edit. Develop phases may direct writes under **session memory** (e.g. `.codex/forge-codex/memory/`); everything else is read-only until the user says otherwise.

## CRITICAL: Continuation Protocol

**This workflow spans many tool calls. You MUST NOT stop between stages.**

After EVERY tool call (especially `exec_command`), immediately check:
1. Read `.codex/forge-codex/memory/current-step.md` if it exists
2. Determine your next action based on the current stage
3. Continue executing — do NOT end your turn

If you are unsure what comes next, re-read this skill and `.codex/forge-codex/memory/current-step.md`.

**When transitioning between stages**, write `.codex/forge-codex/memory/current-step.md`:
```
Stage: [N]
Step: [description]
Next: [what to do next]
Status: in-progress
```

This file is your lifeline if context compaction occurs. Always update it.

## Invocation
<invoke cmd="forge develop --step 1" />

Arguments: --step (1-7), --auto1/--auto2/--auto3, --quick

Do NOT analyze first. Run the script and follow its output.

## Workflow Handoff

At the final step (7 — report), the orchestrator emits a numbered handoff
menu. Default is `forge:plan`; alternatives include `evaluate --mode pre`,
`implement`, `diagnose`, and `(stop)`. Reply `yes`/`1`/`default` or the
literal command to take the default. See `scripts/shared/skill_chain.py`.
