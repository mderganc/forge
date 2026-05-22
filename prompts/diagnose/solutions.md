# Phase 5: Solution Generation

{{DIAGNOSE_ARTIFACT_GATE}}

## Agents to Dispatch
- **Architect (lead):** Generate solutions for each confirmed root cause
- **Investigator (support):** Provide evidence for solution feasibility
- **Critic:** Challenge solution adequacy

## Pre-Mortem for Fixes
Before selecting a fix, run a pre-mortem per `templates/pre-mortem.md`:
- Imagine each proposed fix was deployed and **failed**. What went wrong?
- Focus on: unintended side effects, data migration risks, rollback viability, edge cases the fix doesn't cover.
- Add any new failure modes to findings.

## Confirmed root causes only

Generate solution options **only** for hypotheses with register `status: confirmed`. Do not design fixes for `plausible`, `open`, or `ruled_out` entries unless the user explicitly expands scope.

Register summary: {{HYPOTHESIS_REGISTER_SUMMARY}}

Five Whys: {{FIVE_WHYS_SUMMARY}} — cite `chain-id` and `hypothesis_id` per fix.

## Solution Types
For each **confirmed** root cause, generate at least 3:
1. Quick fix — minimum viable, lowest effort
2. Proper fix — addresses root cause correctly
3. Systemic fix — addresses root cause AND prevents recurrence

## Decision Matrix
Use: python3 {{SCRIPT_DIR}}/decision_matrix.py
Weights: Effectiveness=3x, Effort=2x(inv), Risk=2x(inv), Reversibility=1x, Maintainability=1x
