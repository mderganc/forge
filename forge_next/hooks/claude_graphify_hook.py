#!/usr/bin/env python3
"""Claude Code hook: inject Graphify context when a knowledge graph exists.

Usage (written by ``forge claude-graphify`` into ~/.claude/settings.json):
  /path/to/forge claude-graphify-hook SessionStart
  /path/to/forge claude-graphify-hook PreToolUse

Reads hook JSON from stdin; prints hookSpecificOutput JSON to stdout when applicable.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from forge_next.hooks.subagent_lifecycle import lifecycle_reminder_message

_SESSION_MSG = (
    "graphify: This repo has a knowledge graph. Read graphify-out/GRAPH_REPORT.md before "
    "Grep/Glob/Bash search or bulk reads for architecture questions. After code edits run "
    "graphify update . Refresh the index at ship time (forge ship --step 1); workflow "
    "forge --step skills do not print per-step GRAPHIFY banners."
)

_PRE_TOOL_MSG = (
    "graphify STOP: Knowledge graph exists. Read graphify-out/GRAPH_REPORT.md (god nodes + "
    "communities) before searching raw files. Prefer graphify query/path/explain for "
    "cross-module questions."
)

_FORGE_PROMPT_MSG = (
    "graphify: Forge workflow starting — if graphify-out/ exists, read GRAPH_REPORT.md before "
    "codebase search tools. Graphify refresh runs at ship (forge ship), not on each workflow step."
)

_BASH_SEARCH = re.compile(
    r"(grep|rg |ripgrep|find |fd |ack |ag |SemanticSearch|codebase_search|glob )",
    re.I,
)

_FORGE_PROMPT = re.compile(r"(forge:|/forge:|\\$forge:)", re.I)


def _graph_present(cwd: Path) -> bool:
    return (cwd / "graphify-out" / "graph.json").is_file() or (
        cwd / "graphify-out" / "GRAPH_REPORT.md"
    ).is_file() or (cwd / "GRAPH_REPORT.md").is_file()


def _emit(event: str, message: str) -> None:
    payload = {
        "hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": message,
        }
    }
    print(json.dumps(payload, ensure_ascii=True))


def _tool_input(data: dict) -> dict:
    ti = data.get("tool_input")
    if isinstance(ti, dict):
        return ti
    return data if isinstance(data, dict) else {}


def _cwd(data: dict) -> Path:
    for key in ("cwd", "working_directory", "workspace_root"):
        val = data.get(key)
        if val:
            return Path(str(val)).resolve()
    return Path.cwd().resolve()


def _graphify_enforcement_off(cwd: Path) -> bool:
    try:
        from forge_next.graphify_enforcement import graphify_fully_disabled

        return graphify_fully_disabled(cwd)
    except Exception:
        return False


def handle_session_start(data: dict) -> None:
    cwd = _cwd(data)
    if _graphify_enforcement_off(cwd):
        return
    if _graph_present(cwd):
        _emit("SessionStart", _SESSION_MSG)
        if os.environ.get("FORGE_GRAPHIFY_SESSION_REFRESH", "").strip() in ("1", "true", "yes"):
            try:
                from forge_next.graphify import spawn_refresh_background

                spawn_refresh_background(cwd)
            except Exception:
                pass


def _graphify_pre_tool_message(data: dict, cwd: Path) -> str | None:
    if _graphify_enforcement_off(cwd) or not _graph_present(cwd):
        return None
    tool = str(data.get("tool_name") or data.get("tool") or "").strip()
    ti = _tool_input(data)
    if tool in ("Grep", "Glob"):
        return _PRE_TOOL_MSG
    if tool == "Bash":
        cmd = str(ti.get("command") or "")
        if _BASH_SEARCH.search(cmd):
            return _PRE_TOOL_MSG
        return None
    if tool == "Read":
        path = str(ti.get("file_path") or ti.get("path") or "")
        if path and "graphify-out" not in path.replace("\\", "/"):
            if any(path.endswith(ext) for ext in (".py", ".ts", ".tsx", ".js", ".go", ".rs", ".java", ".md")):
                return _PRE_TOOL_MSG
    return None


def handle_pre_tool_use(data: dict) -> None:
    cwd = _cwd(data)
    parts: list[str] = []
    lifecycle = lifecycle_reminder_message(data)
    if lifecycle:
        parts.append(lifecycle)
    graphify = _graphify_pre_tool_message(data, cwd)
    if graphify:
        parts.append(graphify)
    if parts:
        _emit("PreToolUse", " ".join(parts))


def handle_user_prompt_submit(data: dict) -> None:
    cwd = _cwd(data)
    if _graphify_enforcement_off(cwd) or not _graph_present(cwd):
        return
    prompt = str(data.get("prompt") or data.get("user_prompt") or "")
    if _FORGE_PROMPT.search(prompt):
        _emit("UserPromptSubmit", _FORGE_PROMPT_MSG)


def main(argv: list[str] | None = None) -> int:
    event = (argv or sys.argv[1:2] or ["SessionStart"])[0]
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        data = {}

    if event == "SessionStart":
        handle_session_start(data)
    elif event == "PreToolUse":
        handle_pre_tool_use(data)
    elif event == "UserPromptSubmit":
        handle_user_prompt_submit(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
