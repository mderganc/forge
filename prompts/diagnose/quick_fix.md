# Phase 6: Implement & Validate

## Complexity Gate
{{COMPLEXITY_CHECK}}

Classify `fix_complexity` in session state (`simple`, `complex`, or `large`) using `{{COMPLEXITY_CHECK}}` and evidence from phases 1–5.

### `simple` (local fix)
- <=2 files, no architectural / interface contract change
→ **Proceed** with implementation and validation below.

### `complex` (multi-file but one clear fix shape)
- Broader change, or architectural touch, but **one dominant implementation path**
→ **Skip** implementation in this phase. Hand off to **`plan`** → `implement`.  
→ Record routing rationale in the diagnostic report and `project.md`.

### `large` / systemic (design space still open)
- Cross-subsystem / strategic trade-offs, **multiple viable architectures**, or missing decisions that belong in a design spec  
→ **Skip** implementation in this phase. Hand off to **`develop`** (design / brainstorming) → **`plan`** → `implement`.  
→ Capture known unknowns, constraints, and open questions for the develop session.

Write the handoff file with root causes, complexity tier, and recommended routing.

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
