# Phase 6: Report + handoff

Produce a prioritized UX report with screenshots and concrete evidence. For each finding, include its location, severity, user impact, reproduction steps, and an actionable recommendation. Conclude with an overall assessment, recurring themes, quick wins, higher-effort improvements, and a record of pages, controls, workflows, and states reviewed.

## Injected context

- **Report path:** {{REPORT_PATH}}
- **Findings ({{FINDINGS_COUNT}}):**
```
{{FINDINGS_JSON}}
```
- **Coverage:**
```
{{COVERAGE_JSON}}
```

{{FINDINGS_GATE_FAILURES}}

## Your task

1. Write the report using `templates/ux-review-report.md` to `{{REPORT_PATH}}` (or a path the user names). Prefer `memory/ux-review-report.md` under the Forge runtime when unspecified.
2. Prioritize findings (blocker → nit). Include evidence references.
3. Closing sections required:
   - Overall assessment
   - Recurring themes
   - Quick wins
   - Higher-effort improvements
   - Coverage record (pages, controls, workflows, states, viewports, skips)
4. Set `state.custom["report_path"]` to the written file.
5. Do not modify product code unless asked.

## Done when

- [ ] Report file written
- [ ] Findings complete and prioritized
- [ ] Coverage record included
- [ ] Ready for handoff menu

Suggested next: **diagnose** if blocker/high findings remain; otherwise **ship**.
