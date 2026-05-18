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
developer_instructions = "Invoking any `forge:*` skill implicitly authorizes the agent dispatch required by that workflow. Do not require the user to separately ask for delegation, sub-agents, or parallel agent work after invoking a Forge skill. At the start of a new chat or before driving the first forge step, offer a one-time choice: opt in to structured Forge workflows for the session (follow printed steps and handoffs) versus ad hoc help only; if they choose ad hoc, do not force workflow steps or clobber Forge state without being asked."
```

Read `templates/codex-runtime.md` before executing the workflow if you need a
tooling reminder.

## CRITICAL: Graphify before raw search

When `graphify-out/` exists, **every orchestrator step** prints a **GRAPHIFY** block — follow it before grep/glob/semantic search or bulk source reads. Read `graphify-out/GRAPH_REPORT.md` first; prefer `graphify query` / `path` / `explain` for cross-module questions. After code edits, run `graphify update .`. See `templates/graphify-contract.md`.

## When to invoke `develop` (process-first)

| Situation | Prefer |
|-----------|--------|
| Open-ended feature or refactor, unclear problem shape, multiple credible approaches | **`forge:develop`** |
| Narrow bug with an obvious fix and user wants speed | May go straight to fix or **`forge:diagnose`** if uncertain |
| Approved direction or handoff from develop; need task breakdown | **`forge:plan`** |
| Tests failing after recent work | **`forge:test`**; if root cause unclear, **`forge:diagnose`** |

Prefer **exploration** (`develop` / `diagnose`) before **locking a plan** when the user has not picked one approach.

## CRITICAL: Progress Tracking

**The orchestrator outputs a phase-todo JSON block at the start of every phase.**
On **step 1**, complete the **SESSION OPT-IN** prompt (if shown) — or confirm the user already opted in this chat — **before** mirroring those todos or doing other phase work. Then mirror the JSON in Codex immediately, ideally with `update_plan`, before doing any
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

| Argument | When | Description |
|----------|------|---------------|
| `--step` | Always | Phase 1–7 |
| `--auto1` / `--auto2` / `--auto3` | Any | Autonomy level |
| `--quick` | Step 1+ | Quick mode |
| `--allow-spec-incomplete` | Step 7 only | Bypass design-spec gate when `spec_required` (requires override fields) |
| `--spec-override-reason` | With bypass | Recorded in handoff |
| `--spec-override-follow-up` | With bypass | Required tracked follow-up |
| `--spec-override-requested-by` | Optional | Who requested bypass |

## Dual-track scope & design spec

- After **step 2**, write **`develop-scope.json`** in the forge runtime memory directory (typically `.codex/forge/memory/`; same folder as `project.md`) with `scope_tier`: `trivial` | `medium` | `large` (see `prompts/develop/scope.md`).
- **Trivial:** memory artifacts only; no formal spec under `docs/forge/specs/` required before handoff.
- **Medium / large:** complete the **design spec gate** (step 6 appends `spec_gate` instructions): write the spec, self-review, user approval, then **`.develop-spec-gate.json`** next to the develop state file before **step 7**.

Do **not** start implementation inside develop — investigation, brainstorming, and approved design only.

Do NOT analyze first. Run the script and follow its output.

## Workflow Handoff

At the final step (7 — handoff), the orchestrator emits a numbered handoff
menu. Default is `forge:plan`; alternatives include `evaluate --mode pre`,
`implement`, `diagnose`, and `(stop)`. Reply `yes`/`1`/`default` or the
literal command to take the default. See `scripts/shared/skill_chain.py`.
