"""Golden cases for plan_waves_parse (table + narrative paths)."""

from __future__ import annotations

from scripts.implement.plan_waves import parse_parallelization_table_with_diagnostics
from scripts.implement.plan_waves_types import ParsePolicy


def test_parser_table_source_and_coverage():
    md = """
| Task | Agent | Depends On | Wave |
|------|-------|------------|------|
| Task A | Dev | none | 1 |
| Task B | QA | Task A | 2 |
"""
    total, rows, diag = parse_parallelization_table_with_diagnostics(md)
    assert total == 2
    assert len(rows) == 2
    assert diag.source == "table"
    assert diag.table_coverage == 1.0


def test_parser_skips_rows_without_numeric_wave():
    md = """
| Task | Wave |
|------|------|
| Bad | not-a-number |
| Good | 1 |
"""
    total, rows, diag = parse_parallelization_table_with_diagnostics(md)
    assert total == 1
    assert len(rows) == 1
    assert rows[0].task == "Good"
    assert "table_wave_value_missing" in diag.buckets


def test_parser_narrative_fallback_when_no_table():
    md = """
Wave 1:
- Task 1: parser (agent: Backend)
"""
    total, rows, diag = parse_parallelization_table_with_diagnostics(md)
    assert total == 1
    assert len(rows) == 1
    assert diag.source == "narrative"
    assert rows[0].agent == "Backend"
