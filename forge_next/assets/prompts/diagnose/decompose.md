# Phase 3: Decompose — MECE Cause Tree

Read `templates/diagnose-execution-playbooks.md` § MECE, Fishbone, Five Whys, Fault Tree (if routed).

## Agents to Dispatch
- **Investigator (lead):** Build MECE cause tree, Software Fishbone, 5 Whys, hypothesis register
- **Architect (support):** Structural decomposition of architecture

## Software Fishbone Categories
CODE | CONFIG | DATA | INFRASTRUCTURE | DEPENDENCIES | ENVIRONMENT

## Hypothesis overproduction (mandatory)

Before narrowing or eliminating candidates, build the **hypothesis register**:

1. Produce **at least {{HYPOTHESIS_MIN}}** distinct, **falsifiable root-cause** hypotheses (not symptoms).
2. Span **at least 4** of the six fishbone categories above.
3. Deduplicate — no near-duplicate or vague statements.
4. Set every entry `status: "open"` (no elimination in this phase).

**Write the register** to `.diagnose-hypotheses.json` in the same directory as the diagnose state file (schema: `id`, `statement`, `category`, `invariant_violated`, `predictions`, `falsification_test`, `status`, `evidence`, `ruled_out_reason`).

**Persist the file before invoking step 4.** Phase 4 will gate on register validity.

## MECE issue tree sidecar (mandatory)

Write `.diagnose-mece-tree.json` with `nodes[]`: `id`, `parent_id`, `label`, `category`, `hypothesis_ids[]`, `mutual_exclusion_note` (required when siblings share category).

Summary: {{MECE_SUMMARY}}

## Logic Tree
For each promising branch, build testable sub-hypotheses linked to register entries.
Stop decomposing when a branch is directly actionable.

## 5 Whys (exploratory draft)

Follow `templates/five-why-protocol.md` § Diagnose RCA.

1. Draft **1–2 chains** on **leading** register branches (not yet confirmed).
2. Minimum **3** linked layers per chain unless stop checklist passes early.
3. Each layer: `because`, `why_question` (must reference parent `because`), `evidence`, `verdict`.
4. Persist `.diagnose-five-whys.json` beside state — update in Phase 4 for **confirmed** IDs only.

Summary: {{FIVE_WHYS_SUMMARY}}

## Mandatory core quartet progress

This phase must materially advance the **MECE issue tree** and **5 Whys** on leading branches. Cross-link nodes to observations from Phase 2 and register IDs.

## First-principles linkage

For each major branch / register entry, note which **invariant** would be violated if that branch were the true root cause.

Update `.diagnose-technique-coverage.json` rows for techniques applied in this phase (`evidence_pointer` required when `applied`).

Write supporting narrative to `.codex/forge-codex/memory/investigator.md` (sidecars are gated artifacts).
