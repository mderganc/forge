# README command segmentation — implementation plan

**Status:** In progress (forge implement, 2026-06-10)  
**Extends:** `.codex/forge/memory/plans/20260608-1507-plan.md` Task 5

## Goal

Segment `README.md` **Commands in your apps** into per-command subsections (Sketch/Design format), isolate **ship**, **resume**, **status**, **doctor**, and **graphify** in separate invoke tables, and finish **develop → design** in integration docs.

## Waves

1. README restructure + slim Pipeline overview section
2. integrations/sketch.md, skills/status, claude/codex READMEs
3. tests: `test_readme_commands.py`, `test_docs_design_naming.py`
