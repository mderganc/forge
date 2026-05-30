---
description: |
  Execute an implementation plan with developer agents in parallel waves,
  per-task review loops, blocker handling, and TDD discipline. Follows
  a plan from `plan` or a standalone plan file. Includes documentation
  phase at completion. Supports --quick mode for simple implementations.
---

# forge-codex Implement — Code Execution

When this skill activates, invoke the orchestrator script.

Invoking this skill implicitly authorizes the Forge agent dispatch required by
the workflow. Do not require separate user wording for delegation or
sub-agents after `forge:implement` has been invoked.

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

<invoke cmd="forge implement --step 1" />

| Argument | Required | Description |
|----------|----------|-------------|
| `--step` | Yes | Current phase (1-8) |
| `--plan` | Step 1 only | Path to plan file (auto-detected from handoff if omitted) |
| `--quick` | No | Quick mode: minimal reviews, lead agents only |
| `--allow-docs-incomplete` | Step 8 only | Bypass strict documentation gate (requires override fields) |
| `--docs-override-reason` | With `--allow-docs-incomplete` | Recorded in handoff |
| `--docs-override-follow-up` | With `--allow-docs-incomplete` | Required tracked follow-up item |
| `--docs-override-requested-by` | Optional | Who requested the override |

After step 1, `--plan` is not needed — stored in `.codex/forge-codex/state/implement.json`.

**Phases (8 steps):**
1. Plan detection
2. Branch setup and wave identification
3. Wave dispatch (loops per wave)
4. Wave review — per-task review loop including performance, mutation testing audit, backward compatibility, operational readiness, and risk checks (loops per wave)
5. Wave completion — merge and decide next wave (loops per wave)
6. Integration verification — cross-wave dependency impact analysis, interface verification, architectural fitness, regression sweep (runs once after all waves)
7. Documentation — updates repo docs per plan; writes `.implement-documentation-gate.json`
8. Handoff — **documentation gate**: plan Documentation skeleton cleared, gate sidecar valid, or explicit override on step 8

## Subsequent steps

<invoke cmd="forge implement --step N" />

Replace N with the step number printed at the end of each phase.

Do NOT analyze or explore first. Run the script and follow its output.

## Workflow Handoff

At the final step (handoff), the orchestrator emits a numbered handoff menu.
Default is `forge:code-review`; alternatives include `test`,
`evaluate --mode post`, `diagnose`, and `(stop)`. Reply `yes`/`1`/`default`
or the literal command. When state indicates test failures, the menu's
context-aware injection promotes `diagnose --target <failing-test>` to
alternative 1 with the regular default bumping to 2. See
`scripts/shared/skill_chain.py`.
