"""Markdown table wave map parsing."""

from __future__ import annotations

from scripts.implement.plan_waves_narrative import return_narrative_result
from scripts.implement.plan_waves_table_io import (
    is_separator_row,
    normalize_header,
    split_table_row,
    wave_cell_to_int,
)
from scripts.implement.plan_waves_parse_buckets import ParseBuckets
from scripts.implement.plan_waves_types import (
    ParseDiagnostics,
    ParsePolicy,
    WaveRow,
    build_diagnostics,
)


def find_table_header(lines: list[str]) -> tuple[int | None, list[str]]:
    for i, line in enumerate(lines):
        if "|" not in line or line.strip().startswith("```"):
            continue
        cells = split_table_row(line)
        if len(cells) < 2:
            continue
        norms = [normalize_header(c) for c in cells]
        if any(n == "wave" or n.startswith("wave ") for n in norms):
            return i, norms
    return None, []


def find_wave_column(headers_norm: list[str]) -> int | None:
    for j, n in enumerate(headers_norm):
        if n == "wave" or n.startswith("wave "):
            return j
    return None


def _column_index(headers_norm: list[str], *names: str) -> int | None:
    for want in names:
        w = normalize_header(want)
        for j, n in enumerate(headers_norm):
            if n == w or n.replace(" ", "") == w.replace(" ", ""):
                return j
    return None


def _wave_row_from_cells(
    cells: list[str],
    headers_norm: list[str],
    wave_col: int,
    ti: int | None,
    ai: int | None,
    di: int | None,
    pi: int | None,
    wv: int,
) -> WaveRow:
    def get(col: int | None, default: str = "") -> str:
        if col is None or col >= len(cells):
            return default
        return cells[col].strip()

    return WaveRow(
        task=get(ti, "(task)"),
        agent=get(ai, ""),
        depends_on=get(di, ""),
        wave=wv,
        parallel_with=get(pi, ""),
        raw={
            headers_norm[k]: (cells[k] if k < len(cells) else "")
            for k in range(len(headers_norm))
        },
    )


def parse_table_rows(
    lines: list[str],
    header_idx: int,
    headers_norm: list[str],
    wave_col: int,
    bucket: ParseBuckets,
) -> tuple[list[WaveRow], int]:
    ti = _column_index(headers_norm, "task")
    ai = _column_index(headers_norm, "agent")
    di = _column_index(headers_norm, "depends on", "depends_on", "depends")
    pi = _column_index(headers_norm, "can parallel with", "can_parallel_with", "parallel")

    rows: list[WaveRow] = []
    table_candidate_rows = 0
    data_start = header_idx + 1
    if data_start < len(lines) and is_separator_row(lines[data_start]):
        data_start += 1

    for line in lines[data_start:]:
        if "|" not in line or line.strip().startswith("```"):
            break
        cells = split_table_row(line)
        if len(cells) <= wave_col:
            continue
        if normalize_header(cells[0]) == "task" and "wave" in [normalize_header(c) for c in cells]:
            continue
        table_candidate_rows += 1

        wv = wave_cell_to_int(cells[wave_col])
        if wv is None:
            bucket.add("table_wave_value_missing")
            continue

        rows.append(_wave_row_from_cells(cells, headers_norm, wave_col, ti, ai, di, pi, wv))

    return rows, table_candidate_rows


def parse_table_section(
    bucket: ParseBuckets,
    cfg: ParsePolicy,
    markdown: str,
    lines: list[str],
    header_idx: int,
    headers_norm: list[str],
    wave_col: int,
) -> tuple[int, list[WaveRow], ParseDiagnostics]:
    rows, table_candidate_rows = parse_table_rows(
        lines, header_idx, headers_norm, wave_col, bucket
    )

    if not rows:
        bucket.add("table_rows_missing")
        return return_narrative_result(
            bucket, cfg, markdown, lines, table_candidate_rows
        )

    table_cov = (len(rows) / table_candidate_rows) if table_candidate_rows > 0 else 0.0
    if table_candidate_rows > 0 and table_cov < cfg.min_table_coverage:
        bucket.add("table_coverage_reject")
        narrative = return_narrative_result(
            bucket,
            cfg,
            markdown,
            lines,
            table_candidate_rows,
            table_parsed_rows=len(rows),
        )
        if narrative[1]:
            return narrative

    max_wave = max(r.wave for r in rows)
    bucket.add("table_rows_used")
    diag = build_diagnostics(
        table_candidate_rows,
        len(rows),
        0,
        0,
        bucket.buckets,
        bucket.transcript,
        source="table",
        policy=cfg,
    )
    return max_wave, rows, diag
