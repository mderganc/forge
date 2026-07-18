"""Shared template bundling for forge install integrations."""

from __future__ import annotations

import shutil
from pathlib import Path

BUNDLED_SKILL_TEMPLATE_FILES = (
    "plan-modes.md",
    "writing-plans.md",
    "structural-quality-probes.md",
    "diagnose-execution-playbooks.md",
    "ux-review-criteria.md",
    "ux-review-coverage-checklist.md",
    "ux-review-report.md",
    "workflow-skill-preamble.md",
)


def copy_skill_templates(repo_root: Path, templates_dst: Path) -> None:
    """Copy canonical workflow templates into an integration skills tree."""
    templates_src = repo_root / "templates"
    if not templates_src.is_dir():
        return
    templates_dst.mkdir(parents=True, exist_ok=True)
    for name in BUNDLED_SKILL_TEMPLATE_FILES:
        src_file = templates_src / name
        if src_file.is_file():
            shutil.copy2(src_file, templates_dst / name)
