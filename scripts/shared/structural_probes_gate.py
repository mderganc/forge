"""Structural probe status banners, user gates, and step-entry validation."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from scripts.shared.workflow_gate import validate_override_bypass

PROBE_GATE_SIDECAR = ".structural-probes-gate.json"
STATUS_OK = "OK"
STATUS_FAILED = "FAILED"
STATUS_SKIPPED = "SKIPPED"
STATUS_DEGRADED = "DEGRADED"
STATUS_DEFERRED = "DEFERRED"
NON_OK_STATUSES = frozenset({STATUS_FAILED, STATUS_SKIPPED, STATUS_DEGRADED, STATUS_DEFERRED})


def probe_gate_sidecar_path(state_dir: Path) -> Path:
    return Path(state_dir) / PROBE_GATE_SIDECAR


def is_noninteractive() -> bool:
    if os.environ.get("FORGE_NONINTERACTIVE", "").strip().lower() in ("1", "true", "yes", "on"):
        return True
    return os.environ.get("CI", "").strip().lower() in ("1", "true", "yes")


def _probe_banner_bar() -> str:
    return ("=" * 60) if os.environ.get("FORGE_ASCII") == "1" else ("━" * 60)


def _format_probe_status_line(label: str, value: str) -> str:
    return f"**{label}:** {value}"


def _format_probe_optional_lines(
    *,
    reason: str = "",
    policy: str = "",
    sidecar: Path | str | None = None,
    sidecar_label: str = "Sidecar",
) -> list[str]:
    lines: list[str] = []
    if reason:
        lines.append(_format_probe_status_line("Reason", reason))
    if policy:
        lines.append(_format_probe_status_line("Policy", policy))
    if sidecar:
        lines.append(f"**{sidecar_label}:** `{sidecar}`")
    return lines


def format_loud_probe_status_banner(
    status: str,
    *,
    reason: str = "",
    sidecar: Path | str | None = None,
    policy: str = "",
) -> str:
    """Always print — never return empty for a probe step."""
    bar = _probe_banner_bar()
    lines = [
        bar,
        f"STRUCTURAL PROBES — {status}",
        bar,
        "",
        _format_probe_status_line("Status", status),
    ]
    lines.extend(
        _format_probe_optional_lines(reason=reason, policy=policy, sidecar=sidecar)
    )
    lines.extend(["", ""])
    return "\n".join(lines)


def format_probe_gate_body(
    status: str,
    *,
    reason: str = "",
    sidecar: Path | str | None = None,
    gate_sidecar: Path | str | None = None,
) -> str:
    """Pause block when probes did not reach OK."""
    if status == STATUS_OK:
        return ""
    bar = _probe_banner_bar()
    lines = [
        "",
        bar,
        "STRUCTURAL PROBES GATE",
        bar,
        "",
        "Structural probes did not complete with status **OK**. This step is **paused**",
        "until you choose how to proceed.",
        "",
        _format_probe_status_line("Probe status", status),
    ]
    lines.extend(
        _format_probe_optional_lines(
            reason=reason,
            sidecar=sidecar,
            sidecar_label="Probe sidecar",
        )
    )
    if gate_sidecar:
        lines.append(f"**Gate sidecar:** `{gate_sidecar}`")
    lines.extend(
        [
            "",
            "**Choose one:**",
            "  1. Retry probes (re-run this forge step)",
            "  2. Continue with override (record reason in gate sidecar / CLI flags)",
            "  3. Defer full pass to `forge ship --step 1`",
            "  4. Stop (`forge takeover` to resume later)",
            "",
            "Do **not** run the next forge step until you reply or clear the gate.",
            "",
        ]
    )
    multiselect = build_probe_gate_multiselect(status, reason=reason, sidecar=sidecar)
    lines.append("```handoff-multiselect")
    lines.append(json.dumps(multiselect, indent=2))
    lines.append("```")
    lines.append("")
    print(
        f"FORGE_STRUCTURAL_PROBES: {status} — {reason or 'see gate block'}",
        file=sys.stderr,
    )
    return "\n".join(lines)


def build_probe_gate_multiselect(
    status: str,
    *,
    reason: str = "",
    sidecar: Path | str | None = None,
) -> dict[str, Any]:
    return {
        "type": "forge_probe_gate_multiselect",
        "probe_status": status,
        "reason": reason,
        "sidecar": str(sidecar) if sidecar else None,
        "options": [
            {"id": "retry", "label": "Retry probes (re-run this step)"},
            {"id": "override", "label": "Continue with override reason"},
            {"id": "defer_ship", "label": "Defer full pass to forge ship"},
            {"id": "stop", "label": "(stop) — pause until takeover"},
        ],
        "default_option_ids": ["retry"],
    }


def write_probe_gate_sidecar(
    state_dir: Path,
    *,
    probe_status: str,
    reason: str = "",
    probe_sidecar: Path | str | None = None,
    gate_state: str = "pending",
) -> Path:
    path = probe_gate_sidecar_path(state_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "probe_status": probe_status,
        "probe_reason": reason,
        "probe_sidecar": str(probe_sidecar) if probe_sidecar else None,
        "gate_state": gate_state,
        "user_choice": None,
        "override_reason": None,
        "override_follow_up": None,
        "decided_at": None,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_probe_gate_sidecar(state_dir: Path) -> dict[str, Any] | None:
    path = probe_gate_sidecar_path(state_dir)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def probe_gate_is_pending(state_dir: Path) -> bool:
    gate = load_probe_gate_sidecar(state_dir)
    if gate is None:
        return False
    return gate.get("gate_state") == "pending" and gate.get("probe_status") in NON_OK_STATUSES


def validate_probe_gate_at_step_entry(
    state_dir: Path,
    *,
    allow_incomplete: bool = False,
    override_reason: str = "",
    override_follow_up: str = "",
) -> tuple[bool, str]:
    """Block step N+1 when probe gate is still pending."""
    gate = load_probe_gate_sidecar(state_dir)
    if gate is None:
        return True, ""

    if gate.get("gate_state") in ("cleared", "overridden", "deferred_to_ship"):
        return True, ""

    ok_override, override_msg = validate_override_bypass(
        allow_incomplete,
        override_reason,
        override_follow_up,
        reason_field_label="--structural-probes-override-reason",
        follow_up_field_label="--structural-probes-override-follow-up",
        success_message="Structural probes gate OVERRIDDEN.",
    )
    if allow_incomplete and ok_override:
        write_probe_gate_sidecar(
            state_dir,
            probe_status=str(gate.get("probe_status") or STATUS_FAILED),
            reason=str(gate.get("probe_reason") or ""),
            gate_state="overridden",
        )
        return True, override_msg

    if gate.get("gate_state") == "pending":
        status = gate.get("probe_status", "?")
        reason = gate.get("probe_reason", "")
        body = format_probe_gate_body(
            str(status),
            reason=str(reason),
            sidecar=gate.get("probe_sidecar"),
            gate_sidecar=probe_gate_sidecar_path(state_dir),
        )
        if is_noninteractive():
            return (
                False,
                body
                + "\n\nCI/non-interactive mode: fix probes or pass "
                "`--allow-structural-probes-incomplete` with override reason/follow-up.",
            )
        return False, body

    return True, ""


def finalize_probe_outcome(
    state_dir: Path,
    *,
    status: str,
    reason: str = "",
    sidecar: Path | None = None,
    policy: str = "",
    advisory: bool = False,
) -> tuple[str, bool]:
    """Return (extra body to append, require_confirmation).

    Advisory mode (plan step 2 baseline) prints the banner without a pending gate.
    """
    banner = format_loud_probe_status_banner(
        status, reason=reason, sidecar=sidecar, policy=policy
    )
    if status == STATUS_OK:
        gate_path = probe_gate_sidecar_path(state_dir)
        if gate_path.is_file():
            gate_path.unlink(missing_ok=True)
        return banner, False

    if advisory:
        note = (
            "\n_Advisory only — architecture continues without confirmation "
            "(plan step 2 baseline)._\n"
        )
        return banner + note, False

    gate_path = write_probe_gate_sidecar(
        state_dir,
        probe_status=status,
        reason=reason,
        probe_sidecar=sidecar,
        gate_state="pending",
    )
    gate_body = format_probe_gate_body(
        status,
        reason=reason,
        sidecar=sidecar,
        gate_sidecar=gate_path,
    )
    return banner + gate_body, True


def iter_probe_gate_state_dirs(repo_root: Path) -> list[Path]:
    """State directories that may contain `.structural-probes-gate.json`."""
    from scripts.shared.runtime_layout import runtime_root_candidates

    seen: set[str] = set()
    dirs: list[Path] = []
    for root in runtime_root_candidates(repo_root):
        if not root.is_dir():
            continue
        candidates = [
            root / "state",
            root / "memory",
            *root.glob("sessions/*"),
            *root.glob("sessions/*/sidecars"),
        ]
        for path in candidates:
            if not path.is_dir():
                continue
            key = str(path.resolve())
            if key in seen:
                continue
            seen.add(key)
            dirs.append(path)
    return dirs


def collect_probe_gate_hints(repo_root: Path) -> list[str]:
    """Human-readable probe gate lines for forge status / doctor."""
    hints: list[str] = []
    for state_dir in iter_probe_gate_state_dirs(repo_root):
        gate = load_probe_gate_sidecar(state_dir)
        if gate is None:
            continue
        gate_state = gate.get("gate_state", "?")
        status = gate.get("probe_status", "?")
        rel = state_dir
        try:
            rel = state_dir.relative_to(repo_root)
        except ValueError:
            rel = state_dir
        if gate_state == "pending":
            hints.append(
                f"Structural probe gate PENDING ({status}) — {rel} "
                "(retry, override, defer to ship, or stop)"
            )
        elif gate_state == "deferred_to_ship":
            hints.append(
                f"Structural probes deferred to ship ({status}) — {rel}"
            )
    return hints


def find_deferred_to_ship_gate_dirs(repo_root: Path) -> list[Path]:
    """State dirs whose probe gate was deferred to ``forge ship``."""
    deferred: list[Path] = []
    for state_dir in iter_probe_gate_state_dirs(repo_root):
        gate = load_probe_gate_sidecar(state_dir)
        if gate is None:
            continue
        if gate.get("gate_state") == "deferred_to_ship":
            deferred.append(state_dir)
    return deferred


def run_ship_deferred_probe_passes(repo_root: Path) -> list[str]:
    """Run full structural probes for gates deferred to ship; return status lines."""
    if os.environ.get("FORGE_SKIP_STRUCTURAL_TOOLS", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    ):
        return ["Structural probes skipped (FORGE_SKIP_STRUCTURAL_TOOLS=1)."]

    from scripts.shared.structural_probes import (
        probe_payload_exit_code,
        run_probes_from_state_dir,
        sidecar_path,
    )

    lines: list[str] = []
    for state_dir in find_deferred_to_ship_gate_dirs(repo_root):
        try:
            rel = state_dir.relative_to(repo_root)
        except ValueError:
            rel = state_dir
        print(
            f"forge ship: running deferred structural probes for {rel}…",
            file=sys.stderr,
            flush=True,
        )
        payload = run_probes_from_state_dir(repo_root, state_dir)
        status, reason = resolve_probe_status_from_payload(payload)
        sc = sidecar_path(state_dir)
        if status == STATUS_OK:
            write_probe_gate_sidecar(
                state_dir,
                probe_status=status,
                reason=reason,
                probe_sidecar=sc,
                gate_state="cleared",
            )
            lines.append(f"Deferred probes OK — {rel}")
        else:
            write_probe_gate_sidecar(
                state_dir,
                probe_status=status,
                reason=reason,
                probe_sidecar=sc,
                gate_state="pending",
            )
            lines.append(
                f"Deferred probes {status} — {rel}: {reason or 'see gate sidecar'}"
            )
            if probe_payload_exit_code(payload):
                print(
                    f"FORGE_STRUCTURAL_PROBES: deferred ship pass {status} — {rel}",
                    file=sys.stderr,
                )
    if not lines:
        return []
    return lines


def _explicit_payload_status(payload: dict[str, Any]) -> tuple[str, str] | None:
    explicit = str(payload.get("status") or "").strip().upper()
    if explicit in {STATUS_OK, *NON_OK_STATUSES}:
        return explicit, str(payload.get("status_reason") or payload.get("reason") or "")
    return None


def _status_when_no_probes(payload: dict[str, Any]) -> tuple[str, str]:
    if payload.get("deferred_to_ship"):
        return STATUS_DEFERRED, str(payload.get("status_reason") or "deferred to ship")
    return STATUS_SKIPPED, str(payload.get("status_reason") or "no probes ran")


def _status_from_probe_rows(
    probes: list[Any],
    payload: dict[str, Any],
) -> tuple[str, str]:
    failed = [p for p in probes if p.get("status") == "fail"]
    if failed:
        return STATUS_FAILED, f"{len(failed)} probe(s) failed"

    skipped = [p for p in probes if p.get("status") == "skip"]
    if len(skipped) == len(probes):
        return STATUS_SKIPPED, "all probes skipped"

    if payload.get("degraded"):
        return STATUS_DEGRADED, str(payload.get("status_reason") or "partial scope")
    if payload.get("deferred_to_ship"):
        return STATUS_DEFERRED, str(payload.get("status_reason") or "deferred to ship")

    return STATUS_OK, ""


def resolve_probe_status_from_payload(payload: dict[str, Any] | None) -> tuple[str, str]:
    """Derive top-level status from probe run payload."""
    if payload is None:
        return STATUS_SKIPPED, "no probe payload"

    explicit = _explicit_payload_status(payload)
    if explicit is not None:
        return explicit

    probes = payload.get("probes") or []
    if not probes:
        return _status_when_no_probes(payload)

    return _status_from_probe_rows(probes, payload)
