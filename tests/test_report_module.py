"""Smoke tests for scripts.shared.report (skylos Y1 — prove utility is used)."""

from __future__ import annotations

from scripts.shared.findings import Finding
from scripts.shared.report import write_report


def test_write_report_renders_frontmatter_and_findings() -> None:
    md = write_report(
        title="Diagnose",
        metadata={"mode": "structural"},
        summary="Skylos triage complete.",
        sections=[("Context", "Complexity + dead-code hints.")],
        findings=[
            Finding(
                id="F1",
                phase="analyze",
                severity="warning",
                title="Pyscn complexity",
                detail="validate_coverage > 10",
                status="open",
            )
        ],
        dismissed=[],
        conclusion="Do not delete reserved APIs.",
    )
    assert "---" in md
    assert "Skylos triage" in md
    assert "F1" in md
    assert "Pyscn complexity" in md


def test_diagnostic_report_structured_uses_write_report() -> None:
    from scripts.diagnose.diagnostic_report import generate_structured_report

    md = generate_structured_report(title="Flaky CI", severity="high", mode="guided")
    assert "---" in md
    assert "Diagnostic Report: Flaky CI" in md
    assert "Methodology checklist" in md
