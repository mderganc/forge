"""README command table includes every integrations/spec command id."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def spec_commands() -> dict:
    path = REPO_ROOT / "integrations" / "spec" / "commands.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_readme_lists_all_forge_command_ids(spec_commands: dict):
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    # Section between "## Commands in your apps" and next ## heading
    match = re.search(
        r"## Commands in your apps\s*\n(.*?)\n## ",
        readme,
        re.DOTALL,
    )
    assert match, "README missing '## Commands in your apps' section"
    section = match.group(1)
    missing: list[str] = []
    for cmd in spec_commands["commands"]:
        cmd_id = cmd["id"]  # e.g. forge:ship
        sub = cmd["cli_subcommand"]
        if cmd_id not in section and f"/forge:{sub}" not in section and f"$forge:{sub}" not in section:
            missing.append(cmd_id)
    assert not missing, f"README Commands section missing: {missing}"
