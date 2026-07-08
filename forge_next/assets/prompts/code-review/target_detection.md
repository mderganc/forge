# Phase 1: Target Detection

You are starting a code review. First, identify what will be reviewed and pin the comparison baseline.

## Current Target

**Target argument:** {{TARGET}}
**Detected mode:** {{MODE}} ({{MODE_DISPLAY}})

{{PLAN_LINK_SECTION}}

{{HANDOFF_CONTENT}}

{{NATIVE_PLAN_HINTS}}

## Your Task

### 1. Pin the fixed point

Whatever the user supplied as the comparison baseline — commit SHA, branch name, tag, `main`, `HEAD~5`, PR base, etc. If nothing was provided, infer from target (e.g. `main` for a feature branch) or ask.

1. Resolve the ref: `git rev-parse <ref>`
2. Capture the diff command once: `git diff <ref>...HEAD` (three-dot, merge-base comparison)
3. List commits: `git log <ref>..HEAD --oneline`
4. **Fail fast** if the ref is invalid or the diff is empty — do not proceed to parallel review on a bad ref or empty diff

Record `fixed_point`, `diff_command`, and commit list in `{{MEMORY_DIR}}/project.md` (or session notes).

### 2. Identify the review target

- If a PR number was given, verify it exists with `gh pr view <number>` and note its base branch for the fixed point
- If a branch was given, verify it exists and use its merge-base diff against the fixed point
- If file paths were given, verify they exist
- If a handoff from implement exists, extract the changed files list
- If nothing was provided, check git for uncommitted changes or recent commits

### 3. Identify spec source (Pass A)

Resolve the originating spec in this order:

1. Issue references in commit messages (`#123`, `Closes #45`, GitLab `!67`, etc.) — fetch via issue tracker workflow if `docs/agents/issue-tracker.md` exists
2. `--plan` / `{{PLAN_PATH}}` (orchestrator may have resolved this already)
3. `docs/forge/specs/*-design.md`, `handoff-sketch.md`, implement handoff content
4. Branch/feature-named files under `docs/`, `specs/`, or `.scratch/`
5. Ask the user where the spec is; if none, Pass A will report "no spec available"

Record `spec_source` path or URL in session memory.

### 4. Identify standards sources (Pass B)

Scan the repo for documented coding standards, e.g.:

- `CODING_STANDARDS.md`, `CONTRIBUTING.md`, `AGENTS.md`
- `.cursor/rules/`, `CLAUDE.md`, linter config docs

Always include **`templates/standards-review-baseline.md`** as the fixed smell baseline (repo standards override baseline per that file).

Record `standards_sources` list in session memory.

### 5. Gather context

- Read `{{MEMORY_DIR}}/project.md` if it exists for project context
- Check for recent handoff files to understand flow position
- Note the scope: how many files, how many lines changed

### 6. Confirm with user

- Present the detected target, fixed point, diff command, spec source, and standards sources
- Present the detected mode
- Ask if they want to adjust the mode, target, or fixed point
- If quick mode: note that only lead reviewers (Architect, QA) will participate

Record the confirmed target in the state and proceed to mode selection.
