"""Sidecar file handling for the test-skill flows mode.

Mirrors evaluate's findings-sidecar pattern but with a different schema (single
object, not array) so the function is parallel — not a reuse of
_ingest_findings_sidecars.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

VALID_FLOW_TYPES = {"scenario", "bdd", "http-replay", "workflow-dryrun"}


def recommendation_sidecar_path(state_dir: Path) -> Path:
    """Return the path to the recommendation sidecar for the test skill."""
    return state_dir / ".test-recommendation-step2.json"


def write_recommendation_override(state_dir: Path, flow_type: str) -> Path:
    """Pre-write the sidecar when --flow-type was passed at CLI.

    Used by step 1/2 of test.py when the user has already chosen a type.

    Args:
        state_dir: Directory where state.json lives
        flow_type: One of VALID_FLOW_TYPES

    Returns:
        Path to the written sidecar file
    """
    path = recommendation_sidecar_path(state_dir)
    data = {
        "chosen": flow_type,
        "reasoning": "user override via --flow-type",
        "confidence": 1.0,
        "alternatives": [],
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def ingest_recommendation_sidecar(state_dir: Path) -> dict:
    """Read + validate + delete the sidecar.

    Validation:
    - File exists (else: sys.exit(1) with stderr message naming the file)
    - JSON parses (else: sys.exit(1) with stderr message + parse error)
    - "chosen" present and in VALID_FLOW_TYPES (else: sys.exit(1))
    - "reasoning" present and non-empty (else: sys.exit(1))
    - "confidence" present and 0.0..1.0 (else: sys.exit(1))

    NEVER falls back to a default. On any validation failure, exits with a
    clear stderr message naming the file + the specific issue.

    Args:
        state_dir: Directory where state.json lives

    Returns:
        The parsed sidecar dict on success.

    Deletes the sidecar file after successful validation (so re-runs don't
    re-ingest stale data).
    """
    path = recommendation_sidecar_path(state_dir)

    # Check file exists
    if not path.exists():
        print(f"ERROR: recommendation sidecar not found: {path}", file=sys.stderr)
        sys.exit(1)

    # Parse JSON
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: failed to parse recommendation sidecar {path}: {e}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"ERROR: failed to read recommendation sidecar {path}: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate chosen
    if "chosen" not in data:
        print(f"ERROR: recommendation sidecar {path} missing 'chosen' field", file=sys.stderr)
        sys.exit(1)

    chosen = data.get("chosen")
    if chosen not in VALID_FLOW_TYPES:
        print(
            f"ERROR: recommendation sidecar {path} has invalid 'chosen' value: {chosen!r} "
            f"(must be one of {sorted(VALID_FLOW_TYPES)})",
            file=sys.stderr,
        )
        sys.exit(1)

    # Validate reasoning
    if "reasoning" not in data:
        print(f"ERROR: recommendation sidecar {path} missing 'reasoning' field", file=sys.stderr)
        sys.exit(1)

    reasoning = data.get("reasoning")
    if not reasoning or not str(reasoning).strip():
        print(f"ERROR: recommendation sidecar {path} has empty 'reasoning' field", file=sys.stderr)
        sys.exit(1)

    # Validate confidence
    if "confidence" not in data:
        print(f"ERROR: recommendation sidecar {path} missing 'confidence' field", file=sys.stderr)
        sys.exit(1)

    try:
        confidence = float(data.get("confidence"))
        if not (0.0 <= confidence <= 1.0):
            raise ValueError(f"{confidence} out of range [0.0, 1.0]")
    except (TypeError, ValueError) as e:
        print(
            f"ERROR: recommendation sidecar {path} has invalid 'confidence' value: {e}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Success: delete the file and return
    try:
        path.unlink()
    except OSError:
        pass

    return data


def scope_sidecar_path(state_dir: Path) -> Path:
    return state_dir / ".test-scope-step3.json"


def ingest_scope_sidecar(state_dir: Path) -> dict | None:
    """Load optional scope sidecar into a dict; return None if missing.

    Does not delete the file (scope may be re-read). Malformed JSON → stderr warning, None.
    """
    path = scope_sidecar_path(state_dir)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"WARNING: failed to read scope sidecar {path}: {e}", file=sys.stderr)
        return None
    return data if isinstance(data, dict) else None


def log_override_to_stderr(flow_type: str) -> None:
    """Single-line stderr log for adoption tracking.

    Args:
        flow_type: The flow type that was overridden
    """
    print(f"[flows] override: user passed --flow-type={flow_type}", file=sys.stderr)
