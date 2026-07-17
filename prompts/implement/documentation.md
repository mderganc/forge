# Phase 7: Documentation

Dispatch **Doc-writer** (and specialists as needed) to align repo docs and external wiki evidence with the **plan file Documentation section** and audience applicability.

## Plan prerequisites

Read the plan file from implement state (`plan_path`): especially **§ Documentation** — applicability matrix, Documentation Definition of Done table, and external wiki checklist.

## Doc-writer checklist

1. Read `{{MEMORY_DIR}}/` for context.
2. Read code changes on the feature branch.
3. Update or create documentation per the plan:
   - **User** audience: end-user behavior, limits, migration, CLI/API usage.
   - **Technical operator** audience: deploy, runbooks, troubleshooting, observability.
   - **Architect / expert** audience: ADRs, architecture, interfaces, tradeoffs.
4. Cover **tracked paths** and **wiki mirrors** listed in the plan (`wiki/`, `.wiki/`, `docs/wiki/` when present).
5. For **each applicable** audience row, ensure there is shippable documentation matching `acceptance_check` in the plan.
6. Follow existing project documentation patterns; inline comments only where logic is non-obvious. Docs must match real surfaces (no documenting unused/speculative exports — `templates/structural-build-charter.md`).
7. Summarize doc-writer activity in `{{MEMORY_DIR}}/doc-writer.md`.

## Documentation gate file (required)

Write **`{{STATE_DIR}}/.implement-documentation-gate.json`** next to the implement state file (same directory as the `--state` path). Replace `{{STATE_DIR}}` with the directory containing `implement.json` (or your `--state` path).

### JSON schema

```json
{
  "complete": true,
  "audience_matrix": [
    {
      "audience_level": "architect_expert",
      "applicable": false,
      "justification": "No architecture surface changed.",
      "delivery_evidence": ""
    },
    {
      "audience_level": "technical_operator",
      "applicable": true,
      "justification": "Deployment script changed.",
      "delivery_evidence": "docs/runbook.md updated; see commit …"
    },
    {
      "audience_level": "user",
      "applicable": true,
      "justification": "CLI flag added.",
      "delivery_evidence": "README.md Usage section; CHANGELOG.md entry"
    }
  ],
  "external_wiki_checklist": [
    {
      "system": "GitHub Wiki",
      "page": "Runbook",
      "owner": "team",
      "status": "updated",
      "evidence_link": "https://…"
    }
  ],
  "notes": "optional free text"
}
```

### Rules

- **`complete`:** set `true` only when documentation work for this change is done **or** honestly deferred with explicit rationale captured under `notes` (strict gate still expects plan markers cleared — see below).
- **`audience_matrix`:** must include exactly one row each for `architect_expert`, `technical_operator`, and `user` (normalized aliases accepted by the gate).
  - **`applicable`:** boolean or `yes`/`no`.
  - **`justification`:** non-empty for every row (why in or out of scope).
  - **`delivery_evidence`:** when `applicable` is **true**, must be non-empty (paths, links, PR refs). When `applicable` is **false**, may be empty.
- **`external_wiki_checklist`:** required array. Use `[]` if no external wikis apply. Each item must include **`status`**. If status is not N/A, include **`evidence_link`** (URL or ticket).

## Plan file Documentation marker

Replace the `<!-- FORGE_SKELETON: DOCUMENTATION -->` marker in the plan with real content during this phase. **Implement step 8** refuses to run the handoff while that marker still exists in the plan file (unless the user passes override flags — see README).

## Review

- Self-review: Doc-writer
- Cross-review: QA (examples work, terminology)
- Critic: docs match reality and plan

## Quick Mode

{{QUICK_MODE_NOTE}}
