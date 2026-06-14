"""Compat shim — implementation lives in scripts.diagnose.tools.log_analyzer."""

from __future__ import annotations

from scripts.diagnose.tools import log_analyzer as _impl

if __name__ == "__main__":
    _impl.main()
