# Phase 6: Write Evaluation Report

You are writing the final evaluation report.

## Evaluation Details

**Plan:** {{PLAN_PATH}}
**Mode:** {{MODE}}
**Plan Name:** {{PLAN_NAME}}

## All Findings (including user feedback from discussion)

{{PREVIOUS_FINDINGS}}

## Your Task

Write the evaluation report as a markdown file. Save it to the appropriate location:

- If the plan path contains `docs/plans/` → save to `docs/evaluations/{{PLAN_NAME}}-evaluation.md`
- Otherwise → save alongside the plan as `[plan-directory]/{{PLAN_NAME}}-evaluation.md`

## Report Structure

Use this exact structure:

---
title: "Evaluation: [Plan Title from frontmatter or first heading]"
plan: {{PLAN_PATH}}
mode: {{MODE}}
date: [today's date in YYYY-MM-DD]
---

# Evaluation: [Plan Title]

## Summary
[2-3 sentence overview: what was evaluated, overall assessment, key concern count]

## Findings

### Critical
[List each critical finding that was NOT dismissed. Include ID, title, and detail.]

### Warnings
[List each warning finding that was NOT dismissed.]

### Suggestions
[List each suggestion that was NOT dismissed.]

## Dismissed Items
[Items dismissed during discussion, with the user's stated reason for each.
This section provides an audit trail.]

## Conclusion
[Overall assessment: Is the plan ready for implementation (pre mode)? Was the
implementation successful (post mode)? What are the recommended next steps?]

After writing the report, delete the `.evaluate-state.json` file.
Tell the user where the report was saved.
