"""Mode detection — determine if a plan has been implemented.

Extracts file references from plan text, checks whether those files
exist and have been modified since the plan was written. If >50% show
matching changes, mode is post-implementation.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

_FILE_PATTERNS = [
    r'(?:Create|Modify|Edit|Test|Update|Add to)[:\s]+`([^`]+?(?:\.\w+))(?::\d+[-\u2013]\d+)?`',
    r'`([\w/._-]+\.(?:py|ts|tsx|js|jsx|md|json|yaml|yml|toml|cfg|sql|html|css))`',
]


def extract_file_references(plan_text: str) -> list[str]:
    """Extract unique file path references from plan text."""
    refs: set[str] = set()
    for pattern in _FILE_PATTERNS:
        for match in re.finditer(pattern, plan_text):
            path = match.group(1)
            path = re.sub(r':\d+[-\u2013]\d+$', '', path)
            if '/' in path or path.count('.') == 1:
                refs.add(path)
    return sorted(refs)


def _file_has_recent_changes(filepath: str, since_timestamp: str, repo_root: str) -> bool:
    """Check if a file has git commits since a given ISO timestamp."""
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", f"--since={since_timestamp}", "--", filepath],
            capture_output=True, text=True, cwd=repo_root, timeout=10,
        )
        return bool(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def detect_mode(
    referenced_files: list[str],
    repo_root: str,
    plan_mtime: str | None = None,
) -> tuple[str, int, int]:
    """Detect pre or post implementation mode.

    Args:
        referenced_files: File paths extracted from the plan.
        repo_root: Root of the git repository.
        plan_mtime: ISO timestamp of plan file modification time.

    Returns:
        Tuple of (mode, matched_count, total_count).
    """
    if not referenced_files:
        return ("pre", 0, 0)

    matched = 0
    total = len(referenced_files)

    for fpath in referenced_files:
        full_path = Path(repo_root) / fpath
        if not full_path.exists():
            continue
        if plan_mtime:
            # Only count as matched if the file has commits AFTER the plan was written
            if _file_has_recent_changes(fpath, plan_mtime, repo_root):
                matched += 1
            # else: file exists but no recent changes — not implemented yet
        else:
            # No plan mtime available — fall back to existence check
            matched += 1

    ratio = matched / total if total > 0 else 0
    mode = "post" if ratio > 0.5 else "pre"
    return (mode, matched, total)
