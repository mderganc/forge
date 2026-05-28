# Install knip, madge (npm) and pyscn (pipx/uv) for Forge code-review / evaluate probes.
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $Root

if ($env:FORGE_SKIP_STRUCTURAL_TOOLS -eq "1") {
    Write-Host "FORGE_SKIP_STRUCTURAL_TOOLS=1 — skipping structural tools install."
    exit 0
}

function Invoke-StructuralInstall {
    if (Get-Command forge -ErrorAction SilentlyContinue) {
        forge structural-tools install
        return $LASTEXITCODE
    }
    try {
        python -c "import forge_next.structural_tools" 2>$null
        if ($LASTEXITCODE -eq 0) {
            python -m forge_next.structural_tools install
            return $LASTEXITCODE
        }
    } catch {
        # fall through
    }
    Write-Error "forge or forge_next package not found. Install with: pipx install forge-next"
    return 1
}

$code = Invoke-StructuralInstall
exit $code
