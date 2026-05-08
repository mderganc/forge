# Forge Cursor plugin (commands)

This is a Cursor plugin that adds `forge:*` commands which run the global `forge` CLI.

## Prerequisite

Install the CLI:

```bash
pipx install forge-next
```

## Install (one-command)

### Windows (PowerShell)

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
irm https://raw.githubusercontent.com/mderganc/forge/main/integrations/cursor-plugin/install.ps1 | iex
```

### WSL / Linux / macOS

```bash
curl -fsSL https://raw.githubusercontent.com/mderganc/forge/main/integrations/cursor-plugin/install.sh | bash
```

This installs:
- Cursor plugin (`forge:*` commands)
- Claude command pack
- Codex skill pack

## Local install (development)

Cursor plugins can be tested locally by copying/symlinking this folder into your Cursor local plugins directory, then reloading Cursor.

Folder to link/copy:

- `integrations/cursor-plugin/`

After installing, run:

- `forge:doctor`
- `forge:evaluate`

