from __future__ import annotations

from pathlib import Path

from scripts.implement.plan_waves import parse_parallelization_table, sync_waves_from_plan_file


def test_parse_parallelization_table_extracts_waves():
    md = """
## 4. Parallelization Map

| Task | Agent | Depends On | Wave | Can Parallel With |
|------|-------|-----------|------|-------------------|
| Task 1 | Dev-1 | none | 1 | Task 2, Task 3 |
| Task 2 | Dev-2 | none | 1 | Task 1, Task 3 |
| Task 3 | QA | none | 1 | Task 1, Task 2 |
| Task 4 | Dev-1 | Task 1 | 2 | Task 5 |
| Task 5 | Dev-2 | Task 2 | 2 | Task 4 |
| Task 6 | Dev-1 | Task 4, Task 5 | 3 | none |
"""
    total, rows = parse_parallelization_table(md)
    assert total == 3
    assert len(rows) == 6
    assert sum(1 for r in rows if r.wave == 1) == 3
    assert sum(1 for r in rows if r.wave == 2) == 2


def test_parse_parallelization_table_empty_when_no_wave_column():
    md = "| A | B |\n|---|---|\n| x | y |\n"
    total, rows = parse_parallelization_table(md)
    assert total == 0
    assert rows == []


def test_sync_waves_from_plan_file_reads_repo_template(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    sample = tmp_path / "plan.md"
    sample.write_text(
        (repo_root / "templates/writing-plans.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    total, rows = sync_waves_from_plan_file(sample)
    assert total >= 3
    assert len(rows) >= 6
