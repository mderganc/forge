"""Design spec gate sidecar (.design-spec-gate.json + legacy compat)."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.develop import spec_gate


def test_gate_sidecar_prefers_design_filename(tmp_path: Path) -> None:
    state = tmp_path / "session.json"
    state.write_text("{}", encoding="utf-8")
    primary = tmp_path / spec_gate.SPEC_GATE_FILE
    primary.write_text(json.dumps({"spec_path": "x.md"}), encoding="utf-8")
    assert spec_gate.gate_sidecar_path(state) == primary


def test_gate_sidecar_reads_legacy_develop_file(tmp_path: Path) -> None:
    state = tmp_path / "session.json"
    state.write_text("{}", encoding="utf-8")
    legacy = tmp_path / spec_gate.LEGACY_SPEC_GATE_FILE
    legacy.write_text(
        json.dumps(
            {
                "spec_path": "docs/forge/specs/2026-01-01-slug-design.md",
                "spec_written": True,
                "self_review_passed": True,
                "user_approved": True,
            }
        ),
        encoding="utf-8",
    )
    assert spec_gate.gate_sidecar_path(state) == legacy
    data = spec_gate.load_gate_json(legacy)
    assert data is not None
    assert data["user_approved"] is True
