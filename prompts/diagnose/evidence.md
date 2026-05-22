# Phase 2: Observe & Gather Evidence

Read `templates/diagnose-execution-playbooks.md` § Gemba, Control charts, Barrier analysis (if safety/compliance).

## Agents to Dispatch
- **Investigator (lead):** Run the evidence collection checklist
- **QA Reviewer (support):** Provide test evidence — run tests, check coverage
- **Security Reviewer (support):** Check for security-related evidence if relevant

## Evidence Checklist
- [ ] Error messages & stack traces
- [ ] Reproduction steps (minimal repro) — **Gemba:** link artifact paths
- [ ] Timeline (correlate with deploys, config changes)
- [ ] Metrics (CPU, memory, latency, error rates) — establish baseline vs. degraded per `templates/data-analysis.md` §4
- [ ] Source code (relevant paths end-to-end)
- [ ] Dependencies (versions, changelogs, known issues) — run audit per `templates/data-analysis.md` §5
- [ ] Configuration (env vars, feature flags, DB state)
- [ ] Tests (existing failures? missing coverage?)
- [ ] Git history (recent commits on relevant files) — run `python3 {{SCRIPT_DIR}}/git_hotspots.py --path <dir>` for churn analysis
- [ ] Log analysis — run `python3 {{SCRIPT_DIR}}/log_analyzer.py --file <logfile>` for error pattern extraction and spike detection

## Causal Factor Timeline
[T-N] Last good → [T-0] Issue reported → [T+1] Current

## Barrier Analysis

If incident profile includes safety/compliance/high-severity, draft `.diagnose-barriers.json` (finalize in Phase 7). Per layer: `exists`, `active`, `detected`, `failure_mode`.

Otherwise note which defenses should have caught this (tests, monitoring, code review) in investigator memory.

## Observations vs assumptions

Maintain two lists:

- **Observations:** timestamps, logs, metrics, repro artifacts — each with source pointer.
- **Assumptions:** each tied to a falsification test or missing-data flag.

Update `.diagnose-first-principles.json` — link `violations[]` to observation pointers.

{{AUTONOMY_GATE}}
