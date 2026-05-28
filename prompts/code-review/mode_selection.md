# Phase 2: Mode Selection

Confirm and configure the review mode for this code review session.

## Detected Configuration

**Mode:** {{MODE}} ({{MODE_DISPLAY}})
**Target:** {{TARGET}}
**Quick mode:** {{QUICK_MODE}}

## Mode Details

### PR Mode (`pr`)
Best for reviewing a specific PR or set of changes against a base branch.
- Fetch the full diff
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

## Two-pass review framework (Pass A / Pass B)

Use **both** passes for every finding; note which pass drives each issue (labels help the report and triage). Canonical definitions for later phases:

| Pass | Question | Typical lenses |
|------|-----------|----------------|
| **Pass A — Spec / intent** | Does the change do **what was agreed** (plan, ticket, design, stated user-visible behavior)? | Completeness vs requirements, wrong behavior, missing cases, mismatched API or UX promises |
| **Pass B — Engineering quality** | Is the solution **sound, safe, and maintainable** even if it “works”? | Security, tests, readability, coupling, observability, performance footguns, operational risk |

Pass A issues often block “done”; Pass B issues may be warnings or follow-ups depending on severity.

## Your Task

1. **Confirm the mode** with the user (or auto-confirm if the mode is obvious)
2. **Prepare mode-specific instructions** for each team member:

{{TEAM_ASSIGNMENTS}}

3. **Set the review scope:**
   - For PR mode: identify the exact commits/diff to review
   - For deep mode: identify the code paths to trace
   - For architecture mode: identify the modules/packages to analyze

4. Record the finalized mode and scope, then proceed to team dispatch.

## Structural probes (Pass B)

At team dispatch (step 3), the orchestrator may run **knip / madge / pyscn** and write **`.structural-probes.json`** next to the session state. Follow `templates/structural-quality-probes.md` and cite probe IDs in findings.
