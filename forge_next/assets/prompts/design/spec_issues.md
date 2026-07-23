# Design spec → issues (prep for plan)

When `SPEC_REQUIRED` is **yes**, decompose the approved design spec into **plan-ready issues** before handoff. This step runs **after** `.design-spec-gate.json` is complete and **before** `forge design --step 8`.

Current scope signals:

- **Scope tier:** {{SCOPE_TIER}}
- **Spec required:** {{SPEC_REQUIRED}}
- **Spec gate status:** {{SPEC_GATE_STATUS}}
- **Spec issues gate status:** {{SPEC_ISSUES_GATE_STATUS}}
- **State directory (sidecar goes next to design state):** `{{STATE_DIR}}`

{{DEVELOP_NO_EDIT_POLICY}}

## 1. Read the approved spec

1. Open the path from `.design-spec-gate.json` (`spec_path`).
2. Map each issue to explicit **spec sections** (headings from [templates/design-spec.md](templates/design-spec.md)).
3. Each issue should be **INVEST-sized** — one coherent deliverable plan can schedule in a single wave or small sequence.

**Splitting rules:**

- Prefer **vertical slices** (user-visible capability) over layer-only tickets (“add migration”, “write tests”) unless the spec isolates that work.
- Cover the full spec: every major section in **Chosen design**, **Data / API / schema impact**, **Error handling**, **Test strategy**, and **Rollout** should trace to at least one issue.
- Flag **open questions** as their own issues when they block planning.
- If the spec is still monolithic after splitting, add a note in the epic description — do not hand off a single catch-all issue.

## 2. Beads (when available)

Check `project.md` for `beads: available` (see step 1 startup). Follow [templates/beads-integration.md](templates/beads-integration.md).

**When beads is available:**

1. Create or reuse the session **epic** (`-t epic`, labels `forge,design,plan-prep`).
2. For each issue: `bd create` with `--parent [epic-id]`, `-t task`, labels `plan-prep,stage-design,spec-slice`.
3. Add `discovered-from` deps from issues back to the epic when useful for provenance.
4. Record each `beads_id` on the matching issue row in the sidecar.

**When beads is unavailable (degraded):**

- Assign local IDs (`D-001`, `D-002`, …) and still write the sidecar.
- Note degraded mode in `project.md` if not already recorded.

## 3. User confirmation

Present the issue list as a **numbered table**: title, spec sections covered, acceptance criteria (1–2 bullets each). Ask:

> Confirm this decomposition is ready for planning?

Revise until the user confirms. Planning should not re-litigate scope hidden inside vague issues.

## 4. Record completion (mandatory for step 8)

Write **`.design-spec-issues.json`** in **`{{STATE_DIR}}`** with **exactly** this shape:

```json
{
  "spec_path": "docs/forge/specs/YYYY-MM-DD-<slug>-design.md",
  "issues_written": true,
  "user_confirmed": true,
  "beads_mode": "active",
  "epic_id": "beads-epic-id-or-none",
  "issues": [
    {
      "id": "D-001",
      "beads_id": "optional-when-active",
      "title": "Short imperative title",
      "summary": "One paragraph — what plan should deliver",
      "spec_sections": ["Chosen design", "Data / API / schema impact"],
      "acceptance_criteria": [
        "Observable outcome 1",
        "Observable outcome 2"
      ]
    }
  ]
}
```

- `spec_path` must match `.design-spec-gate.json`.
- `beads_mode`: `active` | `degraded` | `none`.
- At least **one** issue; prefer **3–8** for medium scope, more only when the spec is genuinely large.

## Overrides

If you must hand off without a complete issue split, the human must re-run step 8 with documented override flags (see `forge design --help`).
