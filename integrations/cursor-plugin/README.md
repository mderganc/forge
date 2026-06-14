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

To also install Claude/Codex wrappers into your WSL home:

```powershell
$env:AlsoWsl = "1"
irm https://raw.githubusercontent.com/mderganc/forge/main/integrations/cursor-plugin/install.ps1 | iex -AlsoWsl
```

### WSL / Linux / macOS

```bash
curl -fsSL https://raw.githubusercontent.com/mderganc/forge/main/integrations/cursor-plugin/install.sh | bash
```

This installs:
- Cursor plugin (`forge:*` commands)
- Claude command pack (+ `forge claude-graphify` hooks when using `forge install`)
- Codex skill pack (+ `forge codex-agents` policy when using `forge install`)

When the repo has `graphify-out/`, workflow commands include **Hard rule — Graphify**. Refresh runs at **ship** (`forge ship --step 1`); workflow steps do not print per-step GRAPHIFY banners. See [`docs/graphify.md`](../../docs/graphify.md).

Uninstall:

```bash
forge uninstall --all
```

## Local install (development)

Cursor plugins can be tested locally by copying/symlinking this folder into your Cursor local plugins directory, then reloading Cursor.

Folder to link/copy:

- `integrations/cursor-plugin/`

After installing, run (slash picker should show `/forge:doctor`, `/forge:evaluate`, etc.):

- `/forge:doctor`
- `/forge:evaluate`

Command files live in `commands/` as `<subcommand>.md` (not `forge-<subcommand>.md`). The plugin namespace is `forge`.

**Aliases:** Cursor’s plugin command schema does not document alias fields. This bundle does not provide `/f:<subcommand>` or bare `/diagnose`; use `/forge:<subcommand>`.

