---
description: |
  Real-browser UX review of a web app: map purpose/users/IA/journeys, plan
  coverage, walk every page and control, capture states/screenshots, produce a
  prioritized findings report. Use this — not forge test — for live UI audits.
---

# forge ux-review — Product UX audit

Walk the live UI like a real user and produce an evidence-backed UX report.

**No agent team required** for the walkthrough itself (1:1 browser work). Spawn helpers only if the user asks.

Shared runtime: [templates/workflow-skill-preamble.md](../../templates/workflow-skill-preamble.md).

Criteria: [templates/ux-review-criteria.md](../../templates/ux-review-criteria.md).  
Checklist: [templates/ux-review-coverage-checklist.md](../../templates/ux-review-coverage-checklist.md).  
Report: [templates/ux-review-report.md](../../templates/ux-review-report.md).

vs **`forge test`:** suite execution (`--mode run`) and mock-flow authoring (`--mode flows`). **`ux-review`** is the real-browser product UX audit (IA, discoverability, consistency, every reachable control/state).

<invoke cmd="forge ux-review" />

| Argument | When | Description |
|----------|------|-------------|
| `--step` | Always | 1–6 |
| `--base-url` | Step 1+ | App URL to review |
| `--state` | Resume | Path to session state |
| `--quick` | Optional | Narrow scope — critical journeys only |

Default next: **`forge:ship`** (or **`forge:diagnose`** when high-severity findings remain).
