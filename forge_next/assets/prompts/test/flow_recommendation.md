# Phase 2: Flow-Type Recommendation

**Lead: QA + Architect**

Score each flow type against the eight criteria and write a recommendation sidecar.

## Checklist

- [ ] Read **`templates/test-flow-criteria.md`** (evaluation rubric) and **`templates/mock-flow-types.md`** (four types, layouts, anti-patterns).
- [ ] Note project signals: framework `{{FRAMEWORK}}` ({{FRAMEWORK_CONFIDENCE}}), entry point `{{ENTRY_POINT}}` ({{ENTRY_POINT_CONFIDENCE}}), test DB `{{TEST_DB}}`, roles `{{ROLES}}`.
- [ ] If **`--flow-type`** override (`{{FLOW_TYPE_OVERRIDE}}`): acknowledge override, skip scoring, exit (sidecar pre-written).
- [ ] Score each type (scenario, bdd, http-replay, workflow-dryrun) 0–10 per criterion; pick `chosen` with `confidence` and `alternatives`.
- [ ] Write **`.test-recommendation-step2.json`** in the state directory:

```json
{
  "chosen": "scenario|bdd|http-replay|workflow-dryrun",
  "reasoning": "...",
  "confidence": 0.0,
  "alternatives": [{"type": "...", "score": 0.0, "reason": "..."}]
}
```

- [ ] Verify sidecar with `cat` before advancing.
