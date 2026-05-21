# Phase 7: Diagnostic Wrap-up & Prevention

## Agents to Dispatch
- **Doc-writer (lead):** Write diagnostic output
- **Investigator (support):** Provide methodology summary
- **Architect (support):** Provide architecture recommendations

## Mandatory core quartet (completion checklist)

Confirm explicit artifacts exist for:

1. **First-principles thinking** — invariants, violated principles, causal chain from fundamentals.
2. **Hypothesis-driven problem solving** — ranked hypotheses with predictions vs results.
3. **5 Whys** — documented chain(s) on primary causal branch(es).
4. **MECE issue tree** — tree or structured outline covering the failure space without overlap/gaps.

If any item is thin, document why with severity-scaled rationale (small incidents may compress — still acknowledge).

## Technique Coverage Matrix (final)

Complete the matrix for **all 20 techniques** in `prompts/diagnose/technique_catalog.md`:

| technique | applied / skipped / deferred | evidence or rationale |
|-----------|------------------------------|------------------------|

- **applied:** link or pointer to where the technique appears (memory file, log excerpt, chart).
- **skipped:** why cost/signal trade-off justified (respect scalability rules).
- **deferred:** what would trigger applying it later.

Trace **final root-cause claims** back to violated invariants / hypothesis ranking.

## Hypothesis Register (final)

Include a table of **all** register entries:

| ID | Statement | Category | Status | Key evidence / ruled-out reason |
|----|-----------|----------|--------|--------------------------------|

Source: `.diagnose-hypotheses.json` — {{HYPOTHESIS_REGISTER_SUMMARY}}

## Preferred routing audit

State which incident-profile buckets matched (`technique_catalog.md` routing map) and whether you followed use-case-first ordering before broader methods.

## Diagnostic Output
Use: python3 {{SCRIPT_DIR}}/diagnostic_report.py --title "..." --severity ... --output ...

## Chat Summary
1. Root cause: one sentence
2. Fix applied: one sentence (or "handed off to `plan` / `develop`")
3. Validation: pass/fail summary
4. Output location: file path
5. Recommended follow-ups

## Handoff
Write `.codex/forge-codex/memory/handoff-diagnose.md` with:
- Root causes identified
- Fix applied or recommended
- **`fix_complexity` tier:** `simple` | `complex` | `large` (must match orchestrator state)
- Routing rationale (why not simpler / why design work needed)
- Validation results
- Technique coverage summary (matrix pointers)
- Suggested next:
  - **`develop`** when `fix_complexity` is **`large`** (systemic / multi-strategy) — then `plan`
  - **`plan`** when **`complex`** (clear implementation path but too big for this phase)
  - **resolved** or **menu choice** when **`simple`**

The orchestrator emits a numbered **WORKFLOW HANDOFF** menu on phase 7; defaults are **context-aware** (`develop` first for `large`, `plan` for `complex`).

## Dashboard
Render per `templates/dashboard.md`
