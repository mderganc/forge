# RCA Technique Catalog (Forge Diagnose)

Referenced by prompts and tests. Every diagnose run must complete the **mandatory core quartet** before closure:

1. **First-principles thinking** — baseline invariants, causal decomposition from fundamentals.
2. **Hypothesis-driven problem solving** — ranked hypotheses tied to evidence.
3. **5 Whys** — documented drill on leading branches (may conclude earlier if validated).
4. **MECE issue tree** — mutually exclusive, collectively exhaustive decomposition.

Then add **use-case-first** techniques from the map below. Prefer matches whose **best-use-case** fits the incident profile before generic breadth.

## Severity / scalability rules

- **Small / simple:** minimal subset beyond the quartet — justify omissions.
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
| Recurring systemic constraint patterns | Current Reality Tree |
| “Worked before, now doesn’t” / sudden deviations / complaints | Kepner-Tregoe Problem Analysis |
| Lean operational coaching / management review | A3 Problem Solving |
| Formal corrective-action / supplier quality workflows | 8D Problem Solving |
| Unclear ownership / handoff / process entry points | Process Mapping / SIPOC |
| Lead-time / waste / bottleneck flow issues | Value Stream Mapping |
| Reality vs procedure / operator workaround questions | Gemba Observation |
| Vital-few defect / loss drivers | Pareto Analysis |
| Hidden subgroup differences | Stratification Analysis |
| Variation-over-time / stability | Control Charts / Run Charts |
| Quick variable-relationship screening | Scatter Plot / Correlation Analysis |
| Preventive launch / design / process risk ranking | FMEA |
| Interacting factors / proving drivers in complex processes | Design of Experiments |
| Control failure / bypass / missing safeguards | Barrier Analysis |

## Full toolbox (record coverage for each)

For each technique in the final report matrix, state **applied**, **skipped**, or **deferred** with rationale and evidence pointers.

| # | Technique |
|---|-----------|
| 1 | 5 Whys |
| 2 | Fishbone / Ishikawa |
| 3 | First-principles thinking |
| 4 | MECE issue tree |
| 5 | Hypothesis-driven problem solving |
| 6 | Fault Tree Analysis |
| 7 | Current Reality Tree |
| 8 | Kepner-Tregoe Problem Analysis |
| 9 | A3 Problem Solving |
| 10 | 8D Problem Solving |
| 11 | Process Mapping / SIPOC |
| 12 | Value Stream Mapping |
| 13 | Gemba Observation |
| 14 | Pareto Analysis |
| 15 | Stratification Analysis |
| 16 | Control Charts / Run Charts |
| 17 | Scatter Plot / Correlation Analysis |
| 18 | FMEA |
| 19 | Design of Experiments |
| 20 | Barrier Analysis |
