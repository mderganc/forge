# Forge Cursor plugin (commands)

This is a Cursor plugin that adds `forge:*` commands which run the global `forge` CLI.

## Prerequisite

Install the CLI:

```bash
pipx install forge-codex
```

## Local install (development)

Cursor plugins can be tested locally by copying/symlinking this folder into your Cursor local plugins directory, then reloading Cursor.

Folder to link/copy:

- `integrations/cursor-plugin/`

After installing, run:

- `forge:doctor`
- `forge:evaluate`

