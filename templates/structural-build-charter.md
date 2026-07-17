# Structural build charter

Standing rules for **design, plan, and implement** — the same lenses jscn/pyscn (and related probes) measure later. Follow these while shaping and writing code; probes and code-review verify compliance.

Aligned with probe defaults: **`--min-complexity=15`**.

## Lenses

| Lens | Rule |
|------|------|
| **Complexity** | Keep new/changed functions under the complexity budget. Split or extract before landing hot code. |
| **Clones** | Search for an existing helper before copying logic. Extract the shared shape on the second duplication. |
| **CFG / dead code** | No unreachable branches, stub arms, or “just in case” paths that never execute. |
| **Cycles** | New imports must not create or worsen circular dependencies. Prefer the architecture’s dependency direction. |
| **Unused exports** | Do not leave unused public surfaces. No speculative exports “for later.” |

## Build vs review

| Context | What to do |
|---------|------------|
| **design / plan / implement** | Apply this charter. Solo parent or dispatched agents — same rules. |
| **code-review / evaluate** | Probes + Pass B / eight Civil Learning agents **verify**; they do not replace upstream teaching. |

See also: `templates/structural-quality-probes.md` (tool triage), `templates/workflow-skill-preamble.md` § Simplicity (YAGNI).
