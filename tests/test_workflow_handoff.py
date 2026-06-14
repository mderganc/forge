"""Tests for workflow invocation tokens and handoff multiselect."""

from __future__ import annotations

import pytest

from scripts.shared.handoff_menu import (
    build_handoff_multiselect_payload,
    format_handoff_menu_lines,
)
from scripts.shared.orchestrator import build_skill_handoff_menu
from scripts.shared.workflow_tokens import (
    chain_command_to_agent_invocation,
    workflow_invocation_prefix,
)


def test_workflow_prefix_dollar_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FORGE_WORKFLOW_INVOCATION", raising=False)
    monkeypatch.delenv("CURSOR_AGENT", raising=False)
    monkeypatch.chdir("/")
    assert workflow_invocation_prefix() == "$forge:"


def test_workflow_prefix_slash_when_forced(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FORGE_WORKFLOW_INVOCATION", "slash")
    assert workflow_invocation_prefix() == "/forge:"
    assert chain_command_to_agent_invocation("implement") == "/forge:implement"
    assert chain_command_to_agent_invocation("evaluate --mode pre") == (
        "/forge:evaluate --mode pre"
    )


def test_handoff_menu_includes_multiselect_block(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FORGE_WORKFLOW_INVOCATION", "slash")
    menu = build_skill_handoff_menu("evaluate")
    assert "handoff-multiselect" in menu
    assert "/forge:implement" in menu
    assert "AskQuestion" in menu
    assert "allow_multiple: true" in menu


def test_handoff_multiselect_payload_has_stop_and_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FORGE_WORKFLOW_INVOCATION", "slash")
    payload = build_handoff_multiselect_payload(
        "evaluate",
        default_cmd="implement",
        alternatives=["plan"],
        state_path="/tmp/state.json",
    )
    assert payload["allow_multiple"] is True
    assert payload["default_option_ids"] == ["implement"]
    ids = [o["id"] for o in payload["options"]]
    assert ids == ["implement", "plan", "stop"]
    assert payload["state_file"] == "/tmp/state.json"


def test_handoff_multiselect_slug_ids_for_spaced_commands(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FORGE_WORKFLOW_INVOCATION", "slash")
    payload = build_handoff_multiselect_payload(
        "code-review",
        default_cmd="test",
        alternatives=["ship"],
    )
    assert payload["default_option_ids"] == ["test"]
    assert payload["options"][0]["chain_cmd"] == "test"


def test_build_next_command_respects_workflow_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    from pathlib import Path

    from scripts.shared.orchestrator import build_next_command

    monkeypatch.setenv("FORGE_WORKFLOW_INVOCATION", "slash")
    cmd = build_next_command(Path("scripts/plan/plan.py"), 1, 7)
    assert cmd == "/forge:plan --step 2"

    monkeypatch.setenv("FORGE_WORKFLOW_INVOCATION", "dollar")
    cmd = build_next_command(Path("scripts/plan/plan.py"), 1, 7)
    assert cmd == "$forge:plan --step 2"


def test_handoff_menu_lines_slash_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FORGE_WORKFLOW_INVOCATION", "slash")
    lines = format_handoff_menu_lines(
        "plan",
        default_cmd="evaluate --mode pre",
        alternatives=["implement"],
    )
    text = "\n".join(lines)
    assert "/forge:evaluate --mode pre" in text
    assert "/forge:implement" in text
