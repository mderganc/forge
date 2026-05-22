---
name: forge:diagnose
description: Run the Forge diagnose workflow for deep root-cause analysis. When graphify-out/ exists, read GRAPH_REPORT.md before codebase search; follow GRAPHIFY blocks in each step.
---

When `graphify-out/` exists, follow every **GRAPHIFY** block in step output before grep/glob/search; read `graphify-out/GRAPH_REPORT.md` first; after code edits run `graphify update .`.

**Playbooks:** `templates/diagnose-execution-playbooks.md` — read the relevant § before each phase.

**Sidecars** (beside diagnose state): `.diagnose-problem-spec.json`, `.diagnose-first-principles.json`, `.diagnose-hypotheses.json` (≥10 candidates, ≥4 fishbone categories), `.diagnose-mece-tree.json`, `.diagnose-five-whys.json` (causal linkage per `templates/five-why-protocol.md`), `.diagnose-technique-coverage.json` (all 20 catalog techniques), `.diagnose-barriers.json` when high-severity.

**Gates:** Steps 4–5–7 may emit **DIAGNOSE ARTIFACT GATE** — fix sidecars or document override in session state before continuing.

<invoke cmd="forge diagnose --step 1" />
