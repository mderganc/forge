"""Merge Forge delegation instructions into ~/.codex/config.toml for OpenAI Codex."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import tomlkit

from forge_next.graphify_policy import FORGE_DEVELOPER_INSTRUCTIONS_BODY

# Re-export for tests and README parity.
__all__ = ["FORGE_DEVELOPER_INSTRUCTIONS_BODY", "apply_codex_agents_config"]


def default_codex_config_path() -> Path:
    home = Path(os.environ.get("USERPROFILE") or str(Path.home()))
    return home / ".codex" / "config.toml"


def _normalized_instructions(value: object | None) -> str | None:
    if value is None:
        return None
    return str(value).strip()


def apply_codex_agents_config(
    config_path: Path,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> int:
    """Merge or set root-level developer_instructions. Returns process exit code."""
    config_path = config_path.expanduser().resolve()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    raw = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    try:
        doc = tomlkit.parse(raw) if raw.strip() else tomlkit.document()
    except Exception as exc:
        print(f"Could not parse {config_path}: {exc}", file=sys.stderr)
        return 1

    target = FORGE_DEVELOPER_INSTRUCTIONS_BODY
    existing = _normalized_instructions(doc.get("developer_instructions"))

    if existing == target:
        print(f"Already configured ({config_path}).")
        return 0

    if existing is not None and existing != target and not force:
        print(
            f"Refusing to overwrite existing developer_instructions in {config_path}.\n"
            "Re-run with --force to replace it with the Forge delegation text.",
            file=sys.stderr,
        )
        return 1

    doc["developer_instructions"] = target

    out = tomlkit.dumps(doc)
    if not dry_run:
        config_path.write_text(out, encoding="utf-8", newline="\n")
        action = "Updated" if existing else "Wrote"
        print(f"{action} {config_path}")
    else:
        print(f"Would write {config_path} (dry-run; no changes).")

    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="codex-agents",
        description=(
            "Add Forge delegation instructions to Codex config.toml so forge:* skills may "
            "dispatch sub-agents without extra user wording (see README OpenAI Codex section)."
        ),
    )
    p.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config.toml (default: ~/.codex/config.toml)",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing developer_instructions value with the Forge snippet.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without writing the file.",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    args = build_parser().parse_args(argv)
    path = Path(args.config).expanduser() if args.config else default_codex_config_path()
    rc = apply_codex_agents_config(path, force=args.force, dry_run=args.dry_run)
    raise SystemExit(rc)
