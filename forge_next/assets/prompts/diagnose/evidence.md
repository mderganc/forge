# Phase 2: Reproduce & Observe

Read `templates/diagnose-feedback-loop.md` first, then `templates/diagnose-execution-playbooks.md` § Gemba, Control charts, Barrier analysis (if safety/compliance).

**Feedback loop status:** {{REPRO_LOOP_SUMMARY}}

## Agents to Dispatch
- **Investigator (lead):** Build and run the feedback loop, then evidence collection
- **QA Reviewer (support):** Provide test evidence — run tests, check coverage
- **Security Reviewer (support):** Check for security-related evidence if relevant

## Beat A — Build the feedback loop

1. Choose `loop_type` per `templates/diagnose-feedback-loop.md` (ordered constructors).
2. Write `.diagnose-feedback-loop.json` beside diagnose state with at least:
   - `version`: 1
   - `loop_type`, `command_or_path`
   - `cannot_build_loop`: false (or true with `blocked_reason` + `user_ask` if genuinely blocked)

## Beat B — Run the loop

1. Execute `command_or_path`; observe the failure.
2. Set `runs_observed` (≥1), `deterministic`, optional `failure_rate`.
3. Set `symptom_captured` (verbatim).
4. Set `matches_user_report`: **true** only when the loop reproduces the user's failure mode.

## Beat C — Minimal repro

1. `minimal_repro_steps[]` — smallest human-readable sequence.
2. `artifacts[]` — paths to logs, HAR, screenshots, test files.

## Beat D — Remaining evidence

### Evidence Checklist
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

If **First-principles thinking** is in `activated_techniques`, update `.diagnose-first-principles.json` — link `violations[]` to observation pointers. Otherwise keep observations in problem spec or investigator memory.

{{AUTONOMY_GATE}}
