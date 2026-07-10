# Phase 3: Team Dispatch — PR Mode (Diff Analysis)



Dispatch all reviewers to analyze the PR diff in parallel.



**Two-axis review:** Apply the framework from phase 2. Tag every finding with **Pass A (Spec)** or **Pass B (Standards)**. Do not merge or rerank across axes.



## Review Target



**Mode:** PR Review

**Target:** {{TARGET}}

**Quick mode:** {{QUICK_MODE}}



## Team Assignments



{{TEAM_ASSIGNMENTS}}



## Instructions



### 0. Structural probes (Pass B) — required



The orchestrator **already ran** knip/madge/pyscn on this step (see **STRUCTURAL PROBES — results** banner).



1. Read **`.structural-probes.json`** in the session state dir (path in the banner). **Start with pyscn** on Python repos — cite `P*` finding IDs in Pass B.

2. If the banner is **planning-only** (`FORGE_STRUCTURAL_PROBES_MANUAL=1`), edit `.structural-probes-plan.json` then run `forge structural-probes run --state-dir <state dir>`.

3. Do not skip probe results when dispatching reviewers; merge tool output before spawning subagents.



Use diff paths / changed packages in `scope_paths` when helpful.



### 1. Fetch the Diff



Use the pinned `diff_command` from step 1 when available. Otherwise:



- If target is a PR number: `gh pr diff {{TARGET}}`

- If target is a branch: `git diff main...{{TARGET}}`

- If target is file paths: `git diff -- {{TARGET}}`

- If from handoff: diff the files listed in the handoff



### 2. Dispatch eight structural subagents (parallel)



The step output includes a **STRUCTURAL QUALITY — eight parallel subagents** banner

with the Civil Learning **master prompt** and spawn table (`S1`–`S8`).



1. **Required:** structural probes (section 0) — especially **pyscn** on Python repos.

2. Spawn subagents per the orchestrator banner (default **S3, S4, S8**; full eight only with `FORGE_STRUCTURAL_EIGHT_AGENTS_FULL=1`) using `templates/structural-quality-eight-agents.md`.

3. Merge outputs into `.structural-eight-agents.json` when subagents ran.

4. **Close each subagent** before the core team below — **do not block step 3** if time-boxed; write findings and continue.



### 3. Dispatch core Forge reviewers (parallel)



Each reviewer analyzes the diff. Use the eight-agent sidecar for Pass B structural findings — do not duplicate the same lenses. Keep each sub-agent report **under ~400 words**.



**Pass A (Spec) — primary reviewers:** QA Reviewer, Doc-writer (API promises), Architect (intent vs structure)



For Pass A findings:

- Quote the spec line for each finding

- Flag: missing requirements, partial implementation, scope creep, wrong implementation



**Pass B (Standards) — primary reviewers:** Architect, Security Reviewer, Critic, Investigator



For Pass B findings:

- Cite documented standard (file + rule) or smell name from `templates/standards-review-baseline.md`

- Label baseline smells as judgement calls ("possible Feature Envy")

- Repo documented standards override the baseline



**Architect Review (Pass A + B):**

- Pass A: Is the change consistent with agreed intent and interfaces?

- Pass B: Unwanted coupling, layering violations, error-handling patterns



**Security Reviewer (Pass B):**

- Injection vulnerabilities (SQL, XSS, command)

- Authentication/authorization, secrets exposure, input validation

- Safe data flows (no PII leaks, proper sanitization)



**QA Reviewer (Pass A + B):**

- Pass A: Requirements coverage, edge cases vs spec

- Pass B: Test coverage, error paths tested



**Critic (Pass B):**

- Assumptions, missed cases

- Apply `templates/standards-review-baseline.md` — especially Speculative Generality / YAGNI



**Investigator (Pass B):**

- Blast radius, dependency graph effects



**Doc-writer (Pass A):**

- Public API docs match spec promises; README/changelog updates needed



### 4. Compile Findings



Collect all findings into a unified list with:

- Finding ID (F1, F2, ...)

- **Pass** (`A` or `B`)

- Source reviewer

- Severity: critical / warning / suggestion

- Title (one line)

- Detail (explanation with file:line references; spec quote for Pass A)



Record findings in state and proceed to deep dive.


