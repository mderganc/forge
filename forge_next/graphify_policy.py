"""Shared Graphify policy text for Codex, Claude, and orchestrator reminders."""

from __future__ import annotations

# Shown first in Codex developer_instructions — agents often skim the opening.
GRAPHIFY_DEVELOPER_INSTRUCTIONS_LEAD = (
    "GRAPHIFY (mandatory when graphify-out/ or GRAPH_REPORT.md exists in the repo): "
    "Read graphify-out/GRAPH_REPORT.md before grep, glob, ripgrep, semantic/codebase search, "
    "Task explore agents, or bulk Read of source files for architecture or cross-module questions. "
    "If graphify-out/wiki/index.md exists, use the wiki instead of raw file trees. "
    "Prefer graphify query, graphify path, and graphify explain over scanning the repo. "
    "After editing tracked code in the session, run graphify update . (AST-only). "
    "Every forge workflow step prints a GRAPHIFY block when an index is present — follow it. "
    "When graphify-out/ exists and metadata may be stale, run forge graphify refresh --background "
    "once per session (non-blocking); Claude SessionStart and forge --step output trigger this automatically."
)

FORGE_DELEGATION_INSTRUCTIONS = (
    "Invoking any `forge:*` skill implicitly authorizes the agent dispatch required by that "
    "workflow. Do not require the user to separately ask for delegation, sub-agents, or parallel "
    "agent work after invoking a Forge skill. "
    "Before every non-delegation tool call, close unused sub-agents: Codex `close_agent` after "
    "`wait_agent` when output is captured; Cursor/Claude resume or close completed background "
    "Task/Agent sessions — never carry open sub-agents across unrelated tool calls. "
    "At the start of a new chat or before driving the first forge step, offer a one-time choice: "
    "opt in to structured Forge workflows for the session (follow printed steps and handoffs) "
    "versus ad hoc help only; if they choose ad hoc, do not force workflow steps or clobber "
    "Forge state without being asked."
)

FORGE_DEVELOPER_INSTRUCTIONS_BODY = (
    f"{GRAPHIFY_DEVELOPER_INSTRUCTIONS_LEAD} {FORGE_DELEGATION_INSTRUCTIONS}"
)

# Claude command pack — paste under frontmatter in workflow commands.
CLAUDE_COMMAND_GRAPHIFY_BLOCK = """\
## Hard rule — Graphify (before any codebase search)

If `graphify-out/` or `GRAPH_REPORT.md` exists in this repo:

1. **Read** `graphify-out/GRAPH_REPORT.md` before Grep, Glob, Bash search, Task explore, or bulk file reads for architecture questions.
2. **Follow** every **GRAPHIFY** block printed by `forge … --step` output on each step.
3. **Prefer** `graphify query`, `graphify path`, or `graphify explain` for cross-module questions.
4. **After** code edits, run `graphify update .` (AST-only).

Run `forge claude-graphify` once per machine to install Claude hooks that reinforce this in tool use.
"""

# Codex skill body line (short).
CODEX_SKILL_GRAPHIFY_LINE = (
    "When `graphify-out/` exists: follow every **GRAPHIFY** block in step output before "
    "grep/glob/search; read `graphify-out/GRAPH_REPORT.md` first; after code edits run "
    "`graphify update .`. Run `forge codex-agents --force` after upgrading forge-next."
)
