"""Canonical Forge agent roster is documented and referenced from dispatch prompts."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_forge_agent_roster_template_exists():
    paths = [
        REPO_ROOT / "templates" / "forge-agent-roster.md",
        REPO_ROOT / "forge_next" / "assets" / "templates" / "forge-agent-roster.md",
    ]
    for path in paths:
        assert path.is_file(), path
        text = path.read_text(encoding="utf-8")
        assert "backend-architect" in text
        assert "agents/architect.md" in text


def test_design_dispatch_prompts_reference_roster():
    for rel in (
        "prompts/design/investigation.md",
        "prompts/design/solution.md",
        "prompts/design/scope.md",
        "templates/workflow-skill-preamble.md",
    ):
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        assert "forge-agent-roster.md" in text, rel
        assert "backend-architect" in text, rel


def test_sketch_skills_forbid_agent_dispatch():
    for rel in (
        "skills/sketch/SKILL.md",
        "integrations/cursor-plugin/commands/sketch.md",
        "integrations/codex/skills/forge-sketch/SKILL.md",
    ):
        text = (REPO_ROOT / rel).read_text(encoding="utf-8").lower()
        assert "no agent" in text or "dialogue only" in text or "1:1" in text, rel
