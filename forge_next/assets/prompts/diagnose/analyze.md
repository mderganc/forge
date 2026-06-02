# Phase 4: Analyze & Rank Causes

{{HYPOTHESIS_GATE}}
{{QUARTET_GATE}}

Read `templates/diagnose-execution-playbooks.md` for techniques in `activated_techniques` only.

## Register status
{{HYPOTHESIS_REGISTER_SUMMARY}}

## Sidecars (when activated)
- First-principles: {{FIRST_PRINCIPLES_SUMMARY}}
- MECE tree: {{MECE_SUMMARY}}
- Five Whys (finalize): {{FIVE_WHYS_SUMMARY}}

## Agents to Dispatch
- **Investigator (lead):** Finalize 5 Whys; optional register elimination / FMEA
- **Critic:** Challenge rankings, look for bias

## Finalize 5 Whys (mandatory)

Extend `.diagnose-five-whys.json` until `templates/five-why-protocol.md` stop checklist passes on each leading chain:

- `root_cause`, `but_for`, `stop_reason`
- Causal linkage between layers

If hypothesis register is active, link chains to **`confirmed`** hypothesis IDs when applicable.

## Full-register elimination (only when hypothesis technique activated)

Skip unless **Hypothesis-driven problem solving** is in `activated_techniques`.

Work through **every** non-`deferred` hypothesis in discriminating-test order:

1. Predict → falsify → update `status` (`ruled_out` \| `plausible` \| `confirmed`)
2. Record evidence pointers
3. Persist `.diagnose-hypotheses.json` before step 5

(Minimum **{{HYPOTHESIS_MIN}}** hypotheses required when register is in play.)

## Optional toolbox (apply only if activated or routed)

| Technique | When to run in this phase |
|-----------|---------------------------|
| FMEA | Activated or high-severity profile — `python3 {{SCRIPT_DIR}}/fmea_score.py` |
| Pareto | Vital-few drivers — ranked list with counts |
| Bayesian / counterfactual | Plausible hypotheses — but-for test per chain |

## Data-Driven Correlation

When evidence supports it:

- Metrics at symptom onset (`templates/data-analysis.md`)
- `python3 {{SCRIPT_DIR}}/git_hotspots.py --path <dir>`
- `python3 {{SCRIPT_DIR}}/log_analyzer.py --file <logfile>`

## Technique Coverage Matrix (update)

Update rows for **activated** techniques only — `applied` requires `evidence_pointer`.

Summary: {{TECHNIQUE_COVERAGE_SUMMARY}}

See `prompts/diagnose/technique_catalog.md` for catalog names and routing map.

{{AUTONOMY_GATE}}
