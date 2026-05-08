# forge-codex

A Codex-native agent toolkit for structured software delivery: investigation, planning, implementation, review, testing, diagnostics, and workflow continuity across sessions.

## Recent Changes

Mock Flows + Numbered Handoff Menu (2026-05-07):
- `forge:test --mode flows` authors end-to-end mock flows in 4 styles (scenario / BDD / HTTP-replay / workflow-dry-run). The skill detects your project layout, recommends the best-fit flow type with a confidence score, and progressively gates 8 quality criteria across scaffold → author → execute → report phases. Run with `--flow-type <type>` to override the recommendation, or `--framework`/`--entry-point`/`--roles` to fine-tune detection. Reference `templates/mock-flow-types.md` for per-type details.
- Every skill's final step now presents a numbered handoff menu instead of a single hardcoded next-skill string. Reply with "yes" / "1" / "default" or pick a numbered alternative to steer the workflow. Use `scripts/smoke.py` as a CI-eligible end-to-end harness for the new flows mode.

State-lifecycle and authoring fixes (2026-05-07):
- The `plan` skill now materializes a section-marker skeleton at step 1 (sourced from `templates/writing-plans.md`) and refuses to mark step 6 complete while any `<!-- FORGE_SKELETON: ... -->` markers remain.
- `python3 scripts/shared/resume.py --cleanup` lists state files eligible for cleanup (dry-run by default). Add `--force` to delete; `--all-stale --force` for migration mode (clears every state file regardless of age).
- Re-running step 1 of any skill now aborts when an in-progress same-skill session exists. To resume, use the `--state <path>` flag or run `resume.py`.
- Over-cap `--step` invocations (e.g., `--step 9` on an 8-step skill) now print a friendly "skill complete" message and exit 0 instead of erroring.
- A `failure_count` field tracks consecutive same-step retries; after two failures, `resume.py` emits an "inspect logs" hint instead of producing a third retry command.

## Quick Start

```bash
# Clone the repo
git clone https://github.com/your-org/forge-codex.git /path/to/forge-codex

# Enter the project
cd /path/to/forge-codex
```

Then use the repo as the home for Codex-oriented workflow assets, skills, prompts, and orchestrators.

## Codex Config

If you want local Codex sessions to treat Forge skill invocation as implicit
permission to use Forge agents, add a `developer_instructions` block to
`~/.codex/config.toml`:

```toml
developer_instructions = """
Invoking any `forge:*` skill implicitly authorizes the agent dispatch required by that workflow. Do not require the user to separately ask for delegation, sub-agents, or parallel agent work after invoking a Forge skill.

At the start of a fresh interactive session, begin the first user-visible response with exactly: Ready Player 1?
"""
```

You can verify the injected developer prompt with:

```bash
codex debug prompt-input
```

If a higher-priority launcher or hosted integration injects its own developer
instructions, those may still override or compete with your local config.

## Goals

- Turn a structured multi-skill workflow model into a Codex-first environment
- Support multi-step, resumable engineering workflows instead of one-shot prompts
- Separate skill orchestration from reusable methodology templates
- Preserve handoff context between phases and between sessions
- Make review, verification, and diagnostics first-class parts of the workflow

## Planned Skills

| Skill | Purpose | Typical Invocation |
|-------|---------|--------------------|
| **develop** | Investigate a problem space and shape solution options | `develop <problem or feature>` |
| **plan** | Convert an approved direction into an implementation plan | `plan` |
| **evaluate** | Review a plan before or after implementation | `evaluate <plan>` |
| **implement** | Execute a plan in ordered or parallel waves | `implement` |
| **code-review** | Run structured review modes against code changes | `code-review <target>` |
| **test** | Execute tests, analyze failures, and identify coverage gaps | `test` |
| **diagnose** | Perform root-cause analysis on bugs and regressions | `diagnose <issue>` |
| **status** | Show workflow position, open findings, and next action | `status` |
| **resume** | Continue the active workflow from persisted state | `resume` |

## Forge Skill Invocation Contract

Invoking a Forge workflow skill is intended to be enough to authorize the agent team that skill needs.

- `forge:develop`, `forge:plan`, `forge:implement`, `forge:code-review`, `forge:test`, and `forge:diagnose` should auto-dispatch the relevant Forge agents when their workflow calls for it.
- `forge:evaluate` should auto-dispatch the review team when team/review mode is active.
- Users should not need to separately ask for "sub-agents", "delegation", or "parallel agent work" after invoking a Forge skill.
- If the surrounding Codex session policy blocks agent spawning, that should be surfaced as an environment limitation rather than treated as normal Forge behavior.
- Every spawned agent must be closed (`close_agent`) once it reports back or is no longer useful. Forge skills never leave agents open across wave / step / phase boundaries — Codex caps concurrent agents and leaked sessions eventually block further dispatch. See `templates/codex-runtime.md` for the lifecycle pattern.
- At the end of each skill's workflow, a numbered handoff menu replaces the previous single next-skill prompt. Users can reply "yes", "1", "default", or a literal command; the menu makes workflow alternatives explicit.

## Workflow Model

```text
develop -> plan -> evaluate (pre) -> implement -> code-review -> test -> diagnose (if needed)

At any point:
- evaluate can run as a standalone critique workflow
- diagnose can run as an ad-hoc incident workflow
- status and resume can inspect or continue the current state
```

The intended model is composable rather than monolithic:

- Each skill can run on its own
- Skills can hand off context to the next skill in the chain
- State files make interrupted workflows resumable
- Review loops enforce quality gates before moving downstream

## Agents

The Codex version is expected to use a small set of specialized roles rather than a single undifferentiated agent.

| Agent | Role |
|-------|------|
| **architect** | Investigation lead, solution design, architecture review |
| **planner** | Implementation planning, sequencing, dependency mapping |
| **backend-dev** | Backend implementation with tests |
| **frontend-dev** | Frontend implementation with tests |
| **critic** | Challenges assumptions, stresses weak logic, finds hidden risks |
| **qa-reviewer** | Validates behavior, testing quality, and verification depth |
| **security-reviewer** | Reviews security-sensitive changes and operational risk |
| **doc-writer** | Produces user-facing and developer-facing documentation and tracks documentation debt |

## Methodology Coverage

`forge-codex` is intended to bundle practical engineering methods instead of vague “best practices”.

**Investigation and diagnostics**

- 5 Whys
- Kepner-Tregoe IS/IS-NOT
- Fishbone / Ishikawa
- FMEA
- MECE decomposition
- Bayesian evidence updates
- hypothesis-driven debugging
- change analysis
- counterfactual reasoning
- barrier analysis

**Solution design**

- divergent and convergent option generation
- trade-off scoring
- pre-mortem analysis
- reversibility checks
- constraint analysis

**Planning**

- phased execution
- dependency mapping
- parallelization opportunities
- rollback planning
- explicit verification steps
- documentation-in-the-loop

**Review and testing**

- structured finding severity
- behavior verification
- edge-case analysis
- regression coverage review
- failure triage
- operational readiness checks

## Architecture

The repo is expected to follow a script-driven orchestration model.

- **Skill orchestrators** drive state progression for each workflow
- **Prompt templates** provide repeatable phase instructions
- **Shared templates** hold reusable review and planning patterns
- **State files** persist current step, completed step, findings, and handoffs
- **Memory files** carry context between adjacent skills
- **Reports** provide durable outputs from evaluate, review, and diagnose flows

## State and Continuity

Cross-session continuity is a core design goal.

- Each active skill should persist its own state file
- Resume logic should distinguish between a true conflict and an unrelated active session
- Standalone skills should not pause just because another non-conflicting workflow exists
- Handoff files should summarize completed work and recommend the next step
- Status tooling should surface active sessions, findings, and next actions without requiring manual inspection

## Design Principles

- **Codex-first**: optimize for Codex workflows, not a direct port of another assistant’s toolkit model
- **Actionable outputs**: produce plans, findings, commands, and reports that can be used immediately
- **Resumable by default**: interrupted work should be recoverable
- **Verification over narration**: claims should be tied to code, tests, or runtime evidence
- **Composable workflows**: users should be able to run a single skill or the full chain
- **Minimal hidden state**: the workflow should be inspectable from files in the repo

## Current Project Structure

```text
forge-codex/
├── README.md
├── agents/
├── prompts/
│   ├── develop/
│   ├── plan/
│   ├── evaluate/
│   ├── implement/
│   ├── code-review/
│   ├── test/
│   └── diagnose/
├── templates/
│   ├── review/
│   ├── planning/
│   ├── reporting/
│   └── handoff/
├── scripts/
│   ├── shared/
│   ├── develop/
│   ├── plan/
│   ├── evaluate/
│   ├── implement/
│   ├── code-review/
│   ├── test/
│   └── diagnose/
├── skills/
│   ├── develop/
│   ├── plan/
│   ├── evaluate/
│   ├── implement/
│   ├── code-review/
│   ├── test/
│   ├── diagnose/
│   ├── status/
│   └── resume/
└── templates/
```

## Initial Roadmap

### Phase 1: Skeleton

- define repository layout
- add shared orchestration primitives
- add `status` and `resume` foundations
- document the state model

### Phase 2: Core Skills

- implement `evaluate`
- implement `diagnose`
- implement `develop`
- add report generation and state cleanup rules

### Phase 3: Delivery Flow

- implement `plan`
- implement `implement`
- implement `code-review`
- implement `test`

### Phase 4: Hardening

- add regression tests for state handling
- verify conflict detection logic
- tighten workflow transitions
- document extension points for future agents and skills

## Current Status

This repository now contains the copied Codex workflow assets, reorganized into a Codex-first layout. Assistant-specific packaging has been removed, and the top-level structure has been normalized around `agents/`, `skills/`, `scripts/`, `prompts/`, and `templates/`.

## License

MIT
