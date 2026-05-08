# Phase 6: Implement & Validate

## Complexity Gate
{{COMPLEXITY_CHECK}}

If fix requires >2 files or architectural changes:
→ Skip this phase
→ Hand off to `plan` then `implement`
→ Write handoff with root causes and recommended solution

If fix is simple (<=2 files):
→ Proceed with implementation below

## Agents to Dispatch
- **Backend/Frontend Dev:** Apply the approved fix
- **QA Reviewer:** Run validation ladder per `templates/verification-protocol.md`
- **Investigator:** Verify fix addresses the root cause (not just symptom)

## Validation Ladder
1. Unit tests (always)
2. Regression (full suite)
3. Reproduction case (no longer triggers)
4. Static analysis (if available)

{{AUTONOMY_GATE}}
