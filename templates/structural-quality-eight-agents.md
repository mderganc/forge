# Structural quality — eight parallel subagents (Civil Learning)

Pass B structural review uses **eight parallel subagents**, not a single reviewer wearing eight hats. The orchestrator spawns all eight at team dispatch (code-review step 3, evaluate post step 4, evaluate review step 1) after structural probes are planned or run.

## Master prompt (source wording)

Use this charter when briefing the lead or the user; each subagent gets **one numbered item** plus the shared closing line.

> I want to clean up my codebase and improve code quality. This is a complex task, so we'll need 8 subagents. Make a sub agent for each of the following:
>
> 1. Deduplicate and consolidate all code, and implement DRY where it reduces complexity
> 2. Find all type definitions and consolidate any that should be shared
> 3. Use tools like knip to find all unused code and remove, ensuring that it's actually not referenced anywhere
> 4. Untangle any circular dependencies, using tools like madge
> 5. Remove any weak types, for example 'unknown' and 'any' (and the equivalent in other languages), research what the types should be, research in the codebase and related packages to make sure that the replacements are strong types and there are no type issues
> 6. Remove all try catch and equivalent defensive programming if it doesn't serve a specific role of handling unknown or unsanitized input or otherwise has a reason to be there, with clear error handling and no error hiding or fallback patterns
> 7. Find any deprecated, legacy or fallback code, remove, and make sure all code paths are clean, concise and as singular as possible
> 8. Find any AI slop, stubs, larp, unnecessary comments and remove. Any comments that describe in-motion work, replacements of previous work with new work, or otherwise are not helpful should be either removed or replaced with helpful comments for a new user trying to understand the codebase-- but if you do edit, be concise
>
> I want each to do detailed research on their task, write a critical assessment of the current code and recommendations, and then implement all high confidence recommendations.

## Forge guardrails

| Context | Implement high-confidence fixes? |
|---------|----------------------------------|
| `forge:code-review`, `forge:evaluate` | **No** by default — findings + recommendations only |
| `forge:implement`, user asked to fix | **Yes** when edits are in scope |

Always: read `.structural-probes.json` (and probe plan/inventory sidecars); cite `K*`, `M*`, `P*` IDs; confirm deletions with graphify or traces (see `templates/structural-quality-probes.md` false-positive rules).

## Parallel dispatch

Spawn **all eight** subagents in one wave. Required lifecycle: `spawn_agent` → wait → capture → **`close_agent`** before the next orchestrator step (`templates/codex-runtime.md`).

| ID | Subagent | Mission | Tool hints |
|----|----------|---------|------------|
| **S1** | DRY / deduplication | Item 1 above | pyscn clones; graphify |
| **S2** | Shared types | Item 2 | mypy, tsc |
| **S3** | Dead code | Item 3 | knip, pyscn deadcode |
| **S4** | Circular deps | Item 4 | madge `--circular` |
| **S5** | Weak types | Item 5 | mypy, tsc |
| **S6** | Error handling | Item 6 | trace catches; bandit |
| **S7** | Legacy paths | Item 7 | pyscn CFG dead code |
| **S8** | AI slop | Item 8 | manual review |

**Quick mode:** dispatch **S3, S4, S8** only.

## Per-subagent spawn prompt

Copy for each row (replace `{ID}`, `{NAME}`, `{MISSION}`):

```text
You are structural subagent {ID} — {NAME}.

Mission (Civil Learning): {MISSION}

Do detailed research on your task, write a critical assessment of the current code
and recommendations, and then implement all high confidence recommendations.

(Findings-only — no commits — if this is code-review or evaluate without implement permission.)

Before you start:
- Read templates/structural-quality-probes.md and .structural-probes.json (if present).
- Respect review target scope: {{TARGET}} / diff paths / plan referenced files.

When done, append one object to .structural-eight-agents.json → agents[]:
{
  "id": "{ID}",
  "name": "{NAME}",
  "assessment": "...",
  "recommendations": ["..."],
  "findings": [{"severity": "warning|critical|suggestion", "title": "...", "detail": "...", "probe_ids": []}],
  "implemented": ["..."] 
}
```

## Sidecar schema (`.structural-eight-agents.json`)

```json
{
  "generated_at": "ISO-8601",
  "master_prompt": "Civil Learning (see template)",
  "agents": [
    {
      "id": "S3",
      "name": "Dead code",
      "assessment": "...",
      "recommendations": [],
      "findings": [],
      "implemented": []
    }
  ]
}
```

## After the eight agents

1. Merge structural findings into the main review list (IDs `SF1`, `SF2`, … with `source: structural:S3`).
2. Dispatch the **core Forge team** (Architect, Security, QA, Critic, Investigator, Doc-writer) for Pass A + holistic Pass B — they may reference the eight-agent sidecar instead of re-running the same lenses.

## Related

- `templates/structural-quality-probes.md` — knip / madge / pyscn commands and triage
- `templates/codex-runtime.md` — spawn / close pattern
