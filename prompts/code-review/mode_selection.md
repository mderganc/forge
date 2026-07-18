# Phase 2: Mode Selection

Confirm and configure the review mode for this code review session.

## Detected Configuration

**Mode:** {{MODE}} ({{MODE_DISPLAY}})
**Target:** {{TARGET}}
**Quick mode:** {{QUICK_MODE}}
**Effort:** {{EFFORT}}
**Structural probes:** {{STRUCTURAL_ENABLED}}

{{EFFORT_CONFIG_SECTION}}

## Mode Details

### PR Mode (`pr`)
Best for reviewing a specific PR or set of changes against a base branch.
- Fetch the full diff (use pinned `diff_command` from step 1)
- All reviewers analyze the diff from their perspective
- Focus: correctness, style, test coverage, security

### Deep Mode (`deep`)
Best for troubleshooting reviews or investigating specific problem areas.
- Trace code paths related to the issue
- Focus on call chains, data flow, error handling
- Security Reviewer traces auth and data boundaries
- Investigator follows dependency chains

### Architecture Mode (`architecture`)
Best for reviewing design decisions, structural patterns, and system health.
- Check SOLID principles adherence
- Analyze coupling and cohesion metrics
- Review dependency direction and layering
- Evaluate extensibility and maintainability

## Two-axis review framework (Pass A / Pass B)

Aligned with [mattpocock/skills code-review](https://github.com/mattpocock/skills/blob/main/skills/engineering/code-review/SKILL.md). Use **both** passes for every finding; tag each issue with its pass. **Do not merge or rerank findings across axes.**

| Pass | Axis | Question | Typical lenses |
|------|------|----------|----------------|
| **Pass A** | **Spec** | Does the change do **what was agreed** (plan, ticket, design, stated user-visible behavior)? | Completeness vs requirements, wrong behavior, missing cases, scope creep, mismatched API or UX promises |
| **Pass B** | **Standards** | Is the solution **sound, safe, and maintainable** even if it "works"? | Repo standards, smell baseline (`templates/standards-review-baseline.md`), security, tests, coupling, structural probes |

Pass A issues often block "done"; Pass B issues may be warnings or follow-ups depending on severity.

### Why two axes

A change can pass one axis and fail the other:

- Code that follows every standard but implements the wrong thing → **Standards pass, Spec fail.**
- Code that does exactly what the issue asked but breaks project conventions → **Spec pass, Standards fail.**

Reporting them separately stops one axis from masking the other.

## Your Task

1. **Confirm the mode** with the user (or auto-confirm if the mode is obvious)
2. **Prepare mode-specific instructions** for each team member:

{{TEAM_ASSIGNMENTS}}

3. **Set the review scope:**
   - For PR mode: use the pinned diff from step 1
   - For deep mode: identify the code paths to trace
   - For architecture mode: identify the modules/packages to analyze

4. Record the finalized mode and scope, then proceed to team dispatch.

## Structural probes (Pass B)

At team dispatch (step 3), the orchestrator **runs** structural probes (**pyscn** when Python is present) and writes **`.structural-probes.json`**. Read that sidecar before reviewers; planning-only mode: `FORGE_STRUCTURAL_PROBES_MANUAL=1`. See `templates/structural-quality-probes.md`.
