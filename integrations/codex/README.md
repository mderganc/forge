# Forge + Codex integration (v1)

This is a **skill pack** for Codex-style environments. Skills are thin wrappers that run the global `forge` CLI.

## Prerequisite

Install the CLI:

```bash
pipx install forge-next
```

Verify:

```bash
forge doctor
```

## Skills

Skill definitions live in `integrations/codex/skills/<skill-name>/SKILL.md` (OpenAI Codex layout: each skill is a folder with `SKILL.md` containing `name` and `description` in YAML frontmatter). They invoke `forge ...`.

This pack ships four skills: `forge-plan`, `forge-evaluate`, `forge-resume`, and `forge-status`. Other Forge workflows are available via the global `forge` CLI and Cursor/Claude integrations, not as Codex skills in v1.

### Default install location (via `forge install`)

By default, `forge install --codex` installs to:

- Windows: `%USERPROFILE%\.codex\skills\forge\`
- macOS/Linux/WSL: `~/.codex/skills/forge/`

Override with `forge install --codex-dir <path>`.

