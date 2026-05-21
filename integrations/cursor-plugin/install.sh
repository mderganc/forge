#!/usr/bin/env bash
set -euo pipefail

REPO="${REPO:-https://github.com/mderganc/forge}"
REF="${REF:-main}"
CURSOR_PLUGINS_DIR="${CURSOR_PLUGINS_DIR:-}"
CLAUDE_DIR="${CLAUDE_DIR:-}"
CODEX_DIR="${CODEX_DIR:-}"
SKIP_CLI_INSTALL="${SKIP_CLI_INSTALL:-0}"

info() { echo "[forge-install] $*"; }

show_graphify_status() {
  if [ -n "${FORGE_GRAPHIFY_COMMAND:-}" ]; then
    info "Graphify: available (FORGE_GRAPHIFY_COMMAND is set)"
  elif command -v graphify >/dev/null 2>&1; then
    info "Graphify: available (\`graphify\` on PATH)"
  else
    info "Graphify: not available (\`graphify\` not on PATH; FORGE_GRAPHIFY_COMMAND unset)"
  fi
}

ensure_cli() {
  if [ "$SKIP_CLI_INSTALL" = "1" ]; then
    info "Skipping CLI install (SKIP_CLI_INSTALL=1)."
    return
  fi
  if command -v forge >/dev/null 2>&1; then
    info "Found forge on PATH."
    return
  fi
  info "forge not found on PATH. Installing forge-next..."
  if command -v pipx >/dev/null 2>&1; then
    pipx install forge-next --force
    return
  fi
  python3 -m pip install --user --upgrade forge-next
  info "Installed via pip --user. Ensure ~/.local/bin is on PATH."
}

download_and_install() {
  info "Installing integrations via 'forge install'..."
  args=(install --all --repo-url "$REPO" --ref "$REF")
  if [ -n "$CURSOR_PLUGINS_DIR" ]; then args+=(--cursor-dir "$CURSOR_PLUGINS_DIR"); fi
  if [ -n "$CLAUDE_DIR" ]; then args+=(--claude-dir "$CLAUDE_DIR"); fi
  if [ -n "$CODEX_DIR" ]; then args+=(--codex-dir "$CODEX_DIR"); fi
  forge "${args[@]}"
}

ensure_cli
download_and_install

info "Done."
show_graphify_status
info "Graphify setup (after Graphify is available): forge graphify refresh in each app repo; see docs/graphify.md"
info "Next steps:"
echo "  1) Restart Cursor"
echo "  2) Run: forge:doctor"
echo "  3) Run: forge:evaluate"

info "Uninstall:"
echo "  forge uninstall --all"

