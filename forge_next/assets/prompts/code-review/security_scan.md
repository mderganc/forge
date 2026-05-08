# Phase 3: Team Dispatch — Deep Mode (Security & Troubleshooting Scan)

Dispatch all reviewers to trace code paths and investigate specific areas.

## Review Target

**Mode:** Deep Troubleshooting Review
**Target:** {{TARGET}}
**Quick mode:** {{QUICK_MODE}}

## Team Assignments

{{TEAM_ASSIGNMENTS}}

## Instructions

### 1. Identify Investigation Areas

From the target and handoff context, identify:
- Specific code paths that need tracing
- Error conditions or failure modes to investigate
- Security-sensitive paths (auth, data handling, external input)
- Performance-critical paths

### 2. Dispatch Reviewers in Parallel

**Security Reviewer — Code Path Tracing:**
- Trace all paths where external input enters the system
- Follow data through validation, processing, storage, and output
- Check for injection points at every boundary crossing
- Verify authentication checks on every protected resource
- Map authorization decision points and verify they are correct
- Check for TOCTOU (time-of-check-time-of-use) vulnerabilities
- Review cryptographic usage (algorithms, key management, random generation)

**Investigator — Deep Code Path Analysis:**
- Trace the specific code paths related to the target issue
- Follow the call chain from entry point to data store and back
- Map error propagation: where do errors originate and where are they caught?
- Identify silent failure modes (swallowed exceptions, default values hiding errors)
- Check for race conditions in concurrent code paths
- Trace resource lifecycle (open/close, acquire/release)

**Architect — Structural Analysis:**
- Are the code paths well-structured and easy to follow?
- Is error handling consistent across the traced paths?
- Are there unnecessary indirections or overly complex control flow?
- Do the code paths respect module boundaries?

**QA Reviewer — Edge Case Analysis:**
- What happens with empty/null/zero inputs on these paths?
- What happens when external services are unavailable?
- What happens under concurrent access?
- What happens at boundary values (max int, empty string, huge payload)?

**Critic — Assumption Audit:**
- What assumptions do these code paths make?
- Which assumptions are validated and which are implicit?
- What happens when assumptions are violated?
- Are there defensive checks where assumptions might fail?

**Doc-writer — Documentation Gaps:**
- Are complex code paths adequately commented?
- Are error codes and failure modes documented?
- Is the expected behavior documented for edge cases?

### 3. Compile Findings

Collect all findings into a unified list with:
- Finding ID (F1, F2, ...)
- Source reviewer
- Severity: critical / warning / suggestion
- Title (one line)
- Detail (explanation with file:line references and code path traces)

Record findings in state and proceed to deep dive.
