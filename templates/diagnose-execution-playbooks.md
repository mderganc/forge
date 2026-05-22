# Diagnose Execution Playbooks

Operational layer for [`prompts/diagnose/technique_catalog.md`](../prompts/diagnose/technique_catalog.md). Deep theory: [`skills/diagnose/references/methodologies.md`](../skills/diagnose/references/methodologies.md).

**Before each diagnose phase:** read the sections listed in the phase prompt for techniques you will apply or skip.

## Playbook template (every technique)

| Field | Requirement |
|-------|-------------|
| **When** | Incident profile / severity from Phase 1 routing |
| **Phase** | Diagnose step that must produce the artifact |
| **Minimum artifact** | Sidecar path or memory section with required fields |
| **Anti-patterns** | Checkbox compliance without evidence |
| **Done** | Gate passes or matrix row `applied` with `evidence_pointer` |

---

## Adjunct methods (Phase 1–2)

### Kepner-Tregoe IS/IS-NOT

- **When:** Every run; sudden deviation / discrimination needed.
- **Phase:** 1 → `.diagnose-problem-spec.json`
- **Minimum artifact:** `is_isnot.WHAT|WHERE|WHEN|EXTENT` each with `is`, `is_not`, `distinction`.
- **Anti-patterns:** Empty cells; distinction repeats IS text.
- **Done:** Step 4 problem-spec gate passes.

### Cynefin classification

- **When:** Phase 1; drives strategy (chaotic → stabilize first).
- **Phase:** 1 → `cynefin_domain` in problem spec.
- **Minimum artifact:** One of Clear / Complicated / Complex / Chaotic + one-line strategy note.
- **Anti-patterns:** Label without changing investigation depth.
- **Done:** Domain recorded; Phase 4 strategy matches domain.

### Change analysis

- **When:** “Worked before, now doesn't”; regressions.
- **Phase:** 1–2 → problem spec + evidence timeline.
- **Minimum artifact:** `last_known_good`, `change_window`, `candidate_changes[]` with category + evidence.
- **Anti-patterns:** “Something changed” without LKG timestamp/commit.
- **Done:** At least one change candidate linked to evidence.

### Gemba observation (catalog #13)

- **When:** UI/repro-heavy incidents.
- **Phase:** 2 evidence checklist.
- **Minimum artifact:** Minimal repro steps + artifact IDs (log path, screenshot, HAR).
- **Anti-patterns:** “User saw error” without repro.
- **Done:** Evidence checklist item checked with pointer.

### Control charts / run charts (#16)

- **When:** Metric spikes; SLO breaches.
- **Phase:** 2 → metrics baseline vs degraded in evidence.
- **Minimum artifact:** Metric name, baseline value, onset time, or `metric_unavailable` rationale.
- **Anti-patterns:** “Latency increased” without numbers.
- **Done:** Coverage row or evidence section cites metric.

### Barrier / Swiss Cheese (#20)

- **When:** Safety/compliance; prod escape.
- **Phase:** 2 draft, 7 finalize → `.diagnose-barriers.json`
- **Minimum artifact:** ≥3 layers with `exists`, `active`, `detected`, `failure_mode`.
- **Anti-patterns:** “Tests should have caught it” for every layer.
- **Done:** Barrier sidecar validates when profile requires.

---

## Mandatory core quartet

### 1. Five Whys

- **When:** All runs; frontline operational incidents prefer this (catalog routing).
- **Phase:** 3 draft chains on leading branches; **4 finalize** on **confirmed** hypotheses only.
- **Minimum artifact:** `.diagnose-five-whys.json` — see [`templates/five-why-protocol.md`](five-why-protocol.md) § Diagnose RCA.
- **Anti-patterns:** Unrelated why questions; symptom layers; stopping at layer 1.
- **Done:** Step 5/7 five-whys gate passes.

### 2. Fishbone / Ishikawa (#2)

- **When:** Multi-driver brainstorming.
- **Phase:** 3 → hypothesis register `category` + MECE nodes.
- **Minimum artifact:** ≥10 register entries spanning ≥4 of CODE|CONFIG|DATA|INFRASTRUCTURE|DEPENDENCIES|ENVIRONMENT.
- **Anti-patterns:** Six category headers with one vague bullet each.
- **Done:** Hypothesis register gate at step 4.

### 3. First-principles thinking (#3)

- **When:** All runs (quartet).
- **Phase:** 1–2 baseline; 4 tie-in → `.diagnose-first-principles.json`
- **Minimum artifact:** `invariants[]`, `violations[]` with `observation_links`.
- **Anti-patterns:** “System should work” as invariant.
- **Done:** Step 4 first-principles gate passes.

### 4. MECE issue tree (#4)

- **When:** All runs (quartet).
- **Phase:** 3 → `.diagnose-mece-tree.json`
- **Minimum artifact:** ≥3 nodes; `parent_id`, `category`, optional `hypothesis_ids[]`, `mutual_exclusion_note` for sibling overlap.
- **Anti-patterns:** Duplicate branches; orphan nodes.
- **Done:** Step 4 MECE gate passes.

### 5. Hypothesis-driven problem solving (#5)

- **When:** All runs (quartet).
- **Phase:** 3–4 → `.diagnose-hypotheses.json`
- **Minimum artifact:** Predict → falsify → update status for **every** entry before step 5.
- **Anti-patterns:** Open hypotheses at solution phase.
- **Done:** Elimination gate at step 5.

---

## Toolbox 6–20 (apply or skip with rationale)

### 6. Fault Tree Analysis

- **When:** High-severity; multiple interacting causes.
- **Phase:** 3–4 optional `.diagnose-fault-tree.json` or MECE + logic tree in memory.
- **Minimum artifact:** Top event + AND/OR gates to basic events, or coverage `applied` with pointer.
- **Anti-patterns:** Single OR branch listing symptoms only.
- **Done:** Matrix row + evidence; mandatory OR with FMEA on high-severity.

### 7. Current Reality Tree

- **When:** Recurring systemic patterns.
- **Phase:** 4–7 UDE chain ≥3 links in memory or coverage pointer.
- **Minimum artifact:** UDE → intermediate causes → core conflict.
- **Anti-patterns:** Jump from symptom to “culture problem”.
- **Done:** Coverage row documents chain location.

### 8. Kepner-Tregoe Problem Analysis

- **When:** Sudden deviation (catalog); same as IS/IS-NOT adjunct.
- **Phase:** 1 problem spec.
- **Done:** IS/IS-NOT + distinction complete.

### 9. A3 Problem Solving

- **When:** Lean/management review (rare in software).
- **Phase:** Usually **skipped** with profile rationale.
- **Minimum if applied:** A3 sections 1–5 outline in memory.

### 10. 8D Problem Solving

- **When:** Supplier/formal CAPA.
- **Phase:** Skip unless compliance profile; if applied, D1–D4 outline.

### 11. Process Mapping / SIPOC

- **When:** Handoff/ownership bugs.
- **Phase:** 2–3 SIPOC table ≥5 filled cells if applied.

### 12. Value Stream Mapping

- **When:** Flow/latency end-to-end.
- **Phase:** Skip default; if applied, value-stream sketch with bottleneck marked.

### 13. Gemba Observation

- See adjunct above.

### 14. Pareto Analysis

- **When:** Most runs after elimination.
- **Phase:** 4 ranked list with counts or metric shares.
- **Minimum artifact:** Ordered causes/defects with numeric weight.
- **Anti-patterns:** “80% is X” without data.

### 15. Stratification Analysis

- **When:** Subgroup differences (env, tenant, version).
- **Phase:** 4 slice table: dimension × outcome.

### 16. Control charts / run charts

- See adjunct above.

### 17. Scatter plot / correlation

- **When:** Quick variable screening.
- **Phase:** 4 two variables + conclusion if applied.

### 18. FMEA

- **When:** Phase 4 always; high-severity mandatory.
- **Phase:** 4 → `fmea_score.py` output or register S/O/D + justification per hypothesis.
- **Anti-patterns:** RPN without evidence-based O scores.
- **Done:** Script output or register fields; coverage `applied`.

### 19. Design of Experiments

- **When:** Multi-factor complex processes only.
- **Phase:** Skip default; if applied, factors + test matrix sketch.

### 20. Barrier Analysis

- See adjunct / Swiss Cheese above.

---

## Phase 4 adjuncts

### Bayesian update

- **When:** Ranking plausible hypotheses after falsification.
- **Phase:** 4 register or analyze notes: `prior`, `likelihood_note`, `posterior_band` per plausible ID.
- **Anti-patterns:** “High confidence” without evidence cite.

### Counterfactual / but-for

- **When:** Before confirming root cause.
- **Phase:** 4 + five-whys `but_for` field per confirmed chain.
- **Anti-patterns:** Correlation without but-for test.

### Pareto

- See #14 above.

---

## Coverage matrix (all 20)

Finalize in Phase 7 → `.diagnose-technique-coverage.json` with exact catalog names from `technique_catalog.md`. Step 5 gates **routed** techniques from `routing_preferred`.
