"""Narrative (non-table) wave map parsing."""

from __future__ import annotations

import re

from scripts.implement.plan_waves_parse_buckets import ParseBuckets
from scripts.implement.plan_waves_types import (
    ParseDiagnostics,
    ParsePolicy,
    WaveRow,
    build_diagnostics,
)


def _looks_like_wave_heading(line: str) -> re.Match[str] | None:
    return re.match(
        r"^\s{0,3}(?:[-*]\s*)?(?:#{1,6}\s*)?(?:\*\*)?\s*wave\s*(\d+)\b(?:\*\*)?\s*:?\s*(.*)$",
        line.strip(),
        flags=re.IGNORECASE,
    )


def _extract_agent(text: str) -> str:
    m = re.search(r"\bagent\s*:\s*([^,;|)]+)", text, flags=re.IGNORECASE)
    return (m.group(1).strip() if m else "")


def _extract_depends_on(text: str) -> str:
    m = re.search(r"\bdepends(?:\s+on)?\s*:\s*([^;|)]+)", text, flags=re.IGNORECASE)
    return (m.group(1).strip() if m else "")


def _clean_task_text(text: str) -> str:
    cleaned = re.sub(r"^\s*(?:[-*]\s+|\d+\.\s+)", "", text).strip()
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", cleaned)
    cleaned = re.sub(
        r"\b(agent|depends(?:\s+on)?)\s*:\s*[^;|)]+", "", cleaned, flags=re.IGNORECASE
    )
    cleaned = re.sub(r"\s*\(\s*\)", "", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" -;,:")
    return cleaned


def _looks_like_task_label(text: str) -> bool:
    return bool(re.search(r"\btask\s*(?:#?\d+|[A-Za-z_-]+)\b", text, flags=re.IGNORECASE))


def _narrative_row(chunk: str, wave: int, source: str) -> WaveRow:
    return WaveRow(
        task=_clean_task_text(chunk),
        agent=_extract_agent(chunk),
        depends_on=_extract_depends_on(chunk),
        wave=wave,
        parallel_with="",
        raw={"source": source},
    )


def _append_inline_wave_tasks(wave: int, inline: str, rows: list[WaveRow]) -> None:
    if not inline or not _looks_like_task_label(inline):
        return
    chunks = [c.strip() for c in re.split(r"\s*(?:,|;|\|)\s*", inline) if c.strip()]
    for chunk in chunks:
        if _looks_like_task_label(chunk):
            rows.append(_narrative_row(chunk, wave, "narrative-inline"))


def _append_bullet_wave_task(line: str, stripped: str, wave: int, rows: list[WaveRow]) -> None:
    if not re.match(r"^\s*(?:[-*]|\d+\.)\s+", line):
        return
    task = _clean_task_text(stripped)
    if not task or not _looks_like_task_label(task):
        return
    rows.append(_narrative_row(stripped, wave, "narrative-bullet"))


def parse_narrative_wave_rows(markdown: str) -> list[WaveRow]:
    """Best-effort parser for narrative wave maps (non-table formats)."""
    rows: list[WaveRow] = []
    current_wave: int | None = None

    for line in markdown.splitlines():
        wave_match = _looks_like_wave_heading(line)
        if wave_match:
            current_wave = int(wave_match.group(1))
            _append_inline_wave_tasks(current_wave, wave_match.group(2).strip(), rows)
            continue

        if current_wave is None:
            continue

        stripped = line.strip()
        if not stripped or stripped.startswith("```"):
            continue
        if _looks_like_wave_heading(stripped):
            continue

        _append_bullet_wave_task(line, stripped, current_wave, rows)

    return rows


def count_narrative_candidates(lines: list[str], markdown: str) -> int:
    low = markdown.lower()
    return sum(
        1
        for line in lines
        if re.match(r"^\s*(?:[-*]|\d+\.)\s+", line) and "wave" in low
    )


def _diag(
    bucket: ParseBuckets,
    cfg: ParsePolicy,
    *,
    table_candidates: int,
    table_rows: int,
    narrative_candidates: int,
    narrative_row_count: int,
    source: str,
) -> ParseDiagnostics:
    return build_diagnostics(
        table_candidates,
        table_rows,
        narrative_candidates,
        narrative_row_count,
        bucket.buckets,
        bucket.transcript,
        source=source,
        policy=cfg,
    )


def return_narrative_result(
    bucket: ParseBuckets,
    cfg: ParsePolicy,
    markdown: str,
    lines: list[str],
    table_candidates: int,
    *,
    table_parsed_rows: int = 0,
) -> tuple[int, list[WaveRow], ParseDiagnostics]:
    """Parse narrative rows and return (max_wave, rows, diagnostics)."""
    narrative_rows = parse_narrative_wave_rows(markdown)
    narrative_candidates = count_narrative_candidates(lines, markdown)
    nc = len(narrative_rows)
    narrative_cov = (nc / narrative_candidates) if narrative_candidates > 0 else 0.0

    if narrative_candidates > 0 and narrative_cov < cfg.min_narrative_coverage:
        bucket.add("narrative_coverage_reject")
        return 0, [], _diag(
            bucket,
            cfg,
            table_candidates=table_candidates,
            table_rows=table_parsed_rows,
            narrative_candidates=narrative_candidates,
            narrative_row_count=nc,
            source="none",
        )

    if not narrative_rows:
        bucket.add("narrative_rows_missing")
        return 0, [], _diag(
            bucket,
            cfg,
            table_candidates=table_candidates,
            table_rows=table_parsed_rows,
            narrative_candidates=narrative_candidates,
            narrative_row_count=0,
            source="none",
        )

    bucket.add("narrative_rows_used")
    diag = _diag(
        bucket,
        cfg,
        table_candidates=table_candidates,
        table_rows=table_parsed_rows,
        narrative_candidates=narrative_candidates,
        narrative_row_count=nc,
        source="narrative",
    )
    return max(r.wave for r in narrative_rows), narrative_rows, diag


def parse_when_no_table_header(
    bucket: ParseBuckets,
    cfg: ParsePolicy,
    markdown: str,
    lines: list[str],
) -> tuple[int, list[WaveRow], ParseDiagnostics]:
    bucket.add("table_header_missing")
    return return_narrative_result(bucket, cfg, markdown, lines, table_candidates=0)
