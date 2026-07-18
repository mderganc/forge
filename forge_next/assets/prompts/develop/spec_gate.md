# Design spec gate (medium / large scope)

When `SPEC_REQUIRED` is **yes** (scope tier `medium` or `large` from `design-scope.json`; legacy `develop-scope.json` still read), you **must** complete this gate **before** running `forge design --step 7` (spec → issues).

Current scope signals (from orchestrator state):

- **Scope tier:** {{SCOPE_TIER}}
- **Spec required:** {{SPEC_REQUIRED}}
- **Rationale:** {{SCOPE_RATIONALE}}
- **State directory (sidecar goes next to design state):** `{{STATE_DIR}}`

## Status

{{SPEC_GATE_STATUS}}

## 1. Write the design spec

1. Follow [templates/design-spec.md](templates/design-spec.md).
2. Save the file under **`docs/forge/specs/YYYY-MM-DD-<short-slug>-design.md`** (create `docs/forge/specs/` if needed).
3. In **Context**, reference:
   - `sketch-decisions.md` when present (intent and resolved branches from sketch)
   - Approved direction from `solutions.md` / user approval on step 6
4. **Commit** the spec to git when the team requires an audit trail (recommended for medium/large).

**Allowed edits:** spec path is a normal tracked documentation path — you may create/edit under `docs/forge/specs/` for this artifact. Session memory rules still apply elsewhere.

## 2. Self-review (inline)

Re-read the spec and fix before involving the user:

1. **Placeholder scan:** no `TBD`, empty sections, or vague “should” without criteria.
2. **Consistency:** architecture matches goals; no contradictions vs `solutions.md` or `sketch-decisions.md` without an explicit “changed decision” note.
3. **Scope:** one coherent plan-sized design; flag if it needs splitting.
4. **Ambiguity:** every requirement has one clear interpretation.

## 3. User review (chunked)

Present the written spec to the user in **2–4 chunks** aligned with [templates/design-spec.md](templates/design-spec.md) (*Review with the user in chunks*): e.g. (1) goals / non-goals / constraints, (2) candidate snapshot + chosen design, (3) data/ops/tests, (4) rollout / assumptions / open questions. **Confirm each chunk** before moving on; use **one question at a time** for follow-ups. After the final chunk and any edits, ask for explicit approval to record the gate.

## 4. Record completion (mandatory for step 7)

Write **`.design-spec-gate.json`** in **`{{STATE_DIR}}`** (same directory as the design session state) with **exactly** this shape:

```json
{
  "spec_path": "docs/forge/specs/YYYY-MM-DD-<slug>-design.md",
  "spec_written": true,
  "self_review_passed": true,
  "user_approved": true
}
```

Use a repo-relative path for `spec_path`. All three booleans must be `true` for the gate to pass.

## Overrides

If you must hand off without a complete spec, the human must re-run **step 8** with documented override flags (see `forge design --help`).
