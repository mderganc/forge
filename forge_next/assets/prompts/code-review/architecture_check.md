# Phase 3: Team Dispatch — Architecture Mode

Dispatch all reviewers to analyze design patterns, coupling, and SOLID principles.

## Review Target

**Mode:** Architecture Review
**Target:** {{TARGET}}
**Quick mode:** {{QUICK_MODE}}

## Team Assignments

{{TEAM_ASSIGNMENTS}}

## Instructions

### 1. Identify Scope

Read the target files/modules and build a mental model of:
- Module boundaries and public interfaces
- Dependency graph (what depends on what)
- Data flow patterns (how data moves through the system)
- Error propagation patterns

### 2. Dispatch Reviewers in Parallel

**Architect Review — SOLID Principles:**
- **S** (Single Responsibility): Does each module/class have one reason to change?
- **O** (Open/Closed): Can behavior be extended without modifying existing code?
- **L** (Liskov Substitution): Are subtypes truly substitutable for their base types?
- **I** (Interface Segregation): Are interfaces minimal and focused?
- **D** (Dependency Inversion): Do modules depend on abstractions, not concretions?

**Architect Review — Coupling & Cohesion:**
- Afferent coupling (Ca): How many modules depend on this one?
- Efferent coupling (Ce): How many modules does this one depend on?
- Instability (I = Ce / (Ca + Ce)): Is this module stable or volatile?
- Cohesion: Do the elements within each module belong together?

**Security Reviewer — Architectural Security:**
- Are trust boundaries clearly defined?
- Is authentication/authorization centralized or scattered?
- Are there privilege escalation paths?
- Is sensitive data properly compartmentalized?

**QA Reviewer — Testability:**
- Can components be tested in isolation?
- Are dependencies injectable?
- Are there hidden dependencies (globals, singletons)?
- Is the test infrastructure adequate for the architecture?

**Critic — Design Smells & Code Smells:**
- Run code smells assessment per `templates/code-smells.md`
- Priority smells: God Class, Shotgun Surgery, Inappropriate Intimacy (critical); Feature Envy, Long Method, Divergent Change (warning)
- For each smell: cite file:line, name the smell, state the consequence, recommend the specific refactoring
- Check for Dependency Structure Matrix issues: cyclic dependencies between modules, layering violations, coupling clusters

**Investigator — Dependency Analysis:**
- Map the full dependency graph
- Identify circular dependencies
- Check for dependency inversions (concrete depends on concrete)
- Evaluate third-party dependency health

**Doc-writer — Architecture Documentation:**
- Is the architecture documented?
- Do module-level docs explain the "why" not just the "what"?
- Are architectural decisions recorded (ADRs)?

### 3. Compile Findings

Collect all findings into a unified list with:
- Finding ID (F1, F2, ...)
- Source reviewer
- Severity: critical / warning / suggestion
- Title (one line)
- Detail (explanation with specific code references)

Record findings in state and proceed to deep dive.
