#!/usr/bin/env python3
"""Copy repo templates/*.md into forge_next/assets/templates/ for wheel packaging."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "templates"
DST = REPO_ROOT / "forge_next" / "assets" / "templates"


def main() -> int:
    if not SRC.is_dir():
        print(f"ERROR: missing source templates dir: {SRC}", file=sys.stderr)
        return 1

    copied = 0
    for path in sorted(SRC.rglob("*.md")):
        rel = path.relative_to(SRC)
        out = DST / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, out)
        copied += 1

    # Remove packaged templates removed from source (sync is mirror, not append-only).
    for path in sorted(DST.rglob("*.md")):
        rel = path.relative_to(DST)
        if not (SRC / rel).is_file():
            path.unlink()
            print(f"Removed stale packaged template: {rel}")

    print(f"Synced {copied} template file(s) to {DST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
