"""Tests for workflow step prompt sidecar."""

from __future__ import annotations

from pathlib import Path

from scripts.shared.workflow_prompt_archive import (
    format_workflow_prompts_markdown,
    load_archive,
    record_step_prompt,
    sidecar_path,
)


def test_record_and_format_full_prompts(tmp_path: Path) -> None:
    record_step_prompt(
        tmp_path,
        skill="test",
        step=1,
        phase_name="Context",
        body="Step one body",
        template_name="test/context",
    )
    record_step_prompt(
        tmp_path,
        skill="test",
        step=3,
        phase_name="Execution",
        body="Step three body",
        template_name="test/execution",
    )

    path = sidecar_path(tmp_path)
    assert path is not None
    assert path.is_file()

    archive = load_archive(tmp_path)
    assert archive["skill"] == "test"
    assert len(archive["steps"]) == 2

    brief = format_workflow_prompts_markdown(tmp_path, style="brief")
    assert "| 1 |" in brief
    assert "test/context" in brief
    assert "Step one body" not in brief

    full = format_workflow_prompts_markdown(tmp_path, style="full")
    assert "Step one body" in full
    assert "Step three body" in full
    assert "### Step 3" in full


def test_record_replaces_same_step(tmp_path: Path) -> None:
    record_step_prompt(
        tmp_path,
        skill="test",
        step=2,
        phase_name="Discovery",
        body="first",
        template_name="test/discovery",
    )
    record_step_prompt(
        tmp_path,
        skill="test",
        step=2,
        phase_name="Discovery",
        body="second",
        template_name="test/discovery",
    )
    archive = load_archive(tmp_path)
    bodies = [s["body"] for s in archive["steps"] if s["step"] == 2]
    assert bodies == ["second"]
