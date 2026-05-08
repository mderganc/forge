#!/usr/bin/env python3
"""Git history analytics for the diagnose skill.

Identifies code churn hotspots, temporal coupling between files,
and recent committers for blame analysis.

Usage:
    python3 git_hotspots.py [--path <dir>] [--days <N>] [--top <N>]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter


def run_git(args: list[str], cwd: str | None = None) -> str:
    """Run a git command and return stdout."""
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=30,
    )
    if result.returncode != 0:
        print(f"WARNING: git {' '.join(args)} failed: {result.stderr.strip()}", file=sys.stderr)
        return ""
    return result.stdout


def get_churn_hotspots(path: str = ".", days: int = 90, top_n: int = 20) -> list[tuple[str, int]]:
    """Get most frequently changed files in the given time window."""
    output = run_git(
        ["log", f"--since={days} days ago", "--format=format:", "--name-only", "--", path],
    )
    if not output:
        return []

    counter = Counter(
        line.strip()
        for line in output.splitlines()
        if line.strip()
    )
    return counter.most_common(top_n)


def get_temporal_coupling(path: str = ".", days: int = 90, min_coupling: int = 3) -> list[tuple[tuple[str, str], int]]:
    """Find files that frequently change together in the same commit."""
    output = run_git(
        ["log", f"--since={days} days ago", "--format=format:%H", "--name-only", "--", path],
    )
    if not output:
        return []

    # Parse commits and their files
    commits: list[list[str]] = []
    current_files: list[str] = []

    for line in output.splitlines():
        line = line.strip()
        if not line:
            if current_files:
                commits.append(current_files)
                current_files = []
        elif len(line) == 40 and all(c in "0123456789abcdef" for c in line):
            if current_files:
                commits.append(current_files)
            current_files = []
        else:
            current_files.append(line)
    if current_files:
        commits.append(current_files)

    # Count co-occurrences
    pair_counter: Counter = Counter()
    for files in commits:
        unique_files = sorted(set(files))
        for i in range(len(unique_files)):
            for j in range(i + 1, len(unique_files)):
                pair_counter[(unique_files[i], unique_files[j])] += 1

    # Filter by minimum coupling threshold
    coupled = [
        (pair, count)
        for pair, count in pair_counter.most_common(50)
        if count >= min_coupling
    ]
    return coupled[:20]


def get_recent_committers(path: str = ".", days: int = 30, top_n: int = 10) -> list[tuple[str, int]]:
    """Get most active committers in the given path/time window."""
    output = run_git(
        ["log", f"--since={days} days ago", "--format=%aN", "--", path],
    )
    if not output:
        return []

    counter = Counter(
        line.strip()
        for line in output.splitlines()
        if line.strip()
    )
    return counter.most_common(top_n)


def get_recent_commits(path: str = ".", days: int = 7, top_n: int = 20) -> list[str]:
    """Get recent commit summaries."""
    output = run_git(
        ["log", f"--since={days} days ago", "--oneline", f"-{top_n}", "--", path],
    )
    if not output:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def render_markdown(
    hotspots: list[tuple[str, int]],
    coupling: list[tuple[tuple[str, str], int]],
    committers: list[tuple[str, int]],
    recent: list[str],
    path: str,
    days: int,
) -> str:
    """Render analysis results as markdown."""
    lines = [
        f"# Git History Analysis: `{path}`",
        f"**Window:** last {days} days",
        "",
    ]

    # Churn hotspots
    lines.append("## Churn Hotspots")
    lines.append("")
    if hotspots:
        lines.append("Files that change most frequently (higher churn correlates with higher bug density):")
        lines.append("")
        lines.append("| Rank | File | Changes |")
        lines.append("|------|------|---------|")
        for i, (filepath, count) in enumerate(hotspots, 1):
            lines.append(f"| {i} | `{filepath}` | {count} |")
    else:
        lines.append("No changes found in the specified window.")
    lines.append("")

    # Temporal coupling
    lines.append("## Temporal Coupling")
    lines.append("")
    if coupling:
        lines.append("Files that frequently change together (hidden dependencies):")
        lines.append("")
        lines.append("| File A | File B | Co-changes |")
        lines.append("|--------|--------|-----------|")
        for (file_a, file_b), count in coupling:
            lines.append(f"| `{file_a}` | `{file_b}` | {count} |")
    else:
        lines.append("No significant temporal coupling detected.")
    lines.append("")

    # Recent committers
    lines.append("## Recent Committers")
    lines.append("")
    if committers:
        lines.append("| Author | Commits |")
        lines.append("|--------|---------|")
        for author, count in committers:
            lines.append(f"| {author} | {count} |")
    else:
        lines.append("No commits found.")
    lines.append("")

    # Recent commits
    lines.append("## Recent Commits")
    lines.append("")
    if recent:
        for commit in recent:
            lines.append(f"- `{commit}`")
    else:
        lines.append("No recent commits.")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Git history analytics for forge-codex diagnose skill"
    )
    parser.add_argument(
        "--path", default=".",
        help="Directory or file path to analyze (default: current directory)",
    )
    parser.add_argument(
        "--days", type=int, default=90,
        help="Number of days to look back (default: 90)",
    )
    parser.add_argument(
        "--top", type=int, default=20,
        help="Number of top results to show (default: 20)",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON instead of markdown",
    )
    args = parser.parse_args()

    hotspots = get_churn_hotspots(args.path, args.days, args.top)
    coupling = get_temporal_coupling(args.path, args.days)
    committers = get_recent_committers(args.path, args.days)
    recent = get_recent_commits(args.path, min(args.days, 14))

    if args.json:
        output = {
            "hotspots": [{"file": f, "changes": c} for f, c in hotspots],
            "temporal_coupling": [{"file_a": a, "file_b": b, "co_changes": c} for (a, b), c in coupling],
            "committers": [{"author": a, "commits": c} for a, c in committers],
            "recent_commits": recent,
        }
        print(json.dumps(output, indent=2))
    else:
        print(render_markdown(hotspots, coupling, committers, recent, args.path, args.days))


if __name__ == "__main__":
    main()
