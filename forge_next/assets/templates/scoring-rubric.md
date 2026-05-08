# Scoring Rubric

Used in Stage 2 (Solution Evaluation) and Stage 3 (User Approval) to score solution options.

## Dimensions

| Dimension | Scale | Measures | Example Anchors |
|-----------|-------|----------|----------------|
| Impact - Quality (Q) | 1-10 | Effect on code quality, reliability, maintainability | 1=negligible, 5=moderate improvement, 10=transformative |
| Impact - Time (T) | 1-10 | Effect on development velocity, time savings | 1=no time impact, 5=saves hours/week, 10=saves days/week |
| Impact - Cost (C) | 1-10 | Effect on operational/infrastructure costs | 1=no cost impact, 5=moderate savings, 10=major cost reduction |
| Impact - Risk (R) | 1-10 | Risk reduction (security, data loss, downtime) | 1=no risk change, 5=reduces moderate risk, 10=eliminates critical risk |
| Effort (E) | 1-10 | Implementation complexity and time | 1=trivial (<1hr), 5=moderate (1-3 days), 10=massive (weeks) |
| Priority (P) | Auto | Urgency ranking | Calculated — see formula |

## Priority Auto-Calculation

Priority = (avg(Q, T, C, R) / E) * normalization_factor

Normalization scales the result to 1-10 range. Higher priority = more impact per unit effort.

## Specific Values Override

When a dimension has a calculable specific value, use it instead of the 1-10 scale:
- Cost: `$2.43/run saved` instead of `C=7`
- Time: `~4hrs/week saved` instead of `T=6`
- Risk: `Eliminates 3 of 5 OWASP categories` instead of `R=8`

The 1-10 score is still provided alongside for comparison across solutions.

## Scoring Table Format

| Dimension | Score (1-10) | Notes |
|-----------|-------------|-------|
| Impact - Quality | 7 | [specific justification] |
| Impact - Time | 4 | [specific justification] |
| Impact - Cost | 3 | [specific justification or calculable value] |
| Impact - Risk | 8 | [specific justification] |
| Effort | 6 | [specific justification] |
| Priority (auto) | 5.5 | avg(7,4,3,8)/Effort, normalized |

## Scoring Integrity Rules

1. Every score must have a justification in the Notes column — no bare numbers.
2. Scores must be defensible — if the critic challenges a score, the Architect must explain it.
3. Scores across solutions for the same root cause should be internally consistent (e.g., if Solution A effort=3 and Solution B effort=8, the difference should be explainable).
4. After implementation (Stage 6), actual scores are compared against estimates for learning.
5. **Source data grounds every score.** Justifications must cite first-hand evidence (code measurements, test results, profiler output, dependency counts, LOC estimates) rather than relying solely on synthesized assessments or LLM judge ratings. When an LLM judge has rated something, include the rating but always present the underlying source data alongside it — the source data is the primary basis for the score.
