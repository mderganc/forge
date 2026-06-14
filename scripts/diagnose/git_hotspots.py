"""Compat shim — implementation lives in scripts.diagnose.tools.git_hotspots."""

from __future__ import annotations

from scripts.diagnose.tools import git_hotspots as _impl

if __name__ == "__main__":
    _impl.main()
