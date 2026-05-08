# Phase 4: Codebase Alignment (Pre-Implementation)

You are checking whether the plan is consistent with the existing codebase.

## Plan Summary

**Path:** {{PLAN_PATH}}
**Referenced Files:** {{REFERENCED_FILES}}

## Previous Findings

{{PREVIOUS_FINDINGS}}

## Your Task

Read the existing code and check:

1. **Pattern consistency:** Does the plan follow the conventions already in the codebase? Naming patterns, file organization, error handling style, test structure?
2. **Architecture fit:** Does the plan work with the existing architecture or fight against it? Would the changes create inconsistencies in how the system is structured?
3. **Interface compatibility:** Do the proposed changes match existing function signatures, data models, and API contracts? Will callers of modified code still work?
4. **Duplication risk:** Does the plan propose creating something that already exists in a different form? Is there existing code that does part of what the plan describes?

Use Grep and Glob to search the codebase for relevant patterns. Read existing files to understand conventions.

For each conflict found, create a finding explaining what the plan proposes vs. what the codebase already does, and suggest how to reconcile them.

## Findings Output

Write your findings to `{{FINDINGS_SIDECAR}}` as a JSON array using the `Write` tool:

```json
[
  {"phase": "codebase_alignment", "severity": "critical|warning|suggestion", "title": "...", "detail": "..."}
]
```

Write `[]` if no conflicts.
