# Full Team Review — Dispatch

Dispatch the full review team to analyze the current implementation.

## Team Assignments

All reviewers operate against the current feature branch in parallel:

| Agent | Focus |
|-------|-------|
| **Architect** | Architecture conformance — does code match plan? Component boundaries? Drift? |
| **QA Reviewer** | Full test suite + coverage. Edge cases. Integration. Requirements verification. |
| **Security Reviewer** | OWASP audit. Input validation. Auth/authz. Dependencies. Secrets. |
| **Critic** | Most likely production failure? What wasn't tested? What assumption was wrong? |
| **Investigator** | Deep-dive on any areas flagged by other reviewers. |

## Structural probes (Pass B)

If the step output includes a **STRUCTURAL PROBES** banner, complete the plan → `forge structural-probes run` → read `.structural-probes.json` (`templates/structural-quality-probes.md`) before dispatch. Pass probe context to each reviewer.

## Eight parallel structural subagents (first)

When the step includes **STRUCTURAL QUALITY — eight parallel subagents**:

1. Complete structural probes (inventory → plan → `forge structural-probes run`).
2. Spawn **S1–S8** in parallel using the Civil Learning master prompt and per-agent
   missions in `templates/structural-quality-eight-agents.md`.
3. Write `.structural-eight-agents.json`; **close each subagent** before the core team.

## Instructions

1. Dispatch all core reviewers in parallel (consume the eight-agent sidecar — do not redo the same lenses)
2. Each reviewer writes findings to their memory file
3. Use finding format from `templates/review-loop.md`
4. Each finding needs: ID, severity (PASS/WARN/FAIL), location, description, impact, fix
5. **Close each reviewer with `close_agent` as soon as it has written its memory
   file.** Do not leave reviewers open while the next phase (findings
   aggregation) runs — Codex caps concurrent agents and leaked sessions block
   later dispatch. See `templates/codex-runtime.md` → *Parallel work* for the
   required spawn → wait → capture → close pattern.

## Quick Mode
{{QUICK_MODE_NOTE}}
