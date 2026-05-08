# User Questions Protocol

Defines how the workflow skills ask the user for decisions in Codex.

## Core Principle

Use the lightest interaction that fits the situation:
- In normal Codex turns, ask one concise plain-text question and wait for the reply.
- If the environment explicitly supports a structured picker, you may use it, but do not depend on it.

## When to Ask the User

- Approval gates
- Mode selection
- Finding triage
- Cross-skill transitions
- Session conflicts
- Scope confirmation

## When Not to Ask

- Information-only output
- Agent-to-agent communication
- Continuation directives that should proceed automatically

## Format

When a prompt says to ask the user, present:
1. One short question
2. Two to four concrete options in prose
3. A brief note on what each option means if needed

Example:

`Approve the implementation plan? Options: approve and continue to implement; revise the plan; simplify scope; reject for now.`

## Rules

1. Keep the question actionable.
2. Prefer mutually exclusive options unless multiple selections are genuinely needed.
3. If the user needs to choose from many items, narrow the list first.
4. Record the user's answer in the relevant memory file before continuing.
