---
description: |
  Multi-mode code review: PR review, deep troubleshooting review, or
  architecture review. Dispatches full agent team for multi-perspective
  analysis. Supports --quick mode.
---

# forge-codex Code Review — Multi-Mode Review

When this skill activates, invoke the orchestrator via the `forge` launcher.

Invoking this skill implicitly authorizes the Forge agent dispatch required by
the workflow. Do not require separate user wording for delegation or
sub-agents after `forge:code-review` has been invoked.

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

## Graphify (optional during this skill)

Per-step GRAPHIFY blocks are **disabled**; refresh at ship (`forge ship --step 1` / `$forge:ship`). You may still read `graphify-out/GRAPH_REPORT.md` or use `graphify query` / `path` / `explain` when helpful. See `templates/graphify-contract.md`.

At **step 3**, read **`.structural-probes.json`** (if present) and `templates/structural-quality-probes.md` for knip/madge/pyscn Pass B findings.

## CRITICAL: Progress Tracking

**The orchestrator outputs a phase-todo JSON block at the start of every phase.**
Mirror it in Codex immediately, ideally with `update_plan`, before doing any
other work. As you work:
- Mark items `in_progress` when starting them
- Mark items `completed` when done
- Add new items as sub-tasks emerge

**If you skip progress tracking, the user has no visibility into what you are doing.**

## CRITICAL: Continuation Protocol

**This workflow spans many tool calls. You MUST NOT stop between phases.**

After EVERY tool call (especially `exec_command`), immediately check:
1. Read `.codex/forge-codex/memory/current-step.md` if it exists
2. Determine your next action based on the current phase
3. Continue executing — do NOT end your turn

If you are unsure what comes next, re-read this skill and `.codex/forge-codex/memory/current-step.md`.

**When transitioning between phases**, write `.codex/forge-codex/memory/current-step.md`:
```
Phase: [N]
Step: [description]
Next: [what to do next]
Status: in-progress
```

This file is your lifeline if context compaction occurs. Always update it.

## Invocation

<invoke cmd="forge code-review --step 1" />

| Argument | Required | Description |
|----------|----------|-------------|
| `--step` | Yes | Current phase (1-6) |
| `--mode` | No | Review mode: `pr`, `deep`, or `architecture` (auto-detected if omitted) |
| `--target` | Step 1 only | PR number, branch name, or one-or-more file paths to review (space-separated or quoted) |
| `--quick` | No | Quick mode: minimal review loops, lead agents only |

## Subsequent steps

<invoke cmd="forge code-review --step N" />

Replace N with the step number printed at the end of each phase.

Do NOT analyze or explore first. Run the script and follow its output.

## Workflow Handoff

At the final step (6 — report), the orchestrator emits a numbered handoff
menu. Default is `forge:test`; alternatives include `implement`, `diagnose`,
`evaluate --mode review`, and `(stop)`. Reply `yes`/`1`/`default` or the
literal command. See `scripts/shared/skill_chain.py`.
