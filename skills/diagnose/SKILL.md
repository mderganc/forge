---
description: |
  Deep diagnostic problem-solving for bugs, performance issues, and systemic
  failures. Uses the full agent team with Investigator as lead. Combines 20+
  RCA methodologies in a structured 7-phase pipeline. Supports autonomy modes
  (guided/autonomous/interactive) and --quick mode for simple issues.
---

# forge-codex Diagnose — Deep Issue Diagnosis & Resolution

When this skill activates, invoke the orchestrator via the `forge` launcher.

Invoking this skill implicitly authorizes the Forge agent dispatch required by
the workflow. Do not require separate user wording for delegation or
sub-agents after `forge:diagnose` has been invoked.

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

<invoke cmd="forge diagnose --step 1" />

| Argument | Required | Description |
|----------|----------|-------------|
| `--step` | Yes | Current phase (1-7) |
| `--mode` | No | Autonomy mode: guided (default), autonomous, interactive |
| `--quick` | No | Quick mode: Investigator-only, minimal team dispatch |

## Subsequent steps

<invoke cmd="forge diagnose --step N" />

Do NOT analyze or explore first. Run the script and follow its output.

## Methodology Reference

Every run completes the **mandatory core quartet**: first-principles thinking,
hypothesis-driven problem solving, **5 Whys**, and a **MECE issue tree**, then
records a **Technique Coverage Matrix** for all **20** methods in
`prompts/diagnose/technique_catalog.md` (applied / skipped / deferred with
evidence). **Use-case-first routing** picks preferred techniques from the
catalog’s incident-profile map before expanding breadth; severity and compliance
rules can override preferences.

The Investigator agent carries supporting methodology detail — see
`agents/investigator.md` and `prompts/diagnose/technique_catalog.md`.

## Bundled Scripts

- `scripts/diagnose/fmea_score.py` — FMEA Risk Priority Number calculator
- `scripts/diagnose/decision_matrix.py` — Weighted decision matrix
- `scripts/diagnose/diagnostic_report.py` — Report template generator
- `scripts/diagnose/log_analyzer.py` — Structured log analysis (error patterns, frequency, spike detection)
- `scripts/diagnose/git_hotspots.py` — Git history analytics (churn hotspots, temporal coupling, blame)

## Workflow Handoff

`diagnose` is terminal in the canonical chain — its handoff menu has no
default ("workflow terminates here"). Numbered alternatives are `forge:plan`
(act on findings), `forge:implement`, `forge:develop`, and `(stop)`. Reply
with a number or literal command. See `scripts/shared/skill_chain.py`.
