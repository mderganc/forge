"""JSON summary extraction from orchestrator output."""

from __future__ import annotations

from forge_next.cli_inspect import summarize_orchestrator_output


def test_summarize_includes_step_and_structural_probes() -> None:
    human = """
CODE-REVIEW — Report (Step 6 of 6)
==================================

---

## Structural probes (Pass B)

**Tools:** pyscn
- **pyscn**: pass — 0 finding(s) — ok

---

Dashboard here
"""
    summary = summarize_orchestrator_output(
        repo_root=__import__("pathlib").Path("/tmp/repo"),
        command="code-review",
        human_output=human,
    )
    assert summary["step"] == 6
    assert summary["max_step"] == 6
    assert summary["structural_probes_summary"] is not None
    assert "pyscn" in summary["structural_probes_summary"]
