"""Table and narrative wave parsing for plan markdown."""

from __future__ import annotations

from typing import Any, Mapping

from scripts.implement.plan_waves_narrative import parse_when_no_table_header, return_narrative_result
from scripts.implement.plan_waves_parse_buckets import ParseBuckets
from scripts.implement.plan_waves_table import (
    find_table_header,
    find_wave_column,
    parse_table_section,
)
from scripts.implement.plan_waves_types import (
    ParseDiagnostics,
    ParsePolicy,
    WaveRow,
    coerce_policy,
)


def parse_parallelization_table_with_diagnostics(
    markdown: str,
    policy: ParsePolicy | Mapping[str, Any] | None = None,
) -> tuple[int, list[WaveRow], ParseDiagnostics]:
    """Parse wave assignments with policy checks and diagnostics."""
    cfg = coerce_policy(policy)
    bucket = ParseBuckets()
    lines = markdown.splitlines()

    header_idx, headers_norm = find_table_header(lines)
    if header_idx is None:
        return parse_when_no_table_header(bucket, cfg, markdown, lines)

    wave_col = find_wave_column(headers_norm)
    if wave_col is None:
        bucket.add("table_wave_column_missing")
        return return_narrative_result(bucket, cfg, markdown, lines, table_candidates=0)

    return parse_table_section(
        bucket, cfg, markdown, lines, header_idx, headers_norm, wave_col
    )
