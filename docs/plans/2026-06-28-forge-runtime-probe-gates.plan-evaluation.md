# Pre-implementation evaluation: runtime adaptation + probe gates

**Plan:** [2026-06-28-forge-runtime-probe-gates.plan.md](./2026-06-28-forge-runtime-probe-gates.plan.md)  
**Design:** [../forge/specs/2026-06-28-forge-runtime-probe-gates-design.md](../forge/specs/2026-06-28-forge-runtime-probe-gates-design.md)  
**Date:** 2026-06-28  
**Verdict:** **Proceed with revisions** (W0–W3 first; defer intent router)

---

## Summary

The plan addresses real Codex transcript failures: mount aliases, silent probe hangs, and agent bypass. Three rules (`.forge/` only, auto path adapt, loud gated probes) are sound. Implementation is **feasible** but larger than the plan suggests because Forge today canonicalizes `.codex/forge/` when writable — reversing that touches tests, docs, and integrations.

**Simplifications applied after review:**

- Deferred intent router (W4) to a follow-up PR.
- Renamed integration/template work to W4 (was W5).
- Probe gate builds on existing `code_review/structural_probes_gate.py`.
- RAL wraps `repo_paths.py` instead of replacing it.

---

## Critical (must fix in plan before implement)

| ID | Issue | Action |
|----|-------|--------|
| F11 | Dual-runtime race during migration | Migrate on step 1 **before** `create_session`; `takeover`/`status` read both roots until archive complete |

---

## Warnings (address in W0–W3)

| ID | Issue | Action |
|----|-------|--------|
| F1 | W0 inverts canonical runtime | Rewrite `test_shared_orchestrator.py` + doc sweep in W0 |
| F2 | Gate module partially exists | Refactor to `scripts/shared/structural_probes_gate.py` |
| F5/F8 | Semver + integrations missing from tasks | Add explicit minor/major decision; W4 covers all integration surfaces |
| F12 | CI hard-fail on gates | Document `--allow-structural-probes-incomplete` + override reason for CI |
| F13 | DEGRADED gate friction | Loud banner always; user gate on FAILED/SKIPPED always; DEGRADED prompts but allow “defer to ship” default |

---

## Suggestions (nice to have)

| ID | Issue |
|----|-------|
| F3/F14 | Intent router deferred ✓ |
| F7/F9/F10 | Reuse `workflow_gate.py`, `repo_paths.py`, diagnose gate patterns |
| F6 | Define `forge_probe_gate_multiselect` schema in W2 |

---

## Recommended ship order

1. **W0** — `.forge/` runtime + migration + tests  
2. **W1** — RAL / writable alias  
3. **W2** — Loud probes + pause gate  
4. **W3** — Timeouts + ship + CI overrides  
5. **W4** — Integration path updates  

---

## Gate recommendation

**Approve for implement** after F11 migration ordering is added to W0 task list.
