"""skills/*/SKILL.md must not use legacy forge-codex paths without a legacy qualifier."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

# Allow forge-codex only when the same line (or previous line) marks it as legacy
LEGACY_NEARBY = re.compile(r"legacy", re.I)
FORGE_CODEX = re.compile(r"forge-codex")


@pytest.mark.parametrize(
    "skill_md",
    sorted(SKILLS_DIR.glob("**/SKILL.md")),
    ids=lambda p: str(p.relative_to(SKILLS_DIR)),
)
def test_skills_forge_codex_paths_qualified(skill_md: Path):
    lines = skill_md.read_text(encoding="utf-8").splitlines()
    violations: list[str] = []
    for i, line in enumerate(lines):
        if not FORGE_CODEX.search(line):
            continue
        context = "\n".join(lines[max(0, i - 1) : i + 2])
        if not LEGACY_NEARBY.search(context):
            violations.append(f"L{i + 1}: {line.strip()}")
    assert not violations, (
        f"{skill_md.relative_to(REPO_ROOT)}: unqualified forge-codex references:\n"
        + "\n".join(violations)
    )
