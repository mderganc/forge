#!/usr/bin/env python3
"""Cursor hook: remind to close unused sub-agents before tool calls.

Usage (``.cursor/hooks.json`` in a repo, or via ``forge cursor-subagent-hooks``):

  forge cursor-subagent-hook preToolUse
  forge cursor-subagent-hook subagentStart
  forge cursor-subagent-hook subagentStop
  forge cursor-subagent-hook postToolUse

Reads hook JSON from stdin; prints hook JSON to stdout when applicable.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from forge_next.hooks.subagent_lifecycle import (
    default_state_path,
    lifecycle_reminder_message,
    record_subagent_start,
    record_subagent_stop,
    record_task_post_tool,
)


def _cwd(data: dict) -> Path:
    for key in ("cwd", "working_directory", "workspace_root", "workspaceRoot"):
        val = data.get(key)
        if val:
            return Path(str(val)).resolve()
    return Path.cwd().resolve()


def _emit_pre_tool_use(message: str) -> None:
    print(
        json.dumps(
            {
                "agent_message": message,
            },
            ensure_ascii=True,
        )
    )


def handle_pre_tool_use(data: dict) -> None:
    cwd = _cwd(data)
    state_path = default_state_path(cwd)
    message = lifecycle_reminder_message(data, state_path=state_path)
    if message:
        _emit_pre_tool_use(message)


def handle_subagent_start(data: dict) -> None:
    record_subagent_start(data, state_path=default_state_path(_cwd(data)))


def handle_subagent_stop(data: dict) -> None:
    record_subagent_stop(data, state_path=default_state_path(_cwd(data)))


def handle_post_tool_use(data: dict) -> None:
    record_task_post_tool(data, state_path=default_state_path(_cwd(data)))


def main(argv: list[str] | None = None) -> int:
    event = (argv or sys.argv[1:2] or ["preToolUse"])[0]
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        data = {}

    if event == "preToolUse":
        handle_pre_tool_use(data)
    elif event == "subagentStart":
        handle_subagent_start(data)
    elif event == "subagentStop":
        handle_subagent_stop(data)
    elif event == "postToolUse":
        handle_post_tool_use(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
