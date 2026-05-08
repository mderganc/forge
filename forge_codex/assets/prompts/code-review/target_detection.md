# Phase 1: Target Detection

You are starting a code review. First, identify what will be reviewed.

## Current Target

**Target argument:** {{TARGET}}
**Detected mode:** {{MODE}} ({{MODE_DISPLAY}})

{{HANDOFF_CONTENT}}

## Your Task

1. **Identify the review target:**
   - If a PR number was given, verify it exists with `gh pr view <number>`
   - If a branch was given, verify it exists and check its diff against main
   - If file paths were given, verify they exist
   - If a handoff from implement exists, extract the changed files list
   - If nothing was provided, check git for uncommitted changes or recent commits

2. **Gather context:**
   - Read `.codex/forge-codex/memory/project.md` if it exists for project context
   - Check for recent handoff files to understand flow position
   - Note the scope: how many files, how many lines changed

3. **Confirm with user:**
   - Present the detected target and mode
   - Ask if they want to adjust the mode or target
   - If quick mode: note that only lead reviewers (Architect, QA) will participate

Record the confirmed target in the state and proceed to mode selection.
