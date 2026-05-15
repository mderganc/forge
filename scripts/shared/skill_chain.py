"""Canonical skill-chain mapping for inter-skill handoff menus.

Used by build_skill_handoff_menu() in orchestrator.py at every skill's
final-step. The default is the conventional next; alternatives let the user
pick a different path without remembering the flag syntax.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SkillTransition:
    """A skill's default next command and alternatives."""
    default: str | None              # "evaluate --mode pre" etc; None = terminal
    alternatives: list[str] = field(default_factory=list)


SKILL_CHAIN: dict[str, SkillTransition] = {
    "iterate":     SkillTransition(None,                   ["diagnose", "plan", "evaluate --mode pre", "implement"]),
    "develop":     SkillTransition("plan",                 ["evaluate --mode pre", "implement", "diagnose"]),
    "plan":        SkillTransition("evaluate --mode pre",  ["implement", "develop", "code-review"]),
    "evaluate":    SkillTransition("implement",            ["plan", "evaluate --mode review", "test"]),
    "implement":   SkillTransition("code-review",          ["test", "evaluate --mode post", "diagnose"]),
    "code-review": SkillTransition("test",                 ["implement", "diagnose", "evaluate --mode review"]),
    "test":        SkillTransition("diagnose",             ["test --mode flows", "code-review", "implement"]),
    "diagnose":    SkillTransition(None,                   ["plan", "implement", "develop"]),
}


# Optional descriptions for each command, rendered as "(why)" inline in the menu
COMMAND_DESCRIPTIONS: dict[str, str] = {
    "iterate":               "meta-workflow: diagnose→plan→evaluate→implement→review→test loops",
    "plan":                  "create the implementation plan",
    "evaluate --mode pre":   "review the plan before implementing",
    "evaluate --mode post":  "review what was implemented against the plan",
    "evaluate --mode review": "full team review of the implementation",
    "implement":             "execute the plan",
    "code-review":           "deep code review of the changes",
    "test":                  "run tests + coverage",
    "test --mode flows":     "author end-to-end mock flows",
    "develop":               "investigate, brainstorm, and design before planning (use after diagnose when solution space is still open)",
    "diagnose":              "root-cause analysis on observed issues",
}
