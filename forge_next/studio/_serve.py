"""Standalone Studio server process (spawned by `forge studio start --background`)."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> int:
    try:
        session_dir = Path(os.environ["FORGE_STUDIO_SESSION_DIR"])
        host = os.environ.get("FORGE_STUDIO_HOST", "127.0.0.1")
        port = int(os.environ["FORGE_STUDIO_PORT"])
        content_dir = session_dir / "content"
        state_dir = session_dir / "state"
        from forge_next.studio import server as studio_server

        studio_server.run_server(
            host=host, port=port, content_dir=content_dir, state_dir=state_dir
        )
    except Exception:
        import traceback

        traceback.print_exc(file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
