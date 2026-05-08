# Phase 7: Diagnostic Wrap-up & Prevention

## Agents to Dispatch
- **Doc-writer (lead):** Write diagnostic output
- **Investigator (support):** Provide methodology summary
- **Architect (support):** Provide architecture recommendations

## Diagnostic Output
Use: python3 {{SCRIPT_DIR}}/diagnostic_report.py --title "..." --severity ... --output ...

## Chat Summary
1. Root cause: one sentence
2. Fix applied: one sentence (or "handed off to `plan`")
3. Validation: pass/fail summary
4. Output location: file path
5. Recommended follow-ups

## Handoff
Write `.codex/forge-codex/memory/handoff-diagnose.md` with:
- Root causes identified
- Fix applied or recommended
- Validation results
- Suggested next: `plan` (if complex fix needed) or "resolved"

## Dashboard
Render per `templates/dashboard.md`
