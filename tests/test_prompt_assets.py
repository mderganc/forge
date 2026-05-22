"""Packaged prompt parity and load_template resolution for pip installs."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def add_repo_to_path():
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))


def test_all_repo_prompts_mirrored_in_packaged_assets():
    src_root = REPO_ROOT / "prompts"
    packaged_root = REPO_ROOT / "forge_next" / "assets" / "prompts"
    drift: list[str] = []
    for path in sorted(src_root.rglob("*.md")):
        rel = path.relative_to(src_root)
        packaged = packaged_root / rel
        if not packaged.is_file():
            drift.append(f"missing in assets: {rel}")
            continue
        if path.read_text(encoding="utf-8") != packaged.read_text(encoding="utf-8"):
            drift.append(f"content drift: {rel}")
    assert not drift, "Prompt sync required:\n" + "\n".join(drift)


@pytest.mark.parametrize("name", ["plan/context", "review/team_dispatch", "pre/feasibility"])
def test_load_template_falls_back_to_packaged_when_checkout_file_missing(
    name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    from scripts.evaluate import template_engine as te

    stub_prompts = tmp_path / "prompts"
    (stub_prompts / name).parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(te, "PROMPTS_DIR", stub_prompts)
    monkeypatch.delenv("FORGE_CODEX_PROMPTS_DIR", raising=False)
    # Incomplete checkout: sentinels absent but directory exists.
    text = te.load_template(name)
    assert text.strip()


def test_validate_workflow_prompts_all_load():
    from scripts.evaluate.template_engine import (
        WORKFLOW_PROMPT_TEMPLATES,
        validate_workflow_prompts,
    )

    missing = validate_workflow_prompts()
    assert missing == [], (
        "Missing workflow templates:\n" + "\n".join(missing or WORKFLOW_PROMPT_TEMPLATES)
    )


def test_read_prompt_file_loads_technique_catalog():
    from scripts.evaluate.template_engine import read_prompt_file

    text = read_prompt_file("diagnose/technique_catalog.md")
    assert "| 1 |" in text or "| 1|" in text
