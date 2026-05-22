# Phase 4: Analyze & Rank Causes

{{HYPOTHESIS_GATE}}
{{QUARTET_GATE}}

Read `templates/diagnose-execution-playbooks.md` § Hypothesis-driven, FMEA, Pareto, Bayesian, but-for.

## Register status
{{HYPOTHESIS_REGISTER_SUMMARY}}

## Quartet sidecars
- First-principles: {{FIRST_PRINCIPLES_SUMMARY}}
- MECE tree: {{MECE_SUMMARY}}
- Five Whys (finalize on confirmed): {{FIVE_WHYS_SUMMARY}}

(Minimum **{{HYPOTHESIS_MIN}}** hypotheses required at register creation.)

## Agents to Dispatch
- **Investigator (lead):** Full-register elimination, FMEA, Bayesian reasoning
- **Critic:** Challenge rankings, look for bias

## Full-register elimination (mandatory)

Work through **every** non-`deferred` hypothesis in the register, in **discriminating-test order** (highest signal / fastest falsification first — not list order).

For **each** hypothesis:
1. State hypothesis → predict observable evidence → run falsification test → conclude
2. Update register `status`: `ruled_out` (with non-empty `ruled_out_reason`), `plausible`, or `confirmed`
3. Record `evidence` with source pointers

`deferred` is allowed only when the user explicitly time-boxes further testing (document in investigator memory).

**Persist `.diagnose-hypotheses.json` before advancing to step 5.**

## Finalize 5 Whys (confirmed only)

Extend `.diagnose-five-whys.json` chains linked to **`confirmed`** hypothesis IDs until `templates/five-why-protocol.md` stop checklist passes (`root_cause`, `but_for`, `stop_reason`).

## FMEA Scoring
Use: `python3 {{SCRIPT_DIR}}/fmea_score.py` on the **full** candidate list (all register entries). Record output path in technique coverage matrix for **FMEA**.

| Cause | Severity (S) | Occurrence (O) | Detection (D) | RPN |
|-------|-------------|----------------|---------------|-----|

## Counterfactual Validation
For **each** hypothesis still `plausible` after falsification, apply the **but-for test**:
- "If this cause had been absent, would the failure still have occurred?"
- If YES → contributor, not root cause — look deeper or rule out.
- If NO → valid root cause candidate; prefer `confirmed` when evidence is decisive.

## Data-Driven Correlation
Use `templates/data-analysis.md` techniques:
- Cross-reference metric changes at symptom onset (error rate, latency, resource usage)
- Run git hotspot analysis on affected files: `python3 {{SCRIPT_DIR}}/git_hotspots.py --path <affected-dir>`
- Log pattern analysis if logs are available: `python3 {{SCRIPT_DIR}}/log_analyzer.py --file <logfile>`

## Pareto
Ranked list with **counts or metrics** — cite in coverage row for **Pareto Analysis**.

## Hypothesis ranking tied to principles

For each surviving hypothesis, state:
- Which **first-principles invariant** it violates if true.
- Predictions vs observed evidence (hypothesis-driven loop).

## Technique Coverage Matrix (update)

Update `.diagnose-technique-coverage.json` — all 20 rows; **applied** requires `evidence_pointer`.

Summary: {{TECHNIQUE_COVERAGE_SUMMARY}}

See `prompts/diagnose/technique_catalog.md` for the full list of 20 + routing rules.

{{AUTONOMY_GATE}}
