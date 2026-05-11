---
name: forge:resume
description: Continue or clean up saved Forge workflow state.
---

## Hard rule — what the user sees

**Never show terminal commands** for this workflow.

## What to tell the user first

- **Resume** surfaces in-progress work, **continuity context** (last snapshot of skill steps), **memory narrative** (recent actions / next steps from `memory/`), and **Graphify** codebase index status when configured.
- If **JSON state** and the **continuity snapshot** disagree, resume asks the user to choose **state-based** vs **snapshot-based** continuation before auto-running anything.
- With **multiple active sessions**, the session menu is authoritative; memory and snapshot are **annotation only**.
- **Cleanup** options remove stale state files only when the user explicitly wants deletion.

## What you run (agent)

Invoke **resume** through the launcher from the repo root; use cleanup options only when they explicitly want deletion. Translate output into what’s active, what the continuity/memory/Graphify sections mean, and what was cleared—never paste launcher lines.

---
