# Phase 4: Deep Dive

The Investigator follows up on critical findings from the team dispatch phase.

## Current Findings

{{FINDINGS}}

## Your Task

### 1. Identify Critical Findings

From the findings above, select all findings with severity **critical** or **warning**
that need deeper investigation. These typically include:
- Security vulnerabilities that need proof-of-concept verification
- Architectural issues that may have wider impact than initially noted
- Logic errors that need call-chain tracing to confirm
- Performance concerns that need measurement

### 2. Investigator Deep Dive

For each critical finding, the Investigator should:

1. **Read the relevant code** — not just the flagged line, but the full context
   (the function, the caller, the callee, the error handler)
2. **Trace the data flow** — where does the input come from? Where does the output go?
3. **Check for similar patterns** — is this a one-off issue or a pattern repeated elsewhere?
4. **Assess blast radius** — if this finding is a real problem, what is the impact?
5. **Verify or refute** — does the deeper investigation confirm or dismiss the finding?

### 3. Update Findings

For each investigated finding:
- If confirmed: add detail with code references and impact assessment
- If refuted: mark as dismissed with explanation
- If escalated: upgrade severity with justification
- If new findings discovered: add them to the list

### 4. Summarize

Produce an updated findings list ready for the discussion phase.
Focus on actionable findings — things the author can and should fix.
