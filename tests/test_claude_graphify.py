from __future__ import annotations

import json
from pathlib import Path

import pytest

from forge_next.claude_graphify import (
    HOOK_MARKER,
    apply_claude_graphify_settings,
    merge_graphify_hooks,
)
from forge_next.graphify_policy import (
    FORGE_DEVELOPER_INSTRUCTIONS_BODY,
    GRAPHIFY_DEVELOPER_INSTRUCTIONS_LEAD,
)
from forge_next.hooks import claude_graphify_hook as hook


def test_merge_graphify_hooks_adds_managed_entries() -> None:
    settings = merge_graphify_hooks({})
    hooks = settings["hooks"]
    assert "SessionStart" in hooks
    assert "PreToolUse" in hooks
    assert "UserPromptSubmit" in hooks
    assert any(HOOK_MARKER in str(h) for h in hooks["PreToolUse"])


def test_apply_claude_graphify_settings_writes_file(tmp_path: Path) -> None:
    cfg = tmp_path / "settings.json"
    assert apply_claude_graphify_settings(cfg) == 0
    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert HOOK_MARKER in json.dumps(data)


def test_codex_body_leads_with_graphify() -> None:
    assert FORGE_DEVELOPER_INSTRUCTIONS_BODY.startswith(GRAPHIFY_DEVELOPER_INSTRUCTIONS_LEAD[:40])


def test_pre_tool_use_grep_emits_context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = Path(__file__).resolve().parents[1]
    if not (repo / "graphify-out" / "GRAPH_REPORT.md").is_file():
        pytest.skip("no graphify index in forge checkout")

    monkeypatch.setattr(hook, "_cwd", lambda _data: repo)
    payload = {
        "tool_name": "Grep",
        "tool_input": {"pattern": "foo"},
    }
    monkeypatch.setattr("sys.stdin", type("R", (), {"read": lambda self: json.dumps(payload)})())
    import io

    buf = io.StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    hook.main(["PreToolUse"])
    out = buf.getvalue()
    assert "graphify STOP" in out
    assert "GRAPH_REPORT" in out
