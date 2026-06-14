# RCA Technique Catalog (Forge Diagnose)

Referenced by prompts and tests. **Adaptive diagnose spine:**

1. **Phase 1:** Pick **one** entry framing path (`framing_entry` in `.diagnose-problem-spec.json`) — KT IS/IS-NOT, Cynefin, first-principles snapshot, evidence snapshot, or MECE sketch.
2. **Phase 3–4:** **5 Whys** — always; documented in `.diagnose-five-whys.json` (orchestrator-gated).
3. **As needed:** Activate other catalog techniques via `activated_techniques` / `routing_preferred` when the incident profile warrants them (MECE, hypothesis register, FMEA, etc.).

Do **not** run every framing method or fill all 20 technique rows on simple incidents. Prefer matches whose **best-use-case** fits the incident profile.

## Severity / scalability rules

- **Small / simple:** framing + 5 Whys only unless signal demands more — justify additions.
- **High-severity / recurring / systemic:** broaden technique coverage — justify additions.
- **Safety / compliance / high-consequence:** mandatory paths — **Kepner-Tregoe-style discrimination**, **barrier analysis**, plus **fault tree** or **FMEA** depth as appropriate (mandatory set overrides preference).

## Tie-break / conflict policy

- If multiple techniques fit, prefer **lower-cost / higher-signal** methods first unless severity mandates stricter ones.
- **Mandatory set** (policy/compliance/safety) overrides preference routing.

## Preferred-use-case routing map

| Incident profile | Prefer |
|-----------------|--------|
| Simple operational / frontline quick investigation | 5 Whys |
| Messy multi-driver brainstorming | Fishbone / Ishikawa |
| Ambiguous strategy / process redesign / challenging assumptions | First-principles thinking |
| Executive framing / large complex decomposition | MECE issue tree |
| Fast time-boxed analytics turnaround | Hypothesis-driven problem solving |
| High-consequence failure / safety / reliability trees | Fault Tree Analysis |
| Recurring systemic constraint patterns | Current Reality Tree *(deprioritized — skip by default)* |
| “Worked before, now doesn’t” / sudden deviations / complaints | Kepner-Tregoe Problem Analysis |
| Lean operational coaching / management review | A3 Problem Solving *(deprioritized — skip by default)* |
| Formal corrective-action / supplier quality workflows | 8D Problem Solving *(deprioritized — skip by default)* |
| Unclear ownership / handoff / process entry points | Process Mapping / SIPOC |
| Lead-time / waste / bottleneck flow issues | Value Stream Mapping |
| Reality vs procedure / operator workaround questions | Gemba Observation |
| Vital-few defect / loss drivers | Pareto Analysis |
| Hidden subgroup differences | Stratification Analysis |
| Variation-over-time / stability | Control Charts / Run Charts |
| Quick variable-relationship screening | Scatter Plot / Correlation Analysis |
| Preventive launch / design / process risk ranking | FMEA |
| Interacting factors / proving drivers in complex processes | Design of Experiments *(deprioritized — skip by default)* |
| Control failure / bypass / missing safeguards | Barrier Analysis |

## Execution playbooks

Before applying or skipping a technique, read **`templates/diagnose-execution-playbooks.md`** for that technique’s phase, minimum artifact, anti-patterns, and done criteria.

Persist coverage in **`.diagnose-technique-coverage.json`** (one row per **activated** technique; exact catalog names below).

## Deprioritized techniques (default skip)

Do **not** activate unless the incident profile clearly warrants them — record as **skipped** with rationale when not activated:

| Technique | Default |
|-----------|---------|
| Current Reality Tree (CRT) | Skip — reserve for confirmed TOC/systemic constraint cases |
| A3 Problem Solving | Skip — reserve for formal lean coaching / management review |
| 8D Problem Solving | Skip — reserve for supplier-quality / formal corrective-action workflows |
| Design of Experiments (DoE) | Skip — reserve when multivariate driver proof is required |

## Full toolbox (activated rows only at closure)

For each **activated** technique in the coverage matrix, state **applied**, **skipped**, or **deferred** with rationale and evidence pointers. Step 7 gates validate **activated** rows only (`adaptive=True`), not all 20 catalog entries.

| # | Technique | Notes |
|---|-----------|-------|
| 1 | 5 Whys | Always activated |
| 2 | Fishbone / Ishikawa | |
| 3 | First-principles thinking | |
| 4 | MECE issue tree | |
| 5 | Hypothesis-driven problem solving | |
| 6 | Fault Tree Analysis | |
| 7 | Current Reality Tree | Deprioritized — default skip |
| 8 | Kepner-Tregoe Problem Analysis | |
| 9 | A3 Problem Solving | Deprioritized — default skip |
| 10 | 8D Problem Solving | Deprioritized — default skip |
| 11 | Process Mapping / SIPOC | |
| 12 | Value Stream Mapping | |
| 13 | Gemba Observation | |
| 14 | Pareto Analysis | |
| 15 | Stratification Analysis | |
| 16 | Control Charts / Run Charts | |
| 17 | Scatter Plot / Correlation Analysis | |
| 18 | FMEA | |
| 19 | Design of Experiments | Deprioritized — default skip |
| 20 | Barrier Analysis | |
