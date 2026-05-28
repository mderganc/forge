#!/usr/bin/env bash
# Install knip, madge (npm) and pyscn (pipx/uv) for Forge code-review / evaluate probes.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

if [[ "${FORGE_SKIP_STRUCTURAL_TOOLS:-}" == "1" ]]; then
  echo "FORGE_SKIP_STRUCTURAL_TOOLS=1 — skipping structural tools install."
  exit 0
fi

run_install() {
  if command -v forge >/dev/null 2>&1; then
    forge structural-tools install
    return $?
  fi
  if python3 -c "import forge_next.structural_tools" 2>/dev/null; then
    python3 -m forge_next.structural_tools install
    return $?
  fi
  echo "forge or forge_next package not found. Install with: pipx install forge-next" >&2
  return 1
}

run_install
