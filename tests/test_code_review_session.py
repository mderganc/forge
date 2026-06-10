"""Code-review session resolution (--session, multi-session guard)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.code_review import code_review as cr
from scripts.shared.orchestrator import SkillState, resolve_step_state_path, save_state
from scripts.shared.session_store import create_session


def test_resolve_code_review_state_path_uses_session_id(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "README.md").write_text("# x\n", encoding="utf-8")
    sid, session_path = create_session("code-review", label="probe-session", search_dir=tmp_path)
    st = SkillState(skill_name="code-review", max_step=6, current_step=2)
    st.custom = {"mode": "pr"}
    save_state(st, session_path)

    resolved = resolve_step_state_path("code-review", 2, session_id=sid)
    assert resolved.resolve() == session_path.resolve()


def test_resolve_code_review_state_path_errors_on_multiple_active(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "README.md").write_text("# x\n", encoding="utf-8")
    for label in ("a", "b"):
        st = SkillState(skill_name="code-review", max_step=6, current_step=2)
        st.custom = {"mode": "pr"}
        _, path = create_session("code-review", label=label, search_dir=tmp_path)
        save_state(st, path)

    with pytest.raises(SystemExit) as exc:
        resolve_step_state_path("code-review", 2)
    assert "active code-review sessions" in str(exc.value)


def test_probe_status_one_liner_from_brief() -> None:
    brief = (
        "## Structural probes (Pass B)\n\n"
        "**Tools:** pyscn, skylos\n\n"
        "- **pyscn**: fail — 2 finding(s) — complexity\n"
    )
    line = cr._probe_status_one_liner(brief)
    assert "pyscn" in line
    assert "finding" in line.lower()


def test_probe_status_one_liner_when_not_run() -> None:
    brief = "_Structural probes: not run (no `.structural-probes.json` sidecar)._\n"
    line = cr._probe_status_one_liner(brief)
    assert "not run" in line.lower()
