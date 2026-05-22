"""Barrier analysis sidecar for diagnose."""

from __future__ import annotations

from pathlib import Path

from scripts.diagnose.diagnose_registers import load_sidecar

FILENAME = ".diagnose-barriers.json"
_DEFAULT_LAYERS = (
    "type_system",
    "unit_tests",
    "integration_tests",
    "code_review",
    "ci_checks",
    "monitoring",
)


def register_path(state_dir: Path) -> Path:
    return state_dir / FILENAME


def load_register(path: Path) -> dict | None:
    return load_sidecar(path)


def summarize(data: dict | None) -> str:
    if not data or not isinstance(data.get("layers"), list):
        return "(No barrier analysis sidecar loaded)"
    return f"**{len(data['layers'])}** defense layers analyzed"


def validate(
    data: dict | None,
    *,
    path: Path | None = None,
    required: bool = False,
    min_layers: int = 3,
) -> tuple[bool, list[str]]:
    issues: list[str] = []
    label = str(path) if path else FILENAME

    if data is None:
        if required:
            issues.append(
                f"No barrier analysis at {label}. "
                "Create `.diagnose-barriers.json` when safety/compliance profile applies."
            )
            return False, issues
        return True, issues

    layers = data.get("layers")
    if not isinstance(layers, list) or len(layers) < min_layers:
        issues.append(
            f"Barrier analysis needs at least {min_layers} entries in 'layers'."
        )
        return False, issues

    for idx, layer in enumerate(layers):
        if not isinstance(layer, dict):
            issues.append(f"Barrier layer {idx + 1} is not an object.")
            continue
        name = layer.get("name") or layer.get("layer")
        if not name or not str(name).strip():
            issues.append(f"Barrier layer {idx + 1} missing 'name'.")
        for field in ("exists", "active", "detected", "failure_mode"):
            if field not in layer:
                issues.append(
                    f"Barrier {name or idx + 1}: missing '{field}' (true/false + reason)."
                )

    return len(issues) == 0, issues
