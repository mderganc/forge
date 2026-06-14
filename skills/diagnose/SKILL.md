---
description: |
  Structured 7-phase RCA for bugs, performance, and systemic failures.
  Investigator lead. Playbooks + gated sidecars. --quick for simple issues.
---

# Forge Diagnose — Root Cause Analysis

Routing: [AGENTS.md](../../AGENTS.md) § Process-first.

Shared runtime: [templates/workflow-skill-preamble.md](../../templates/workflow-skill-preamble.md).

Read `templates/diagnose-execution-playbooks.md` and `prompts/diagnose/_index.md` per phase. Gates and sidecars: [AGENTS.md](../../AGENTS.md) § Diagnose.

<invoke cmd="forge diagnose --step 1" />

| Argument | Required | Description |
|----------|----------|-------------|
| `--step` | Yes | Phase 1–7 |
| `--mode` | No | `guided`, `autonomous`, `interactive` |
| `--quick` | No | Investigator-only |

## Adaptive spine

- **Phase 1:** One framing path → `.diagnose-problem-spec.json` with `activated_techniques`.
- **Phase 3–4:** **5 Whys** always (`.diagnose-five-whys.json`).
- **Optional:** MECE, hypothesis register, first-principles only when listed in `activated_techniques`.

## Gates (orchestrator)

| Step | Gate | Validates |
|------|------|-----------|
| 2 | Problem spec | `framing_entry` + `problem_statement` |
| 3 | Feedback loop | `.diagnose-feedback-loop.json` |
| 4 | Register / quartet | Hypothesis register + MECE / first-principles when activated |
| 5 | Bundle | Elimination + 5 Whys + **activated** technique coverage (`routed_only=True`) |
| 7 | Closure | **Activated** technique coverage only + 5 Whys + optional sidecars + barriers when high-severity |

Step 7 no longer requires all 20 catalog rows — only **activated** techniques (`adaptive=True`, gate title: "activated techniques"). CRT, A3, 8D, and DoE are deprioritized (default skip) per `prompts/diagnose/technique_catalog.md`.

Override keys when gates block: `repro_loop_override_reason`, `hypothesis_override_reason`, `five_whys_override_reason`, `technique_coverage_override_reason`, `quartet_override_reason`, `barriers_override_reason`.

Handoff defaults by `fix_complexity`: **large** → design; **complex** → plan; **simple** → user choice.
