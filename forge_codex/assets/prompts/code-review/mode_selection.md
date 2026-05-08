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

## Your Task

1. **Confirm the mode** with the user (or auto-confirm if the mode is obvious)
2. **Prepare mode-specific instructions** for each team member:

{{TEAM_ASSIGNMENTS}}

3. **Set the review scope:**
   - For PR mode: identify the exact commits/diff to review
   - For deep mode: identify the code paths to trace
   - For architecture mode: identify the modules/packages to analyze

4. Record the finalized mode and scope, then proceed to team dispatch.
