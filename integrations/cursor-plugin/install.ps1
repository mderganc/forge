param(
  [string]$Repo = "https://github.com/mderganc/forge",
  [string]$Ref = "main",
  [string]$PluginName = "forge",
  [string]$CursorPluginsDir = "",
  [string]$ClaudeDir = "",
  [string]$CodexDir = "",
  [switch]$SkipCliInstall
)

$ErrorActionPreference = "Stop"

function Write-Info([string]$msg) { Write-Host "[forge-install] $msg" }

function Ensure-Cli {
  if ($SkipCliInstall) {
    Write-Info "Skipping CLI install (SkipCliInstall set)."
    return
  }

  if (Get-Command forge -ErrorAction SilentlyContinue) {
    Write-Info "Found forge on PATH."
    return
  }

  Write-Info "forge not found on PATH. Installing forge-next..."

  # Prefer pipx if available; fall back to pip --user.
  if (Get-Command pipx -ErrorAction SilentlyContinue) {
    pipx install forge-next --force
    return
  }

  if (Get-Command py -ErrorAction SilentlyContinue) {
    py -m pip install --user --upgrade forge-next
  } elseif (Get-Command python -ErrorAction SilentlyContinue) {
    python -m pip install --user --upgrade forge-next
  } else {
    throw "Python not found. Install Python 3.10+ or install pipx, then re-run."
  }

  Write-Info "Installed via pip --user. You may need to restart your terminal so 'forge' is on PATH."
}

Ensure-Cli

Write-Info "Installing integrations via 'forge install'..."
$args = @("install", "--all", "--repo-url", $Repo, "--ref", $Ref)
if ($CursorPluginsDir -and $CursorPluginsDir.Trim().Length -gt 0) { $args += @("--cursor-dir", $CursorPluginsDir) }
if ($ClaudeDir -and $ClaudeDir.Trim().Length -gt 0) { $args += @("--claude-dir", $ClaudeDir) }
if ($CodexDir -and $CodexDir.Trim().Length -gt 0) { $args += @("--codex-dir", $CodexDir) }

& forge @args

Write-Info "Done."
Write-Info "Next steps:"
Write-Host "  1) Restart Cursor"
Write-Host "  2) Run: forge:doctor"
Write-Host "  3) Run: forge:evaluate"

