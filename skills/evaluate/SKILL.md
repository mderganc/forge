---
description: |
  Reads a plan document, analyzes the codebase, and provides detailed critique
  and suggestions. Auto-detects pre-implementation (plan review) vs
  post-implementation (audit) mode. Supports path or keyword plan lookup.
  Use when reviewing plans before implementation or auditing completed work
  against the original plan. Also supports full-team code review mode.
---

# Evaluate: Plan Analysis & Critique

When this skill activates, invoke the orchestrator via the `forge` launcher.

Invoking this skill implicitly authorizes the Forge agent dispatch required by
the workflow when team or review mode is active. Do not require separate user
wording for delegation or sub-agents after `forge:evaluate` has been invoked.

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

In **post** step 4 and **review** step 1, read **`.structural-probes.json`** and `templates/structural-quality-probes.md` when a structural-probes banner is shown.

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

<invoke cmd="forge evaluate --step 1 --plan '<plan path or keywords>'" />

| Argument | Required | Description |
|----------|----------|-------------|
| `--step` | Yes | Current phase (1-7 for pre, 1-8 for post, 1-5 for review) |
| `--plan` | Step 1 only (pre/post) | File path or keywords to find the plan |
| `--mode` | No | Force mode: pre, post, or review (auto-detected if omitted) |
| `--team` | No | Enable team dispatch in pre/post modes (optional) |

### Review Mode

When `--mode review` is specified, evaluate performs a full-team review of the current implementation:

<invoke cmd="forge evaluate --step 1 --mode review" />

Review mode does not require a plan — it reviews the current feature branch.

**Team (review mode):** QA Reviewer (lead), Security Reviewer, Architect, Critic, Investigator, Doc-writer

**Phases:**
1. Team dispatch — all reviewers analyze in parallel
2. Findings aggregation — collect and deduplicate findings
3. Remediation loop — fix/re-review until clean
4. Discussion — interactive review with user
5. Report — evaluation report

After step 1, `--plan` and `--mode` are not needed — stored in state.

**Pre-implementation phases (7 steps):**
1. Plan parsing and mode detection
2. Feasibility analysis (includes performance feasibility and resource constraints)
3. Completeness analysis (includes operational requirements and deployment steps)
4. Codebase alignment
5. Risk & dependency analysis (dependency graph, risk scoring, rollback audit, pre-mortem)
6. Discussion — interactive review with user
7. Report

**Post-implementation phases (8 steps):**
1. Plan parsing
2. Completeness audit (planned vs implemented)
3. Correctness review (includes concurrency and resource lifecycle checks)
4. Code quality review (includes performance anti-patterns)
5. Performance review (algorithmic complexity, N+1 queries, hot paths, memory, I/O)
6. Operational readiness (error handling, logging, resource management, deployment, degradation)
7. Discussion — interactive review with user
8. Report

## Subsequent steps

<invoke cmd="forge evaluate --step N" />

Replace N with the step number printed at the end of each phase.

Do NOT analyze or explore first. Run the script and follow its output.

## Workflow Handoff

At the final step (7 for `pre`, 8 for `post`, 5 for `review`), the orchestrator
emits a numbered handoff menu. Default is `forge:implement`; alternatives
include `plan`, `evaluate --mode review`, `test`, and `(stop)`. Reply
`yes`/`1`/`default` or the literal command. See `scripts/shared/skill_chain.py`.

When resuming an evaluate session without `--mode`, the orchestrator now reads
the saved mode from state (so a post-mode session resumed without `--mode`
correctly uses `max_step=8`, not the pre default).
