# Phase 3: Deepen with 5 Whys

{{DIAGNOSE_ARTIFACT_GATE}}

Read `templates/diagnose-execution-playbooks.md` § Five Whys; add MECE / Fishbone sections only if those techniques are in `activated_techniques`.

## Agents to Dispatch
- **Investigator (lead):** 5 Whys chains (primary); optional MECE / hypothesis register
- **Architect (support):** Structural decomposition when MECE is activated

Activated techniques (from problem spec): see `.diagnose-problem-spec.json` — `activated_techniques` / `routing_preferred`.

## 5 Whys (mandatory — primary deepen step)

Follow `templates/five-why-protocol.md` § Diagnose RCA.

1. Draft **1–2 chains** from the framed problem statement (leading theories).
2. Minimum **3** linked layers per chain unless stop checklist passes early.
3. Each layer: `because`, `why_question` (must reference parent `because`), `evidence`, `verdict`.
4. Persist `.diagnose-five-whys.json` beside state — finalize in Phase 4 (`root_cause`, `but_for`, `stop_reason`).

Summary: {{FIVE_WHYS_SUMMARY}}

If **Hypothesis-driven problem solving** is activated, set `hypothesis_id` on chains when linking to register entries.

## Hypothesis register (only when activated)

Skip this section unless **Hypothesis-driven problem solving** or **Fishbone / Ishikawa** is in `activated_techniques`.

1. Produce **at least {{HYPOTHESIS_MIN}}** distinct, **falsifiable root-cause** hypotheses.
2. Span **at least 4** fishbone categories: CODE \| CONFIG \| DATA \| INFRASTRUCTURE \| DEPENDENCIES \| ENVIRONMENT.
3. Set every entry `status: "open"` (no elimination in this phase).
4. Write `.diagnose-hypotheses.json` before step 4.

## MECE issue tree (only when activated)

Skip unless **MECE issue tree** is in `activated_techniques`.

Write `.diagnose-mece-tree.json` with `nodes[]`: `id`, `parent_id`, `label`, `category`, `hypothesis_ids[]`, `mutual_exclusion_note` when siblings overlap.

Summary: {{MECE_SUMMARY}}

## First-principles (only when activated)

If **First-principles thinking** is activated, link major 5 Whys branches to violated invariants in `.diagnose-first-principles.json`.

## Technique coverage

Update `.diagnose-technique-coverage.json` — one row per activated technique; `applied` requires `evidence_pointer`.

Write supporting narrative to `{{MEMORY_DIR}}/investigator.md`.
