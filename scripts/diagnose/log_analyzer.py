#!/usr/bin/env python3
"""Structured log analysis for the diagnose skill.

Extracts error patterns, frequency histograms, spike detection,
and first/last occurrence from log files.

Usage:
    python3 log_analyzer.py --file <logfile> [--pattern <regex>] [--top <N>]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path


# Common timestamp patterns in logs
TIMESTAMP_PATTERNS = [
    # ISO 8601: 2024-01-15T14:30:00
    re.compile(r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})"),
    # Syslog: Jan 15 14:30:00
    re.compile(r"([A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})"),
    # Epoch seconds (10 digits)
    re.compile(r"\b(\d{10})\b"),
]

# Default error pattern
DEFAULT_ERROR_PATTERN = re.compile(
    r"(error|exception|fatal|panic|fail|critical|traceback)",
    re.IGNORECASE,
)


def extract_timestamp(line: str) -> str | None:
    """Try to extract a timestamp from a log line."""
    for pattern in TIMESTAMP_PATTERNS:
        match = pattern.search(line)
        if match:
            return match.group(1)
    return None


def extract_minute_bucket(line: str) -> str | None:
    """Extract a minute-level time bucket from a log line."""
    ts = extract_timestamp(line)
    if ts is None:
        return None
    # Truncate to minute
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(ts[:19], fmt)
            return dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            continue
    return ts[:16] if len(ts) >= 16 else ts


def normalize_line(line: str) -> str:
    """Normalize a log line for pattern grouping.

    Replaces numbers, UUIDs, hex strings, and timestamps with placeholders
    to group similar error messages together.
    """
    # Remove timestamps
    for pattern in TIMESTAMP_PATTERNS:
        line = pattern.sub("<TIMESTAMP>", line)
    # Replace UUIDs
    line = re.sub(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        "<UUID>",
        line,
        flags=re.IGNORECASE,
    )
    # Replace hex strings (8+ chars)
    line = re.sub(r"\b0x[0-9a-f]{4,}\b", "<HEX>", line, flags=re.IGNORECASE)
    # Replace long numbers (IDs, ports, PIDs)
    line = re.sub(r"\b\d{4,}\b", "<NUM>", line)
    # Replace IP addresses
    line = re.sub(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", "<IP>", line)
    return line.strip()


def analyze_log(
    filepath: Path,
    pattern: re.Pattern | None = None,
    top_n: int = 20,
) -> dict:
    """Analyze a log file and return structured results.

    Args:
        filepath: Path to the log file.
        pattern: Regex to filter lines (default: error/exception/fatal).
        top_n: Number of top patterns to return.

    Returns:
        Dict with keys: total_lines, matched_lines, top_patterns,
        time_histogram, first_seen, last_seen.
    """
    if pattern is None:
        pattern = DEFAULT_ERROR_PATTERN

    total_lines = 0
    matched_lines = 0
    pattern_counter: Counter = Counter()
    time_buckets: Counter = Counter()
    first_seen: dict[str, str] = {}
    last_seen: dict[str, str] = {}

    with open(filepath, encoding="utf-8", errors="replace") as f:
        for line in f:
            total_lines += 1
            if not pattern.search(line):
                continue
            matched_lines += 1

            normalized = normalize_line(line)
            pattern_counter[normalized] += 1

            bucket = extract_minute_bucket(line)
            if bucket:
                time_buckets[bucket] += 1
                if normalized not in first_seen:
                    first_seen[normalized] = bucket
                last_seen[normalized] = bucket

    # Detect spikes: buckets with > 2x the median count
    spike_buckets = []
    if time_buckets:
        counts = sorted(time_buckets.values())
        median = counts[len(counts) // 2]
        threshold = max(median * 2, 3)
        spike_buckets = [
            (bucket, count)
            for bucket, count in sorted(time_buckets.items())
            if count > threshold
        ]

    return {
        "total_lines": total_lines,
        "matched_lines": matched_lines,
        "match_rate": f"{matched_lines / total_lines * 100:.2f}%" if total_lines else "N/A",
        "top_patterns": pattern_counter.most_common(top_n),
        "time_histogram": sorted(time_buckets.items()),
        "spike_buckets": spike_buckets,
        "first_seen": {k: first_seen.get(k, "?") for k, _ in pattern_counter.most_common(top_n)},
        "last_seen": {k: last_seen.get(k, "?") for k, _ in pattern_counter.most_common(top_n)},
    }


def render_markdown(results: dict, filepath: str) -> str:
    """Render analysis results as markdown."""
    lines = [
        f"# Log Analysis: {filepath}",
        "",
        f"**Total lines:** {results['total_lines']}",
        f"**Matched lines:** {results['matched_lines']} ({results['match_rate']})",
        "",
    ]

    # Top patterns
    lines.append("## Top Error Patterns")
    lines.append("")
    lines.append("| # | Count | Pattern | First Seen | Last Seen |")
    lines.append("|---|-------|---------|-----------|-----------|")
    for i, (pattern, count) in enumerate(results["top_patterns"], 1):
        first = results["first_seen"].get(pattern, "?")
        last = results["last_seen"].get(pattern, "?")
        # Truncate long patterns
        display = pattern[:80] + "..." if len(pattern) > 80 else pattern
        # Escape pipe characters for markdown
        display = display.replace("|", "\\|")
        lines.append(f"| {i} | {count} | `{display}` | {first} | {last} |")
    lines.append("")

    # Time histogram
    if results["time_histogram"]:
        lines.append("## Error Frequency Over Time")
        lines.append("")
        lines.append("| Time Bucket | Count |")
        lines.append("|------------|-------|")
        for bucket, count in results["time_histogram"]:
            lines.append(f"| {bucket} | {count} |")
        lines.append("")

    # Spikes
    if results["spike_buckets"]:
        lines.append("## Detected Spikes")
        lines.append("")
        for bucket, count in results["spike_buckets"]:
            lines.append(f"- **{bucket}**: {count} errors (spike)")
        lines.append("")
    else:
        lines.append("## Detected Spikes")
        lines.append("")
        lines.append("No significant spikes detected.")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Structured log analysis for forge-codex diagnose skill"
    )
    parser.add_argument(
        "--file", required=True,
        help="Path to the log file to analyze",
    )
    parser.add_argument(
        "--pattern", default=None,
        help="Regex pattern to filter lines (default: error/exception/fatal/panic)",
    )
    parser.add_argument(
        "--top", type=int, default=20,
        help="Number of top patterns to show (default: 20)",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON instead of markdown",
    )
    args = parser.parse_args()

    filepath = Path(args.file)
    if not filepath.exists():
        print(f"ERROR: File not found: {filepath}")
        sys.exit(1)

    pattern = re.compile(args.pattern, re.IGNORECASE) if args.pattern else None

    results = analyze_log(filepath, pattern=pattern, top_n=args.top)

    if args.json:
        # Convert Counter items to serializable format
        output = {
            "total_lines": results["total_lines"],
            "matched_lines": results["matched_lines"],
            "match_rate": results["match_rate"],
            "top_patterns": [{"pattern": p, "count": c} for p, c in results["top_patterns"]],
            "spike_buckets": [{"bucket": b, "count": c} for b, c in results["spike_buckets"]],
        }
        print(json.dumps(output, indent=2))
    else:
        print(render_markdown(results, str(filepath)))


if __name__ == "__main__":
    main()
