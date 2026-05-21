import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


def test_commands_json_has_no_studio_command() -> None:
    spec = json.loads((REPO / "integrations" / "spec" / "commands.json").read_text(encoding="utf-8"))
    ids = [c.get("id", "") for c in spec.get("commands", [])]
    subs = [c.get("cli_subcommand", "") for c in spec.get("commands", [])]
    assert not any("studio" in str(x).lower() for x in ids + subs)


def test_readme_workflows_no_studio_section() -> None:
    readme = (REPO / "README.md").read_text(encoding="utf-8").lower()
    assert "forge studio" not in readme
    assert "## studio" not in readme
