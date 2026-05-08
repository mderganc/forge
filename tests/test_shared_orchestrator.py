from pathlib import Path

from scripts.shared import orchestrator


def test_runtime_root_uses_canonical_layout_when_dot_codex_is_directory(tmp_path: Path):
    (tmp_path / ".codex").mkdir()

    expected = tmp_path / ".codex" / "forge-codex"
    assert orchestrator.runtime_root(tmp_path) == expected
    assert orchestrator.runtime_state_path("develop", tmp_path) == expected / "state" / "develop.json"


def test_runtime_root_falls_back_to_legacy_when_dot_codex_is_not_directory(tmp_path: Path):
    blocked_anchor = tmp_path / ".codex"
    blocked_anchor.write_text("")

    expected = tmp_path / ".forge"
    assert orchestrator.runtime_root(tmp_path) == expected
    assert orchestrator.runtime_state_path("develop", tmp_path) == expected / "state" / "develop.json"


def test_scan_evaluate_sessions_uses_correct_mode_max_steps(tmp_path: Path):
    docs = tmp_path / "docs"
    docs.mkdir()

    pre_state = docs / ".evaluate-state.json"
    pre_state.write_text('{"mode": "pre", "current_step": 6, "last_completed_step": 5}')
    sessions = orchestrator.detect_active_sessions(tmp_path)
    assert len(sessions) == 1
    assert sessions[0]["skill"] == "evaluate"
    assert sessions[0]["max_step"] == 7

    pre_state.unlink()
    post_state = docs / ".evaluate-state.json"
    post_state.write_text('{"mode": "post", "current_step": 7, "last_completed_step": 6}')
    sessions = orchestrator.detect_active_sessions(tmp_path)
    assert len(sessions) == 1
    assert sessions[0]["max_step"] == 8

    post_state.unlink()
    review_state = docs / ".evaluate-state.json"
    review_state.write_text('{"mode": "review", "current_step": 4, "last_completed_step": 3}')
    sessions = orchestrator.detect_active_sessions(tmp_path)
    assert len(sessions) == 1
    assert sessions[0]["max_step"] == 5
