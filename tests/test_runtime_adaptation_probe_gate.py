"""Tests for runtime adaptation and probe gates."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.shared import runtime_adaptation as ra
from scripts.shared.structural_probes_gate import (
    STATUS_FAILED,
    STATUS_OK,
    finalize_probe_outcome,
    format_loud_probe_status_banner,
    probe_gate_is_pending,
    validate_probe_gate_at_step_entry,
)


def test_migrate_legacy_runtime_copies_sessions(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    legacy = tmp_path / ".codex" / "forge" / "sessions" / "abc123"
    legacy.mkdir(parents=True)
    (legacy / "session.json").write_text('{"skill_name":"plan"}', encoding="utf-8")

    audit = ra.migrate_legacy_runtime_trees(tmp_path)
    assert (tmp_path / ".forge" / "sessions" / "abc123" / "session.json").is_file()
    assert audit["sources"]
    # Legacy tree is archived under .forge/_archive/ (not left as a dual runtime).
    assert not (tmp_path / ".codex" / "forge").exists()
    assert audit["archived"]
    archive_dirs = list((tmp_path / ".forge" / "_archive").glob("legacy-forge-*"))
    assert archive_dirs
    assert (archive_dirs[0] / "sessions" / "abc123" / "session.json").is_file()


def test_migrate_keeps_legacy_when_env_set(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("FORGE_KEEP_LEGACY_RUNTIME", "1")
    legacy = tmp_path / ".codex" / "forge-codex" / "memory"
    legacy.mkdir(parents=True)
    (legacy / "project.md").write_text("# p", encoding="utf-8")

    audit = ra.migrate_legacy_runtime_trees(tmp_path)
    assert (tmp_path / ".forge" / "memory" / "project.md").is_file()
    assert (tmp_path / ".codex" / "forge-codex").is_dir()
    assert audit["archived"] == []


def test_adapt_runtime_writes_profile(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    profile = ra.adapt_runtime(tmp_path)
    assert profile["runtime_root"] == ".forge"
    assert (tmp_path / ".forge" / "adaptation.json").is_file()
    loaded = ra.load_adaptation_profile(tmp_path)
    assert loaded is not None
    assert loaded["writable_repo_root"] == profile["writable_repo_root"]


def test_non_ok_probe_writes_gate_and_pauses(tmp_path: Path):
    state_dir = tmp_path / "sidecars"
    state_dir.mkdir()
    extra, confirm = finalize_probe_outcome(
        state_dir,
        status=STATUS_FAILED,
        reason="pyscn exited 1",
    )
    assert "STRUCTURAL PROBES — FAILED" in extra
    assert "STRUCTURAL PROBES GATE" in extra
    assert confirm is True
    assert probe_gate_is_pending(state_dir)


def test_ok_probe_clears_gate(tmp_path: Path):
    state_dir = tmp_path / "sidecars"
    state_dir.mkdir()
    finalize_probe_outcome(state_dir, status=STATUS_FAILED, reason="x")
    assert probe_gate_is_pending(state_dir)
    finalize_probe_outcome(state_dir, status=STATUS_OK)
    assert not probe_gate_is_pending(state_dir)


def test_loud_banner_never_empty():
    text = format_loud_probe_status_banner(STATUS_FAILED, reason="timeout")
    assert "STRUCTURAL PROBES — FAILED" in text
    assert "timeout" in text


def test_validate_probe_gate_blocks_pending(tmp_path: Path):
    state_dir = tmp_path / "gate"
    state_dir.mkdir()
    finalize_probe_outcome(state_dir, status=STATUS_FAILED, reason="blocked")
    ok, msg = validate_probe_gate_at_step_entry(state_dir)
    assert ok is False
    assert "STRUCTURAL PROBES GATE" in msg


def test_collect_probe_gate_hints_pending(tmp_path: Path):
    from scripts.shared.structural_probes_gate import (
        collect_probe_gate_hints,
        write_probe_gate_sidecar,
    )

    state_dir = tmp_path / ".forge" / "sessions" / "s1" / "sidecars"
    state_dir.mkdir(parents=True)
    write_probe_gate_sidecar(
        state_dir,
        probe_status=STATUS_FAILED,
        reason="test",
        gate_state="pending",
    )
    hints = collect_probe_gate_hints(tmp_path)
    assert any("PENDING" in h for h in hints)
