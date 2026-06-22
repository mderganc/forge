"""User-facing docs must say design, not develop (except legacy/deprecated callouts)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

ALLOWLIST = re.compile(
    r"legacy|deprecated|develop-scope|handoff-develop|prompts/develop|"
    r"developer_instructions|/develop\b|forge develop|Local install \(development\)",
    re.I,
)

SCAN_PATHS = [
    REPO_ROOT / "integrations" / "claude" / "commands",
    REPO_ROOT / "integrations" / "cursor-plugin" / "commands",
    REPO_ROOT / "skills" / "status" / "SKILL.md",
]


@pytest.mark.parametrize("path", [p for p in SCAN_PATHS if p.exists()])
def test_user_facing_paths_use_design_not_develop(path: Path):
    files = [path] if path.is_file() else sorted(path.glob("*.md"))
    violations: list[str] = []
    for f in files:
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if not re.search(r"\bdevelop\b", line, re.I):
                continue
            if ALLOWLIST.search(line):
                continue
            violations.append(f"{f.relative_to(REPO_ROOT)}:{i}: {line.strip()}")
    assert not violations, "Unqualified develop references:\n" + "\n".join(violations)


def test_readme_utility_commands_have_own_tables():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    for heading in ("### Takeover", "### Status", "### Doctor", "### Ship", "### Graphify"):
        assert heading in readme, f"README missing {heading}"
    assert "### Core commands" not in readme
    assert "### Helper commands" not in readme
