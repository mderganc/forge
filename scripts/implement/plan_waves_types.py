"""Shared types for plan wave parsing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class WaveRow:
    task: str
    agent: str
    depends_on: str
    wave: int
    parallel_with: str
    raw: dict[str, str]


@dataclass(frozen=True)
class ParsePolicy:
    min_table_coverage: float = 0.5
    min_narrative_coverage: float = 0.0
    transcript_theme_limit: int = 4


@dataclass(frozen=True)
class ParseDiagnostics:
    table_coverage: float
    narrative_coverage: float
    buckets: dict[str, int]
    transcript_themes: list[str]
    source: str


def coerce_policy(policy: ParsePolicy | Mapping[str, Any] | None) -> ParsePolicy:
    if isinstance(policy, ParsePolicy):
        return policy
    if not isinstance(policy, Mapping):
        return ParsePolicy()

    def _float(name: str, default: float) -> float:
        try:
            return float(policy.get(name, default))
        except (TypeError, ValueError):
            return default

    def _int(name: str, default: int) -> int:
        try:
            return int(policy.get(name, default))
        except (TypeError, ValueError):
            return default

    return ParsePolicy(
        min_table_coverage=max(0.0, min(1.0, _float("min_table_coverage", ParsePolicy.min_table_coverage))),
        min_narrative_coverage=max(0.0, min(1.0, _float("min_narrative_coverage", ParsePolicy.min_narrative_coverage))),
        transcript_theme_limit=max(1, _int("transcript_theme_limit", ParsePolicy.transcript_theme_limit)),
    )


def build_diagnostics(
    table_candidates: int,
    table_rows: int,
    narrative_candidates: int,
    narrative_rows: int,
    buckets: dict[str, int],
    transcript: list[str],
    source: str,
    policy: ParsePolicy,
) -> ParseDiagnostics:
    table_cov = (table_rows / table_candidates) if table_candidates > 0 else 0.0
    narrative_cov = (narrative_rows / narrative_candidates) if narrative_candidates > 0 else 0.0
    theme_counts: dict[str, int] = {}
    for item in transcript:
        theme_counts[item] = theme_counts.get(item, 0) + 1
    top = sorted(theme_counts.items(), key=lambda kv: (-kv[1], kv[0]))[: policy.transcript_theme_limit]
    themes = [name for name, _ in top]
    return ParseDiagnostics(
        table_coverage=table_cov,
        narrative_coverage=narrative_cov,
        buckets=dict(buckets),
        transcript_themes=themes,
        source=source,
    )
