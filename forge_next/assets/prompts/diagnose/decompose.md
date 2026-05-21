# Phase 3: Decompose — MECE Cause Tree

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

## Logic Tree
For each promising branch, build testable sub-hypotheses linked to register entries.
Stop decomposing when a branch is directly actionable.

## 5 Whys
For each leading branch, drill down to root cause.

## Mandatory core quartet progress

This phase must materially advance the **MECE issue tree** and **5 Whys** on leading branches. Cross-link nodes to observations from Phase 2 and register IDs.

## First-principles linkage

For each major branch / register entry, note which **invariant** would be violated if that branch were the true root cause.

Write full MECE tree to `.codex/forge-codex/memory/investigator.md`
