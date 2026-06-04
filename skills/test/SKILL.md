---
description: |
  Execute tests, analyze coverage, investigate failures, and identify coverage
  gaps. Uses QA Reviewer as lead with Investigator support for failure analysis.
  Supports --mode run and --mode flows for authoring mock flows.
---

# Forge Test — Execution, Coverage & Failure Analysis

When this skill activates, invoke the orchestrator via the `forge` launcher.

Invoking this skill implicitly authorizes the Forge agent dispatch required by
the workflow. Do not require separate user wording for delegation or
sub-agents after `forge:test` has been invoked.

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

## Modes

This skill supports two modes:

### Mode: `run` (default)

Executes a 6-step pipeline: detect context → discover suites → execute → analyze failures → identify coverage gaps → report. Lead: QA Reviewer + Investigator.

```bash
# Default invocation (run mode)
forge:test
```

### Mode: `flows`

Authors end-to-end mock flows via a 7-step pipeline: detect context → recommend flow type → define scope → scaffold → author → execute with iteration → report. The skill detects your project layout, scores four flow types (scenario / BDD / HTTP-replay / workflow-dry-run), and recommends the best fit. Each phase progressively gates quality criteria. Lead: QA Reviewer + Architect (recommendation phase) + Developer (scaffold & authoring).

**Per-mode quick-start:**

```bash
# Flows mode — let the skill recommend the type
forge:test --mode flows

# Flows mode with explicit type override
forge:test --mode flows --flow-type scenario      # pytest scenario script
forge:test --mode flows --flow-type bdd           # pytest-bdd feature + steps
forge:test --mode flows --flow-type http-replay   # vcrpy cassettes
forge:test --mode flows --flow-type workflow-dryrun  # orchestrator harness

# Manual overrides when detection confidence is low
forge:test --mode flows --framework pytest --entry-point http --no-db --roles "admin,member"

# Refresh stale HTTP cassettes
forge:test --mode flows --flow-type http-replay --re-record
```

**Quality criteria:** every flow must satisfy eight criteria, gated progressively at scaffold (2/3/4), authoring (5/6/7), and audit (1/8). See `templates/mock-flow-types.md` for the full catalog and per-type fitness scoring.

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

<invoke cmd="forge test --step 1" />

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--step` | Yes | Current phase (1–6 for run mode, 1–7 for flows mode) |
| `--mode` | No | `run` (default) or `flows` — choose execution vs. authoring pipeline |
| `--target` | No | Test command, path, or pattern; supports one-or-more path tokens (auto-detected from handoff if omitted; run mode only) |
| `--flow-type` | No | Override type recommendation: `scenario`, `bdd`, `http-replay`, `workflow-dryrun` (flows mode only) |
| `--framework` | No | Override framework detection when confidence is low (flows mode) |
| `--entry-point` | No | Override entry-point detection: `ui`, `http`, `cli`, `module` (flows mode) |
| `--no-db` | No | Indicate no test database is available (flows mode) |
| `--roles` | No | Comma-separated role list to override discovery (flows mode) |
| `--re-record` | No | Refresh stale HTTP cassettes; implies `--mode flows --flow-type http-replay` |

After step 1, state is persisted under the Forge runtime (e.g. `.codex/forge/sessions/<id>/session.json` or legacy `.codex/forge/state/test.json`) and
subsequent steps auto-detect it.

## Subsequent steps

<invoke cmd="forge test --step N" />

Replace N with the step number printed at the end of each phase. For flows mode, steps run 1–7; for run mode, steps run 1–6.

Do NOT analyze or explore first. Run the script and follow its output.
