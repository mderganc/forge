import json
from pathlib import Path

from scripts.shared import orchestrator


def test_runtime_root_uses_canonical_layout_when_dot_codex_is_directory(tmp_path: Path):
    (tmp_path / ".codex").mkdir()

    expected = tmp_path / ".codex" / "forge"
    assert orchestrator.runtime_root(tmp_path) == expected
    assert orchestrator.runtime_state_path("develop", tmp_path) == expected / "state" / "develop.json"


def test_runtime_root_prefers_legacy_forge_codex_when_canonical_missing(tmp_path: Path):
    """Older repos may only have `.codex/forge-codex/` until migrated."""
    codex = tmp_path / ".codex"
    codex.mkdir()
    legacy = codex / "forge-codex"
    legacy.mkdir()

    assert orchestrator.runtime_root(tmp_path) == legacy


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


def test_consume_handoff_reads_and_closes_files(tmp_path: Path):
    runtime = orchestrator.runtime_memory_dir(tmp_path)
    legacy = orchestrator.legacy_memory_dir(tmp_path)
    runtime.mkdir(parents=True, exist_ok=True)
    legacy.mkdir(parents=True, exist_ok=True)

    runtime_handoff = runtime / "handoff-develop.md"
    legacy_handoff = legacy / "handoff-develop.md"
    runtime_handoff.write_text("runtime handoff", encoding="utf-8")
    legacy_handoff.write_text("legacy handoff", encoding="utf-8")

    content = orchestrator.consume_handoff("develop", search_dir=tmp_path)

    assert content == "runtime handoff"
    assert not runtime_handoff.exists()
    assert not legacy_handoff.exists()


def test_close_handoff_is_noop_when_missing(tmp_path: Path):
    assert orchestrator.close_handoff("implement", search_dir=tmp_path) is False


def test_detect_active_sessions_skips_logically_complete_state(tmp_path: Path):
    state_path = orchestrator.runtime_state_path("plan", tmp_path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state = orchestrator.SkillState(skill_name="plan", max_step=7)
    state.current_step = 7
    state.last_completed_step = 7
    orchestrator.save_state(state, state_path)

    sessions = orchestrator.detect_active_sessions(tmp_path)
    assert sessions == []


def test_append_skill_run_memory_trims_to_last_30(tmp_path: Path):
    state_path = orchestrator.runtime_state_path("plan", tmp_path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    s = orchestrator.SkillState(skill_name="plan", max_step=7)
    s.started_at = "2026-01-01T00:00:00+00:00"

    history_path = None
    for i in range(35):
        history_path = orchestrator.append_skill_run_memory(
            "plan",
            step=(i % 7) + 1,
            phase=f"Phase {i}",
            summary=f"run {i}",
            state=s,
            state_path=state_path,
            search_dir=tmp_path,
        )

    assert history_path is not None
    lines = history_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 30
    first = json.loads(lines[0])
    last = json.loads(lines[-1])
    assert first["summary"] == "run 5"
    assert last["summary"] == "run 34"


def test_append_skill_run_memory_records_session_and_handoff_refs(tmp_path: Path):
    state_path = orchestrator.runtime_state_path("develop", tmp_path)
    handoff_path = orchestrator.runtime_memory_dir(tmp_path) / "handoff-develop.md"
    handoff_path.parent.mkdir(parents=True, exist_ok=True)
    handoff_path.write_text("x", encoding="utf-8")

    s = orchestrator.SkillState(skill_name="develop", max_step=7)
    s.started_at = "2026-01-01T00:00:00+00:00"
    s.current_step = 7
    s.last_completed_step = 7
    s.completed_at = "2026-01-01T00:05:00+00:00"

    history_path = orchestrator.append_skill_run_memory(
        "develop",
        step=7,
        phase="Handoff",
        summary="Completed develop workflow.",
        state=s,
        state_path=state_path,
        handoff_path=handoff_path,
        search_dir=tmp_path,
    )

    payload = json.loads(history_path.read_text(encoding="utf-8").splitlines()[-1])
    assert payload["state_path"].endswith("develop.json")
    assert payload["handoff_path"].endswith("handoff-develop.md")
    assert payload["session_ref"].startswith("develop:")
    assert payload["handoff_ref"].endswith("handoff-develop.md")
