from __future__ import annotations

import json
from pathlib import Path

import pytest

from forge_next.hooks import cursor_subagent_hook as cursor_hook
from forge_next.hooks import subagent_lifecycle as lifecycle
from forge_next.hooks import claude_graphify_hook as claude_hook


def test_skip_close_and_wait_agent_tools() -> None:
    assert lifecycle.should_skip_lifecycle_reminder({"tool_name": "close_agent"})
    assert lifecycle.should_skip_lifecycle_reminder({"tool_name": "wait_agent"})
    assert not lifecycle.should_skip_lifecycle_reminder({"tool_name": "Grep"})


def test_skip_task_resume_and_interrupt() -> None:
    assert lifecycle.should_skip_lifecycle_reminder(
        {"tool_name": "Task", "tool_input": {"resume": "agent-1"}}
    )
    assert lifecycle.should_skip_lifecycle_reminder(
        {"tool_name": "Task", "tool_input": {"interrupt": True}}
    )
    assert not lifecycle.should_skip_lifecycle_reminder(
        {"tool_name": "Task", "tool_input": {"description": "explore"}}
    )


def test_lifecycle_suppressed_by_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FORGE_SKIP_SUBAGENT_LIFECYCLE", "1")
    assert lifecycle.lifecycle_suppressed()
    assert lifecycle.lifecycle_reminder_message({"tool_name": "Read"}) is None


def test_running_agents_add_progress_reminder(tmp_path: Path) -> None:
    state_path = tmp_path / ".cursor" / "forge-subagent-lifecycle.json"
    lifecycle.record_subagent_start({"agent_id": "a1"}, state_path=state_path)
    msg = lifecycle.lifecycle_reminder_message(
        {"tool_name": "Read"},
        state_path=state_path,
    )
    assert msg is not None
    assert "subagent-progress" in msg
    assert "Running: a1" in msg


def test_state_tracks_pending_close(tmp_path: Path) -> None:
    state_path = tmp_path / ".cursor" / "forge-subagent-lifecycle.json"
    lifecycle.record_subagent_start({"agent_id": "a1"}, state_path=state_path)
    lifecycle.record_subagent_stop({"agent_id": "a1"}, state_path=state_path)
    assert lifecycle.pending_close_ids(state_path) == ["a1"]
    lifecycle.record_task_post_tool(
        {"tool_name": "Task", "tool_input": {"resume": "a1"}},
        state_path=state_path,
    )
    assert lifecycle.pending_close_ids(state_path) == []


def test_cursor_pre_tool_use_emits_agent_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cursor_hook, "_cwd", lambda _data: tmp_path)
    monkeypatch.setattr(
        "sys.stdin",
        type("R", (), {"read": lambda self: json.dumps({"tool_name": "Read"})})(),
    )
    import io

    buf = io.StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    cursor_hook.main(["preToolUse"])
    out = json.loads(buf.getvalue())
    assert "close unused sub-agents" in out["agent_message"]


def test_claude_pre_tool_use_includes_lifecycle_on_any_tool(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(claude_hook, "_cwd", lambda _data: tmp_path)
    monkeypatch.setattr(claude_hook, "_graph_present", lambda _cwd: False)
    payload = {"tool_name": "Write", "tool_input": {"path": "foo.txt"}}
    monkeypatch.setattr(
        "sys.stdin",
        type("R", (), {"read": lambda self: json.dumps(payload)})(),
    )
    import io

    buf = io.StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    claude_hook.main(["PreToolUse"])
    out = json.loads(buf.getvalue())
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert "close unused sub-agents" in ctx
