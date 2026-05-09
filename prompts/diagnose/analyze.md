# Phase 4: Analyze & Rank Causes

## Agents to Dispatch
- **Investigator (lead):** FMEA scoring, Bayesian reasoning, hypothesis testing
- **Critic:** Challenge rankings, look for bias

## FMEA Scoring
Use: python3 {{SCRIPT_DIR}}/fmea_score.py
| Cause | Severity (S) | Occurrence (O) | Detection (D) | RPN |
|-------|-------------|----------------|---------------|-----|

## Hypothesis Testing
For top-3 causes by RPN: state hypothesis → predict → test → conclude

## Counterfactual Validation
For each top-5 cause by RPN, apply the **but-for test**:
- "If this cause had been absent, would the failure still have occurred?"
- If YES → the cause is a contributor but not the root cause. Look deeper.
- If NO → the cause passes the counterfactual test. It is a valid root cause candidate.
- Demote causes that fail the counterfactual to "contributing factors."

## Data-Driven Correlation
Use `templates/data-analysis.md` techniques:
- Cross-reference metric changes at symptom onset (error rate, latency, resource usage)
- Run git hotspot analysis on affected files: `python3 {{SCRIPT_DIR}}/git_hotspots.py --path <affected-dir>`
- Log pattern analysis if logs are available: `python3 {{SCRIPT_DIR}}/log_analyzer.py --file <logfile>`

## Pareto
Which 20% of causes explain 80% of symptoms?

## Hypothesis ranking tied to principles

For each top hypothesis, state:
- Which **first-principles invariant** it violates if true.
- Predictions for evidence (hypothesis-driven loop).

## Technique Coverage Matrix (update)

Extend the matrix from Phase 1 — mark techniques **applied** here with evidence links; **skipped** with cost/benefit; **deferred** with trigger for when to revisit.

See `prompts/diagnose/technique_catalog.md` for the full list of 20 + routing rules.

{{AUTONOMY_GATE}}
