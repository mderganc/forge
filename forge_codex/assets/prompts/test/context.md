# Phase 1: Context Detection

You are starting a test execution and analysis workflow. First, identify what will be tested.

## Current Target

**Target argument:** {{TARGET}}

{{HANDOFF_CONTENT}}

## Team

{{TEAM_ASSIGNMENTS}}

## Your Task

1. **Identify the test context:**
   - If a test command/path was given, verify it exists
   - If a handoff from code-review exists, extract files to focus testing on
   - If a handoff from implement exists, extract changed files
   - Read `.codex/forge-codex/memory/project.md` for project scope and task type
   - If nothing was provided, discover test infrastructure in the project

2. **Gather test infrastructure information:**
   - What test framework(s) are used? (pytest, jest, go test, etc.)
   - Where are tests located? (tests/, __tests__/, *_test.go, etc.)
   - Is there a coverage tool configured? (coverage.py, istanbul, etc.)
   - Is there a test runner configuration? (pytest.ini, jest.config, etc.)
   - What CI configuration exists? (.github/workflows, Makefile, etc.)

3. **Determine scope:**
   - Full test suite or targeted tests?
   - If handoff mentions specific findings, target tests for those areas
   - Note any tests that were flagged as missing during code review

Record the test context and proceed to test discovery.
