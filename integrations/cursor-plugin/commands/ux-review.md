---
name: forge:ux-review
description: Real-browser product UX audit: map IA/journeys, walk pages and controls, prioritized findings report.
---

## Hard rule — what the user sees

**Never show terminal commands** for this workflow.

**Never edit the repository** unless the phase allows it. Follow the active skill's orchestrator output for what may be written.


## Graphify

Runs at **ship** only (`forge ship --step 1`). This workflow does not print GRAPHIFY per step.


## What to tell the user first

- **UX review** is a real-browser **product UX audit** (every page/control/state), not automated test execution or mock-flow authoring.
- Pass `--base-url` when known; capture screenshots and keep the coverage checklist live.

## What you run (agent)

Run **ux-review** at step one. Orient → plan → walkthrough → states → findings → report. Prefer cursor-ide-browser MCP. Do not fix product code unless asked.
