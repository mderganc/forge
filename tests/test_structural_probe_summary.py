"""Tests for structural probe summary markdown formatter."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.shared import structural_probes as sp


def _sample_payload() -> dict:
    return {
        "selected_tools": ["pyscn", "skylos"],
        "probes": [
            {
                "tool": "knip",
                "status": "skip",
                "summary": "not selected",
                "findings": [],
            },
            {
                "tool": "pyscn",
                "status": "fail",
                "summary": "complexity",
                "findings": [
                    {
                        "id": "P2",
                        "severity": "warning",
                        "path": "forge_next/cli.py",
                        "detail": "main is too complex",
                    },
                    {
                        "id": "P3",
                        "severity": "warning",
                        "path": "scripts/foo.py",
                        "detail": "fn is too complex",
                    },
                ],
            },
            {
                "tool": "skylos",
                "status": "pass",
                "summary": "dead code",
                "findings": [
                    {
                        "id": "Y1",
                        "severity": "warning",
                        "path": "a.py",
                        "detail": "likely_dead",
                    },
                ],
            },
        ],
    }


def test_format_probe_summary_brief_lists_tools_and_top_findings() -> None:
    text = sp.format_probe_summary_markdown(payload=_sample_payload(), style="brief")
    assert "## Structural probes" in text
    assert "pyscn" in text
    assert "`P2`" in text
    assert "…and" not in text  # only 3 findings total


def test_format_probe_summary_full_includes_table() -> None:
    text = sp.format_probe_summary_markdown(payload=_sample_payload(), style="full")
    assert "| P2 |" in text
    assert "| Y1 |" in text


def test_load_probe_payload_from_file(tmp_path: Path) -> None:
    sidecar = tmp_path / sp.SIDECAR_NAME
    sidecar.write_text(json.dumps(_sample_payload()), encoding="utf-8")
    loaded = sp.load_probe_payload(sidecar)
    assert loaded is not None
    assert loaded["selected_tools"] == ["pyscn", "skylos"]


def test_format_probe_summary_missing_sidecar(tmp_path: Path) -> None:
    text = sp.format_probe_summary_markdown(sidecar=tmp_path / "missing.json")
    assert "not run" in text


def test_resolve_probe_summary_for_state_uses_custom_path(tmp_path: Path) -> None:
    sidecar = tmp_path / sp.SIDECAR_NAME
    sidecar.write_text(json.dumps(_sample_payload()), encoding="utf-8")
    custom = {"structural_probes_sidecar": str(sidecar)}
    text = sp.resolve_probe_summary_for_state(custom, tmp_path, style="brief")
    assert "`P2`" in text


def test_code_review_step6_variables_include_probe_summary(tmp_path: Path, monkeypatch) -> None:
    from scripts.code_review import code_review as cr
    from scripts.shared.orchestrator import SkillState

    sidecar = tmp_path / sp.SIDECAR_NAME
    sidecar.write_text(json.dumps(_sample_payload()), encoding="utf-8")
    state = SkillState(skill_name="code-review")
    state.custom["structural_probes_sidecar"] = str(sidecar)
    state_path = tmp_path / "code-review.json"
    state_path.write_text("{}", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    (tmp_path / "README.md").write_text("# x\n", encoding="utf-8")

    variables = cr._build_variables(state, state_path=state_path, repo_root=tmp_path)
    assert "P2" in variables["STRUCTURAL_PROBES_SUMMARY"]
    assert "## Structural probes" in variables["STRUCTURAL_PROBES_SUMMARY"]
