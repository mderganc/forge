"""Unit tests for iterate natural-language / target parsing and target satisfaction."""

from __future__ import annotations

import pytest

from scripts.iterate.iterate import (
    _target_satisfied,
    parse_natural_iterate,
    parse_target_spec,
    target_spec_to_dict,
)


@pytest.mark.parametrize(
    "raw,expected_op,expected_val",
    [
        ("accuracy >= 0.9", "gte", 0.9),
        ("score > 0.8", "gt", 0.8),
        ("latency <= 100", "lte", 100.0),
        ("90%", "gte", 0.9),
        ("95 %", "gte", 0.95),
    ],
)
def test_parse_target_spec_numeric(raw: str, expected_op: str, expected_val: float) -> None:
    spec, conf = parse_target_spec(raw)
    assert spec is not None
    assert spec.operator == expected_op
    assert isinstance(spec.target_value, (int, float))
    assert abs(float(spec.target_value) - expected_val) < 1e-6
    assert conf in ("high", "medium")


def test_parse_target_spec_empty_returns_none() -> None:
    spec, conf = parse_target_spec("")
    assert spec is None
    assert conf == "low"


def test_parse_target_spec_manual_clarification_low_confidence() -> None:
    spec, conf = parse_target_spec("improve the judge score")  # metric words but no number
    assert spec is not None
    assert conf == "low"
    assert spec.source == "manual_clarification"


def test_parse_natural_iterate_until_and_max_loops() -> None:
    text = "refactor auth flow until accuracy > 90%, max loops 7"
    goal, target_phrase, max_loops, conf = parse_natural_iterate(text)
    assert goal == "refactor auth flow"
    assert target_phrase and "accuracy" in target_phrase.lower()
    assert max_loops == 7
    assert conf == "high"


def test_parse_natural_iterate_empty() -> None:
    g, t, m, c = parse_natural_iterate("   ")
    assert g is None and t is None and m is None
    assert c == "low"


def test_target_spec_to_dict_roundtrip_keys() -> None:
    spec, _ = parse_target_spec("f1 >= 0.85")
    assert spec is not None
    d = target_spec_to_dict(spec)
    assert set(d.keys()) >= {
        "metric_name",
        "operator",
        "target_value",
        "unit",
        "source",
        "measurement_step",
        "confidence",
    }


def test_target_satisfied_uses_metric_gate() -> None:
    spec, _ = parse_target_spec("accuracy >= 0.9")
    assert spec is not None
    assert _target_satisfied(spec, {"target_met": True}) is True
    assert _target_satisfied(spec, {"target_met": False}) is False
    assert _target_satisfied(spec, {"measured_value": 0.95}) is True
    assert _target_satisfied(spec, {"measured_value": 0.5}) is False
    assert _target_satisfied(spec, {"status": "needs_clarification", "target_met": True}) is False


def test_target_satisfied_string_equality() -> None:
    spec, _ = parse_target_spec("release-blocker cleared")
    assert spec is not None
    assert spec.target_value != 0 or isinstance(spec.target_value, str)
    # Non-numeric targets compare as strings on measured_value
    gate = {"measured_value": str(spec.target_value)}
    assert _target_satisfied(spec, gate) is True


def test_target_satisfied_metric_bool_without_spec() -> None:
    """Explicit target_met in gate completes even when no parsed target_spec."""
    assert _target_satisfied(None, {"target_met": True}) is True
    assert _target_satisfied(None, {"target_met": False}) is False


def test_gate_snapshot_includes_json_files(tmp_path) -> None:
    from scripts.iterate.iterate import _gate_snapshot

    d = tmp_path / "gates"
    d.mkdir()
    (d / "a.json").write_text('{"open_findings_total": 1}', encoding="utf-8")
    (d / "bad.json").write_text("not json", encoding="utf-8")
    snap = _gate_snapshot(d)
    assert snap["a.json"]["open_findings_total"] == 1
    assert "_error" in snap["bad.json"]
