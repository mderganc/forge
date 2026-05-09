---
name: forge:doctor
description: Check Forge CLI install and environment for this repo.
---

## What to tell the user first

- **Doctor** verifies Python, paths, encoding, and Forge runtime directories—useful when something feels broken or after install/upgrade.
- Say you’ll report **pass/fail style checks** in normal language.

## What you run (agent)

Run `forge doctor` from the repo root (or `forge doctor --repo "<path>"` when reviewing another tree). Summarize whether the environment looks healthy.

## Exact CLI (reference)

- This repo: `forge doctor`
- Other repo: `forge doctor --repo "<path>"`
