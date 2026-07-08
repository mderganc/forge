# Standards review baseline (Pass B)

Adapted from [mattpocock/skills code-review](https://github.com/mattpocock/skills/blob/main/skills/engineering/code-review/SKILL.md).

Fixed Fowler smell heuristics for **Pass B — Standards** review. Use alongside repo-documented standards (`CONTRIBUTING.md`, `CODING_STANDARDS.md`, `AGENTS.md`, `.cursor/rules/`, etc.).

For a broader catalog (architecture mode, systemic patterns), see `templates/code-smells.md`.

## Rules

1. **The repo overrides.** A documented repo standard always wins. Where the repo endorses something the baseline would flag, suppress the smell.
2. **Always a judgement call.** Each smell is a labelled heuristic ("possible Feature Envy"), never a hard violation.
3. **Skip tooling-enforced rules.** Do not flag what linters, formatters, or typecheckers already enforce.

## Smell baseline

Match each smell against the diff. Format: *what it is* → *how to fix*.

| Smell | Recognition | Fix |
|-------|-------------|-----|
| **Mysterious Name** | A function, variable, or type whose name doesn't reveal what it does or holds | Rename it; if no honest name comes, the design's murky |
| **Duplicated Code** | The same logic shape appears in more than one hunk or file in the change | Extract the shared shape, call it from both |
| **Feature Envy** | A method that reaches into another object's data more than its own | Move the method onto the data it envies |
| **Data Clumps** | The same few fields or params keep travelling together (a type wanting to be born) | Bundle them into one type, pass that |
| **Primitive Obsession** | A primitive or string standing in for a domain concept that deserves its own type | Give the concept its own small type |
| **Repeated Switches** | The same `switch`/`if`-cascade on the same type recurs across the change | Replace with polymorphism, or one map both sites share |
| **Shotgun Surgery** | One logical change forces scattered edits across many files in the diff | Gather what changes together into one module |
| **Divergent Change** | One file or module is edited for several unrelated reasons | Split so each module changes for one reason |
| **Speculative Generality** | Abstraction, parameters, or hooks added for needs the spec doesn't have | Delete it; inline back until a real need shows |
| **Message Chains** | Long `a.b().c().d()` navigation the caller shouldn't depend on | Hide the walk behind one method on the first object |
| **Middle Man** | A class or function that mostly just delegates onward | Cut it, call the real target direct |
| **Refused Bequest** | A subclass or implementer that ignores or overrides most of what it inherits | Drop the inheritance, use composition |

## During code review

1. Scan repo for documented standards first; cite file + rule for hard violations.
2. Apply this baseline for judgement-call smells in changed code.
3. Distinguish Pass B findings from Pass A (spec/intent) — do not merge or rerank across axes.
