param(
  [string]$Repo = "https://github.com/msderganc/forge",
  [string]$Ref = "main",
  [string]$PluginName = "forge",
  [string]$CursorPluginsDir = "",
  [string]$ClaudeDir = "",
  [string]$CodexDir = "",
  [switch]$AlsoWsl,
  [string]$WslDistro = "",
  [string]$WslClaudeDir = "",
  [string]$WslCodexDir = "",
  [switch]$SkipCliInstall
)

$ErrorActionPreference = "Stop"

function Write-Info([string]$msg) { Write-Host "[forge-install] $msg" }

function Show-GraphifyStatus {
  if ($env:FORGE_GRAPHIFY_COMMAND -and $env:FORGE_GRAPHIFY_COMMAND.Trim().Length -gt 0) {
    Write-Info "Graphify: available (FORGE_GRAPHIFY_COMMAND is set)"
  } elseif (Get-Command graphify -ErrorAction SilentlyContinue) {
    Write-Info "Graphify: available (`graphify` on PATH)"
  } else {
    Write-Info "Graphify: not available (`graphify` not on PATH; FORGE_GRAPHIFY_COMMAND unset)"
  }
}

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

if ($AlsoWsl) {
  Write-Info "Installing Claude/Codex into WSL as well..."

  $wslArgs = @()
  if ($WslDistro -and $WslDistro.Trim().Length -gt 0) { $wslArgs += @("-d", $WslDistro) }

  $envPairs = @()
  if ($WslClaudeDir -and $WslClaudeDir.Trim().Length -gt 0) { $envPairs += "CLAUDE_DIR=$WslClaudeDir" }
  if ($WslCodexDir -and $WslCodexDir.Trim().Length -gt 0) { $envPairs += "CODEX_DIR=$WslCodexDir" }

  $envPrefix = ""
  if ($envPairs.Count -gt 0) { $envPrefix = ($envPairs -join " ") + " " }

  $cmd = $envPrefix + "curl -fsSL https://raw.githubusercontent.com/msderganc/forge/$Ref/integrations/cursor-plugin/install.sh | bash"
  & wsl.exe @wslArgs "--" "bash" "-lc" $cmd
}

Write-Info "Done."
Show-GraphifyStatus
Write-Info "Graphify setup (after Graphify is available): forge graphify refresh in each app repo; see docs/graphify.md"
Write-Info "Next steps:"
Write-Host "  1) Restart Cursor"
Write-Host "  2) Run: forge:doctor"
Write-Host "  3) Run: forge:evaluate"

Write-Info "Uninstall:"
Write-Host "  forge uninstall --all"

