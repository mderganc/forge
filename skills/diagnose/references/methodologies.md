---
title: "Diagnostic Methodology Deep Reference"
topics: [root-cause-analysis, FMEA, Kepner-Tregoe, Cynefin, Bayesian-reasoning, MECE, Fishbone, 5-Whys, fault-tree, Swiss-Cheese, Bulletproof-Problem-Solving]
date_created: "2026-04-02"
version: "1"
purpose: "Comprehensive reference for all RCA and problem-solving methodologies used by the diagnose skill"
audience: "AI agents running the diagnose skill"
status: "active"
---

# Diagnostic Methodology Deep Reference

> **Summary**: Reference guide covering 20 diagnostic and root-cause analysis methodologies adapted for software engineering. Includes Kepner-Tregoe, Cynefin, Fishbone, Bulletproof Problem Solving, 5 Whys, FMEA, Bayesian reasoning, Fault Tree Analysis, Swiss Cheese Model, and more.
>
> **Scope**: In — methodology descriptions, software-specific adaptations, when to use each. Out — general project management, non-diagnostic frameworks.
>
> **Assumptions**: Reader is an AI agent with access to code, git, and shell tools.

## 1. Kepner-Tregoe Problem Analysis

**Origin**: Charles Kepner & Benjamin Tregoe, 1958. Rational process for complex problem solving.

**Core technique**: IS/IS-NOT specification — systematically narrow the problem by defining what IS affected vs what IS NOT, finding the **distinction** (what's unique about the IS), and identifying the **change** that caused it.

**Four quadrants**:
1. **WHAT**: Object, defect, unit — what specific thing is failing?
2. **WHERE**: Geographic, on unit, in process — where exactly?
3. **WHEN**: Calendar time, in lifecycle, in pattern — when does/doesn't it happen?
4. **EXTENT**: How many, how much, trending — what's the scope?

**Software application**:
- WHAT: Which component, endpoint, function, class?
- WHERE: Which environment, server, browser, OS? Which file/line?
- WHEN: After deploy? Under load? Specific time? After specific user action?
- EXTENT: All users or subset? All requests or intermittent? Increasing?

**Key insight**: The distinction between IS and IS-NOT points to the cause. If it fails in prod but not staging, the distinction IS the cause direction.

---

## 2. Cynefin Framework

**Origin**: Dave Snowden, 1999. Complexity categorization for decision-making.

**Four domains**:

### Clear (formerly Simple/Obvious)
- Cause-effect is obvious to everyone
- Best practice applies
- **Strategy**: Sense → Categorize → Respond
- **Software**: Known bug pattern, documented fix exists, standard config error
- **Danger**: Complacency — treating complicated problems as clear

### Complicated
- Cause-effect is discoverable but requires expertise/analysis
- Good practice applies (multiple valid approaches)
- **Strategy**: Sense → Analyze → Respond
- **Software**: Performance issue needing profiling, multi-factor bug, integration problem
- **This is where most software bugs live**

### Complex
- Cause-effect only visible in retrospect, emergent behavior
- Novel practice — probe, learn, adapt
- **Strategy**: Probe → Sense → Respond
- **Software**: Distributed system failures, race conditions, emergent performance degradation, cascading failures, heisenbugs
- **Key**: Run safe-to-fail experiments. Add instrumentation. Observe patterns.

### Chaotic
- No perceivable cause-effect. System in crisis.
- Novel practice — stabilize first
- **Strategy**: Act → Sense → Respond
- **Software**: Production outage, data corruption in progress, security breach
- **Key**: Stop the bleeding first. Rollback, circuit-break, disable features. Diagnose after stabilization.

### Disorder (center)
- Don't know which domain you're in
- **Strategy**: Gather information to classify, then act per domain

---

## 3. Fishbone / Ishikawa Diagram

**Origin**: Kaoru Ishikawa, 1968. Structured cause categorization.

**Traditional 6M categories**: Manpower, Methods, Machines, Materials, Measurement, Mother Nature (Environment)

**Software-adapted categories**:

| Category | Examples |
|----------|----------|
| **CODE** | Logic errors, off-by-one, null deref, type coercion, race conditions, deadlocks, algorithmic errors, wrong state machine transitions |
| **CONFIG** | Env vars wrong/missing, feature flags, timeouts too low, connection limits, serialization format, logging levels |
| **DATA** | Corrupt/unexpected input, schema drift, encoding issues, missing records, stale cache, migration errors, edge case values |
| **INFRASTRUCTURE** | Server resources exhausted, network partitions, DNS, load balancer config, disk I/O, container OOM, kernel params |
| **DEPENDENCIES** | Library bugs, API breaking changes, version conflicts, transitive dependency issues, CDN outages, SaaS downtime |
| **ENVIRONMENT** | OS differences, runtime/VM version, browser quirks, locale/timezone, permissions, firewall rules, clock skew |

**Usage**: For each category, brainstorm ALL possible causes within it. This ensures MECE coverage across the problem space.

---

## 4. Bulletproof Problem Solving (Conn & McLean)

**Origin**: Charles Conn & Robert McLean, 2019. McKinsey-refined 7-step process.

### The 7 Steps

1. **Define the problem** — Precise, bounded, actionable statement
2. **Disaggregate** — Break into logic tree components (MECE)
3. **Prioritize** — Prune the tree (80/20 rule)
4. **Build a workplan** — What analysis for each branch?
5. **Conduct analyses** — Test each hypothesis
6. **Synthesize** — Integrate findings into a coherent story
7. **Communicate** — Pyramid Principle structure

### Logic Trees

**Two types**:
- **Issue tree** (hypothesis-driven): Start with a hypothesis, decompose into supporting/refuting questions
- **Factor tree** (analysis-driven): Start with components, decompose into measurable factors

**Cleaving rules**:
- Cut at natural joints — the split should feel intuitive
- Each branch must be testable with available data
- Branches are MECE — no gaps, no overlaps
- Stop decomposing when branches are directly actionable
- 3-5 branches per level

### Day-One Hypothesis
- Form your best guess on day one based on pattern recognition
- Use it to DIRECT investigation, not to BIAS it
- Actively seek disconfirming evidence
- Update or discard as evidence accumulates

### One-Day Answer
- What would you recommend if you had to answer TODAY?
- Forces clarity about what you actually know vs. assume
- Reveals the critical unknowns that need investigation

### Porpoising
- Alternate between analysis depth and synthesis breadth
- Don't go deep on everything — go deep on the critical 20%
- Surface regularly to check if the direction still makes sense

---

## 5. Five Whys

**Origin**: Sakichi Toyoda, Toyota Production System, 1930s.

**Process**: Ask "why?" iteratively until you reach a root cause you can directly address.

**Rules**:
- Don't accept vague answers — each "because" must be specific and verifiable
- Don't stop at symptoms — "the server crashed" is a symptom, not a root cause
- Don't force exactly 5 — stop when you reach an actionable root cause (usually 3-7)
- Fork when multiple causes exist at a level — each fork gets its own chain
- Verify each link: if you remove this cause, does the next effect still happen?

**Software example**:
```
Why did the API return 500? → The database query timed out
Why did the query time out? → It was doing a full table scan
Why was it doing a full table scan? → The index was missing
Why was the index missing? → The migration didn't include it
Why didn't the migration include it? → No review checklist for query perf
→ Root cause: Missing process (add migration perf review step)
```

**Pitfalls**:
- Stopping too early (symptom-level)
- Going too abstract ("because humans make mistakes")
- Single-threading when multiple causes interact

---

## 6. FMEA (Failure Mode & Effects Analysis)

**Origin**: US Military, 1949. Systematic risk assessment.

**Process**:
1. List all potential failure modes (causes)
2. Score each on three dimensions (1-10):
   - **Severity (S)**: Impact if this failure occurs
   - **Occurrence (O)**: Likelihood this is the actual cause
   - **Detection (D)**: Difficulty of verifying/testing this cause
3. Calculate RPN = S × O × D (range: 1 to 1000)
4. Prioritize by RPN descending

**Software severity scale**:
| Score | Impact |
|-------|--------|
| 1-2 | Cosmetic — UI glitch, typo, minor visual |
| 3-4 | Minor — degraded UX, workaround exists |
| 5-6 | Moderate — feature broken, no workaround |
| 7-8 | Major — data affected, security weakened, multi-user impact |
| 9-10 | Critical — data loss, security breach, system down |

**Key insight**: High detection difficulty (D=8-10) means the cause is hard to verify — these are the sneaky ones that persist because they evade testing.

---

## 7. Bayesian Reasoning for Diagnosis

**Core formula**:
```
P(Cause | Evidence) = P(Evidence | Cause) × P(Cause) / P(Evidence)
```

**Practical application** (no math needed):

1. **Set priors**: Based on base rates and experience
   - "Race conditions cause ~5% of bugs in this codebase" → Low prior
   - "Config errors cause ~30% of prod issues" → High prior

2. **Update with evidence**:
   - Evidence strongly supports hypothesis → Multiply prior by 5-10x
   - Evidence weakly supports → Multiply by 2x
   - Evidence is neutral → No change
   - Evidence contradicts → Divide by 5-10x

3. **Seek discriminating evidence**: Find observations that would be very likely under one hypothesis but very unlikely under another

4. **Avoid base rate neglect**: Exotic causes (cosmic rays, compiler bugs) should have very low priors regardless of how well they "explain" the evidence

---

## 8. Fault Tree Analysis (FTA)

**Origin**: Bell Labs, 1962. Top-down deductive failure analysis.

**Structure**: Boolean logic tree from top event (failure) down to basic events (root causes).

**Gates**:
- **AND gate**: All inputs must be true for the output (failure requires multiple conditions)
- **OR gate**: Any input causes the output (multiple possible causes)

**Software example**:
```
Payment fails (TOP)
├── OR ──┐
│        ├── API timeout
│        │   └── AND ──┐
│        │             ├── Database slow
│        │             └── No connection pooling
│        ├── Invalid card data
│        │   └── OR ──┐
│        │            ├── Frontend validation bypassed
│        │            └── Data corruption in transit
│        └── Third-party gateway down
│            └── AND ──┐
│                      ├── Primary gateway offline
│                      └── Fallback not configured
```

**Use when**: Multiple interacting causes, complex system failures, reliability analysis.

---

## 9. Swiss Cheese Model

**Origin**: James Reason, 1990. Accident causation through layered defenses.

**Concept**: Each defense layer (type system, tests, code review, monitoring) has "holes" (weaknesses). A failure occurs only when holes in ALL layers align.

**Software defense layers**:
1. Type system / static analysis
2. Unit tests
3. Integration / E2E tests
4. Code review
5. CI/CD checks (linting, security scanning)
6. Staging/QA environment
7. Canary / progressive rollout
8. Runtime monitoring / alerting
9. Circuit breakers / fallbacks

**Diagnostic use**: When a bug reaches production, map which defense layers had holes. The fix should patch multiple holes, not just one.

**Preventive use**: After fixing, verify at least 3 independent defense layers would now catch a recurrence.

---

## 10. Change Analysis

**Core question**: What changed between the working state and the broken state?

**Categories of change**:
- **Code**: Recent commits, merges, rebases
- **Configuration**: Env vars, feature flags, DB settings
- **Data**: New data patterns, volume changes, schema changes
- **Infrastructure**: Deploy, scaling event, cert rotation, dependency update
- **External**: Third-party API changes, traffic patterns, attack

**Process**:
1. Identify the exact boundary between working and broken (timestamp, deploy, commit)
2. List ALL changes across all categories in that window
3. For each change, assess: could this cause the observed symptoms?
4. Test by reverting the most likely change

**Tools**: `git log`, `git bisect`, deploy logs, config management history, monitoring timelines

---

## 11. Pareto Analysis (80/20)

**Principle**: ~80% of effects come from ~20% of causes.

**Software application**:
- 80% of bugs come from 20% of modules
- 80% of latency comes from 20% of code paths
- 80% of errors come from 20% of error types

**Process**:
1. Categorize all potential causes
2. Estimate or measure impact of each
3. Sort by impact descending
4. Draw the cumulative line — focus investigation on causes above the 80% line
5. Ignore the "trivial many" below the line (for now)

---

## 12. Hypothesis-Driven Debugging (Scientific Method)

**Process**:
1. **Observe**: Gather symptoms, evidence, reproduction conditions
2. **Hypothesize**: Form a specific, falsifiable explanation
3. **Predict**: If hypothesis is true, what ELSE should we observe?
4. **Test**: Design the simplest experiment to confirm or refute
5. **Conclude**: Update or reject hypothesis based on results
6. **Repeat**: Next hypothesis, updated by what you learned

**Key discipline**: ALWAYS predict before testing. If you can't make a prediction, your hypothesis isn't specific enough.

**Binary search / bisection** (git bisect):
- When: regression in a commit range, and the range is more than ~10 commits
- Halve the range with each test → O(log n) commits to check
- `git bisect start`, `git bisect good <hash>`, `git bisect bad <hash>`

---

## 13. Current Reality Tree (Theory of Constraints)

**Origin**: Eliyahu Goldratt, "The Goal", 1984.

**Use when**: Systemic issues — the problem isn't one bug, it's a pattern of recurring issues.

**Process**:
1. List all **Undesirable Effects (UDEs)** — symptoms observed
2. Connect UDEs with if-then cause-effect logic
3. Identify the **root constraint** — the single factor that, if resolved, eliminates the most UDEs
4. Build the tree bottom-up from root causes to UDEs

**Software example**: "Why do we keep having production incidents?"
- UDE: Frequent prod incidents → Because: insufficient test coverage
- UDE: Insufficient test coverage → Because: no time allocated for tests
- UDE: No time for tests → Because: all time spent on incident response
- ROOT CONSTRAINT: Incident response consumes capacity that should be spent on prevention

---

## 14. Systems Thinking & Causal Loop Diagrams

**Use when**: Feedback loops, emergent behavior, "fixes that backfire"

**Reinforcing loop (R)**: A → more B → more A (vicious/virtuous cycle)
**Balancing loop (B)**: A → more B → less A (self-correcting)

**Software examples**:
- **Reinforcing**: More technical debt → slower development → more shortcuts → more technical debt
- **Balancing**: More monitoring → faster incident detection → quicker fixes → fewer incidents → less urgency for monitoring
- **Fixes that backfire**: Adding cache to fix slow queries → stale data bugs → more cache invalidation logic → more complexity → more bugs

**Diagnostic use**: If fixing the symptom doesn't fix the problem, look for the feedback loop that regenerates it.

---

## 15. OODA Loop

**Origin**: John Boyd, military strategy. Observe-Orient-Decide-Act.

**Use when**: Fast-moving incidents, production outages, chaotic domain.

**Cycle**:
1. **Observe**: What's happening RIGHT NOW? Fresh data only.
2. **Orient**: How does this connect to what we know? Update mental model.
3. **Decide**: What's the minimum viable next action?
4. **Act**: Execute and immediately observe the result.

**Key**: Speed of iteration matters more than depth of analysis. Short OODA loops beat thorough-but-slow analysis in chaotic situations. Once stabilized, switch to deeper methodologies.

---

## 16. DMAIC (Six Sigma)

**Use as overall framing**:
1. **Define**: Problem statement, scope, stakeholders (Phase 1)
2. **Measure**: Quantify current state, establish baseline metrics (Phase 2)
3. **Analyze**: Root cause analysis using any of the above methods (Phases 3-4)
4. **Improve**: Implement and validate fix (Phases 5-6)
5. **Control**: Monitoring, tests, processes to prevent recurrence (Phase 7)

---

## 17. MECE Principle (McKinsey)

**Mutually Exclusive**: No overlap between categories — each cause belongs to exactly one bucket.
**Collectively Exhaustive**: No gaps — every possible cause is covered by some bucket.

**Testing MECE**:
- Take any potential cause — does it fit in exactly one category? (ME check)
- Can you think of a cause that doesn't fit any category? (CE check)
- If either fails, recut your categories

**Common MECE structures for software**:
- By layer: frontend / backend / database / infrastructure
- By lifecycle: build / deploy / runtime / monitoring
- By cause type: code / config / data / infra / deps / env (the fishbone categories)
- By timing: always / intermittent / time-based / load-based
- By scope: single user / subset / all users

---

## 18. Pyramid Principle (Barbara Minto)

**Use for**: Structuring the diagnostic report and communicating findings.

**Structure**:
1. **Answer first**: Lead with the root cause and recommended fix
2. **Group supporting arguments**: Each group supports the answer (MECE)
3. **Order logically**: Within each group, order by importance or chronology
4. **SCQA intro**: Situation → Complication → Question → Answer

**Example**:
- **S**: The payment API has been returning 500 errors since Tuesday
- **C**: Error rate is 12% and growing, affecting $X revenue
- **Q**: What is the root cause and how do we fix it?
- **A**: A missing database index causes query timeouts under load; adding the index fixes it in 5 minutes

---

## 19. Rubber Duck Debugging

**Use when**: Stuck after 15+ minutes of investigation. Feeling confused.

**Process**: Explain the problem out loud (or in writing) step by step, as if teaching someone unfamiliar. The act of articulation often reveals hidden assumptions or gaps in understanding.

**AI-adapted version**: Write out your current understanding in structured form:
1. What I know for certain
2. What I suspect but haven't verified
3. What I've ruled out and why
4. What I haven't checked yet
5. What doesn't make sense

Often, item 5 points to the root cause.

---

## 20. Barrier Analysis

**Core question**: What barriers (defenses) should have prevented this failure, and why did they fail?

**Barrier types in software**:
| Barrier Type | Examples | Failure Modes |
|-------------|----------|---------------|
| **Physical** | Network segmentation, WAF, rate limiter | Misconfigured, bypassed, capacity exceeded |
| **Procedural** | Code review, deploy checklist, runbook | Skipped, incomplete, outdated |
| **Automated** | Tests, CI checks, static analysis, monitoring | Missing coverage, disabled, flaky |
| **Administrative** | Access controls, approval workflows | Over-permissioned, rubber-stamped |

**Process**:
1. List all barriers that should protect against this failure class
2. For each: did it exist? Was it active? Did it detect? Did it prevent?
3. Failed barriers reveal systemic weaknesses to address in Phase 7
