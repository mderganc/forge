"""User-facing docs must not claim per-step orchestrator GRAPHIFY banners."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# Files checked for stale Graphify orchestrator claims
def _doc_paths() -> list[Path]:
    paths = [
        REPO_ROOT / "README.md",
        REPO_ROOT / "integrations" / "README.md",
    ]
    for sub in ("cursor-plugin/commands", "claude/commands"):
        cmd_dir = REPO_ROOT / "integrations" / sub
        if cmd_dir.is_dir():
            paths.extend(sorted(cmd_dir.glob("*.md")))
    graphify_skill = (
        REPO_ROOT / "integrations" / "codex" / "skills" / "forge-graphify" / "SKILL.md"
    )
    if graphify_skill.is_file():
        paths.append(graphify_skill)
    return paths


DOC_PATHS = _doc_paths()

# Phrases that imply workflow --step prints GRAPHIFY (ship-only since 0.14.11)
STALE_PATTERNS = [
    re.compile(r"prints a \*\*GRAPHIFY\*\* block every step", re.I),
    re.compile(r"Every `forge <skill> --step", re.I),
    re.compile(r"per-step \*\*GRAPHIFY\*\* banner", re.I),
    re.compile(r"follow \*\*GRAPHIFY\*\* blocks in every `forge --step`", re.I),
    re.compile(r"orchestrator steps print a \*\*GRAPHIFY\*\* block when an index", re.I),
]


@pytest.mark.parametrize("path", DOC_PATHS, ids=lambda p: p.name)
def test_no_stale_per_step_graphify_claims(path: Path):
    text = path.read_text(encoding="utf-8")
    hits: list[str] = []
    for pattern in STALE_PATTERNS:
        if pattern.search(text):
            hits.append(pattern.pattern)
    assert not hits, f"{path.relative_to(REPO_ROOT)}: stale Graphify claims matched {hits}"
