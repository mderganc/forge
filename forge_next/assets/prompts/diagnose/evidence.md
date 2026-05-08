# Phase 2: Observe & Gather Evidence

## Agents to Dispatch
- **Investigator (lead):** Run the evidence collection checklist
- **QA Reviewer (support):** Provide test evidence — run tests, check coverage
- **Security Reviewer (support):** Check for security-related evidence if relevant

## Evidence Checklist
- [ ] Error messages & stack traces
- [ ] Reproduction steps (minimal repro)
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
What should have caught this? (Tests? Monitoring? Code review?)

{{AUTONOMY_GATE}}
