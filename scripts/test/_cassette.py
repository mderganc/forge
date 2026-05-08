"""Cassette freshness check for HTTP-replay flows.

Verifies that recorded VCR cassettes are not stale and warns/fails accordingly.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Literal


def check_cassette_freshness(
    cassette_path: Path, now: datetime | None = None
) -> Literal["fresh", "warn", "fail"]:
    """Check if cassette is stale based on mtime.

    Args:
        cassette_path: Path to the cassette file (.yaml or .json)
        now: Reference time for staleness check (defaults to current UTC).

    Returns:
        "fresh" if cassette is < 30 days old
        "warn" if cassette is 30-89 days old
        "fail" if cassette is >= 90 days old
    """
    if now is None:
        now = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    if not cassette_path.exists():
        return "fail"

    mtime = cassette_path.stat().st_mtime
    cassette_time = datetime.fromtimestamp(mtime, tz=timezone.utc)

    age_days = (now - cassette_time).days

    if age_days < 30:
        return "fresh"
    elif age_days < 90:
        return "warn"
    else:
        return "fail"
