---
description: |
  Infer epic from repo state and drive Forge skills until ship-ready.
  Replaces resume and iterate.
---

# Forge Takeover

Shared runtime: [templates/workflow-skill-preamble.md](../../templates/workflow-skill-preamble.md).

<invoke cmd="forge takeover" />

| Argument | Purpose |
|----------|---------|
| `--issue` | GitHub issue number or URL |
| `--design` | Path to design spec |
| `--goal` | Override default ship-ready goal |
| `--cleanup` | Legacy state file cleanup (dry-run) |

Polls `.forge/.takeover-gates/*.json` between child skills. See `forge takeover --help`.

| Step | Phase | Gate |
|------|-------|------|
| 1 | Initialize + route | — (infers entry skill, writes route plan) |
| 2 | Upstream / continue | `upstream.json` — `status: pass` |
| 3 | Plan + evaluate (pre) | `plan.json` (`status: pass`) then `evaluate-pre.json` (`open_findings_total: 0`) |
| 4 | Implement + evaluate (post) | `implement.json` (`status: pass`) then `evaluate-post.json` (`open_findings_total: 0`) |
| 5 | Code review + test | `code-review.json` (`open_findings_total: 0`) then `test.json` (`failed: 0`) |
| 6 | Report | — (writes summary, hands off to ship) |

**Steps 2–5 await their gate**: each re-runs the *same* step until its gate file passes, then advances. Write the gate JSON described in the step output and re-invoke the same `--step` to re-check.
