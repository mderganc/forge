# Diagnose Prompt Routing

Start here. Full technique list and severity rules: **`prompts/diagnose/technique_catalog.md`**. Operational when/artifact rules: **`templates/diagnose-execution-playbooks.md`**.

## Phase → prompt → playbook

| Step | Prompt | Primary playbooks |
|------|--------|-------------------|
| 1 Define | `define.md` | KT IS/IS-NOT, Cynefin, change analysis → `.diagnose-problem-spec.json` |
| 2 Evidence | `evidence.md` | Feedback loop, Gemba → `.diagnose-feedback-loop.json` |
| 3 Decompose | `decompose.md` | MECE tree, fishbone, first principles (when activated) |
| 4 Analyze | `analyze.md` | **5 Whys** (always), hypothesis register, elimination |
| 5 Solutions | `solutions.md` | Barrier analysis, FMEA (when activated) |
| 6 Quick fix | `quick_fix.md` | Minimal repro validation |
| 7 Report | `report.md` | Technique coverage matrix, closure gates |

## Adaptive spine

1. **Phase 1:** one framing path (`framing_entry` in problem spec).
2. **Phase 2:** feedback loop before hypotheses (gate at step 3).
3. **Phase 3–4:** **5 Whys always**; MECE / hypothesis / first-principles only when in `activated_techniques`.
4. **High-severity:** mandatory KT discrimination, barrier analysis, fault tree or FMEA — see catalog severity rules.

## Sidecar index

| File | Phase |
|------|-------|
| `.diagnose-problem-spec.json` | 1 |
| `.diagnose-feedback-loop.json` | 2 |
| `.diagnose-five-whys.json` | 3–4 |
| `.diagnose-hypotheses.json` | 4 (when activated) |
| `.diagnose-mece-tree.json` | 4 (when activated) |
| `.diagnose-first-principles.json` | 4 (when activated) |
| `.diagnose-technique-coverage.json` | 1 draft → 7 final |
| `.diagnose-barriers.json` | 2–7 |

Before applying or skipping a technique, read its playbook section in **`templates/diagnose-execution-playbooks.md`**.
