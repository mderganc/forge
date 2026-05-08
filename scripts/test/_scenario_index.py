"""Parser-gated scenario-index updates.

The report phase (handle_flow_step_7) calls update_scenario_index() to
register a new flow in <scenarios_dir>/README.md. The update is idempotent:
- If the file doesn't exist, it's created with the standard table header.
- If the file exists and parses as a markdown table with the expected columns,
  the new row is appended (or merged: if a row with the same Scope+Type
  already exists, it's updated rather than duplicated).
- If the file exists but doesn't parse, the function aborts WITHOUT
  modifying the file and instructs the caller to write a stderr message.

A backup of the prior file is written to .codex/forge-codex/memory/scenario-index.bak
before any rewrite.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

EXPECTED_COLUMNS = ["Scope", "Type", "Roles", "Failure paths", "Last run", "Status"]
HEADER_LINE = "| " + " | ".join(EXPECTED_COLUMNS) + " |"
SEPARATOR_LINE = "|" + "|".join(["---"] * len(EXPECTED_COLUMNS)) + "|"


@dataclass
class IndexRow:
    """A single row in the scenario index markdown table."""

    scope: str
    type: str
    roles: str
    failure_paths: str
    last_run: str
    status: str

    def to_markdown_row(self) -> str:
        """Convert to a markdown table row string."""
        return f"| {self.scope} | {self.type} | {self.roles} | {self.failure_paths} | {self.last_run} | {self.status} |"


def parse_index(text: str) -> list[IndexRow] | None:
    """Parse the markdown table from the index file.

    Returns None if file doesn't have the expected header or columns are wrong
    (i.e., file is malformed).

    Args:
        text: The full text of the README.md file

    Returns:
        List of IndexRow objects, or None if parsing fails
    """
    lines = text.strip().split("\n")
    if len(lines) < 3:
        # Minimum: header, separator, and at least one row
        return None

    # Find the header line
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("|") and all(col in line for col in EXPECTED_COLUMNS):
            header_idx = i
            break

    if header_idx is None:
        return None

    # Check for separator line after header
    if header_idx + 1 >= len(lines):
        return None

    sep_line = lines[header_idx + 1].strip()
    if not (sep_line.startswith("|") and "---" in sep_line):
        return None

    # Parse data rows
    rows = []
    for line in lines[header_idx + 2 :]:
        line = line.strip()
        if not line.startswith("|"):
            break
        if not line.endswith("|"):
            continue

        # Extract cells by splitting on | and stripping whitespace
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if len(cells) != len(EXPECTED_COLUMNS):
            return None

        try:
            row = IndexRow(
                scope=cells[0],
                type=cells[1],
                roles=cells[2],
                failure_paths=cells[3],
                last_run=cells[4],
                status=cells[5],
            )
            rows.append(row)
        except (IndexError, ValueError):
            return None

    return rows


def update_scenario_index(
    index_path: Path,
    new_row: IndexRow,
    backup_dir: Path,
) -> tuple[bool, str]:
    """Update the scenario index with a new row.

    Returns (success, message). On parse failure, returns (False, error_msg)
    and leaves the file unchanged.

    If the file doesn't exist, creates it with header + new row.
    If the file exists and parses correctly, appends or merges the row
    (if a row with the same scope+type exists, it's updated).

    Args:
        index_path: Path to the scenario index README.md
        new_row: The new row to add or merge
        backup_dir: Directory where backup will be written

    Returns:
        (success: bool, message: str) tuple
    """
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Case 1: file doesn't exist — create it
    if not index_path.exists():
        content = f"{HEADER_LINE}\n{SEPARATOR_LINE}\n{new_row.to_markdown_row()}\n"
        try:
            index_path.parent.mkdir(parents=True, exist_ok=True)
            index_path.write_text(content, encoding="utf-8")
            return (True, f"Created scenario index at {index_path}")
        except OSError as e:
            return (False, f"Failed to write scenario index {index_path}: {e}")

    # Case 2: file exists — parse, merge/append, rewrite
    try:
        existing_text = index_path.read_text(encoding="utf-8")
    except OSError as e:
        return (False, f"Failed to read scenario index {index_path}: {e}")

    existing_rows = parse_index(existing_text)
    if existing_rows is None:
        return (False, f"Scenario index {index_path} is malformed and cannot be parsed")

    # Check if we should merge or append
    merged = False
    for i, row in enumerate(existing_rows):
        if row.scope == new_row.scope and row.type == new_row.type:
            existing_rows[i] = new_row
            merged = True
            break

    if not merged:
        existing_rows.append(new_row)

    # Write backup of the original file
    backup_path = backup_dir / "scenario-index.bak"
    try:
        backup_path.write_text(existing_text, encoding="utf-8")
    except OSError as e:
        return (False, f"Failed to write backup {backup_path}: {e}")

    # Rebuild the content
    content = f"{HEADER_LINE}\n{SEPARATOR_LINE}\n"
    for row in existing_rows:
        content += f"{row.to_markdown_row()}\n"

    try:
        index_path.write_text(content, encoding="utf-8")
        action = "merged" if merged else "appended"
        return (True, f"Scenario index updated ({action}): {index_path}")
    except OSError as e:
        return (False, f"Failed to write scenario index {index_path}: {e}")
