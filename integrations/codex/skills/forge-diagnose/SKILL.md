---
name: forge:diagnose
description: Run the Forge diagnose workflow for deep root-cause analysis. When graphify-out/ exists, read GRAPH_REPORT.md before codebase search; Graphify refresh runs at ship, not per workflow step.
---

When `graphify-out/` exists, read `graphify-out/GRAPH_REPORT.md` before grep/glob/search; refresh at ship (`forge ship --step 1` / `$forge:ship`). Workflow `forge … --step` skills do not print per-step GRAPHIFY banners. After code edits run `graphify update .`.

**Playbooks:** `templates/diagnose-execution-playbooks.md` — read the relevant § before each phase.

**Sidecars** (adaptive): `.diagnose-problem-spec.json` (one `framing_entry`), `.diagnose-five-whys.json` (always), optional first-principles / hypotheses / MECE when `activated_techniques` includes them, `.diagnose-technique-coverage.json` (activated rows only), `.diagnose-barriers.json` when high-severity.

**Gates:** Steps 4–5–7 may emit **DIAGNOSE ARTIFACT GATE** — fix sidecars or document override in session state before continuing.

<invoke cmd="forge diagnose --step 1" />
