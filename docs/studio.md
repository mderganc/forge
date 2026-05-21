# Forge Studio (agent / runtime only)

> **This is not a Forge workflow.** Users do not install or run Studio. It is internal transport for **develop** and **plan** visual gates (browser URL during gate questions).

Operational guide for agents: [`templates/studio.md`](../templates/studio.md).

## Summary

- Localhost HTTP server bundled in `forge-next` (Python stdlib).
- Sessions live under `.codex/forge/studio/<session-id>/`.
- CLI: `forge studio start|stop|events|status|push|approve|unlock` (omitted from `forge --help`).
- Each screen: **design notes**, **probing questions**, gate UI, optional freeform feedback.
- Session log: `.codex/forge/memory/studio-log.md` (`{{STUDIO_LOG}}`).
- Locked references: `.codex/forge/studio/approved/` + `studio-approved-index.md` (`{{STUDIO_APPROVED}}`).
- Event types: `click`, `submit`, `probe-response`, `probes-submit`, `feedback`, `approve`, `unlock`, `done`.
- Not listed in `integrations/spec/commands.json` or README workflows.

## Distinction from Graphify

Graphify maps the codebase. Studio shows HTML mockups during workflow gates. Neither replaces the other.
