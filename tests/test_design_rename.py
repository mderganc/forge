"""User-facing develop → design rename (CLI, spec, aliases)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def spec_commands() -> dict:
    path = REPO_ROOT / "integrations" / "spec" / "commands.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_commands_json_uses_forge_design(spec_commands: dict) -> None:
    ids = {c["id"] for c in spec_commands["commands"]}
    subs = {c["cli_subcommand"] for c in spec_commands["commands"]}
    assert "forge:design" in ids
    assert "design" in subs
    assert "forge:develop" not in ids


def test_cli_dispatch_registers_design_and_develop_alias() -> None:
    from forge_next import cli_dispatch

    assert "design" in cli_dispatch._WORKFLOW_MODULES
    assert "develop" in cli_dispatch._WORKFLOW_MODULES
    assert (
        cli_dispatch._WORKFLOW_MODULES["design"]
        == cli_dispatch._WORKFLOW_MODULES["develop"]
    )


def test_develop_script_skill_name_is_design() -> None:
    from scripts.develop import develop as mod

    assert mod.SKILL_NAME == "design"
