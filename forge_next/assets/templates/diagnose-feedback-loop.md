<!-- Inspired by Matt Pocock engineering/diagnose skill (feedback-loop-first debugging). -->

# Diagnose Feedback Loop

The feedback loop is the debugging superpower: a fast, deterministic pass/fail signal for the bug. Without it, hypothesis testing and 5 Whys devolve into guessing.

Spend disproportionate effort here before Phase 3 (5 Whys).

## Build a loop — try in roughly this order

1. **Failing test** — unit, integration, or e2e at the seam that reaches the bug.
2. **HTTP script** — curl or small script against a running dev server.
3. **CLI invocation** — fixture input; diff stdout or exit code against known-good.
4. **Headless browser** — Playwright/Puppeteer; assert DOM, console, or network.
5. **Replay** — saved request, payload, or event log replayed in isolation.
6. **Throwaway harness** — minimal subset of the system with mocked deps.
7. **Property / fuzz** — many random inputs when output is sometimes wrong.
8. **Bisection harness** — automate boot-at-state-X for `git bisect run`.
9. **Differential loop** — same input through old vs new; diff outputs.
10. **HITL script** — last resort; structured human steps with captured output.

Persist the choice in `.diagnose-feedback-loop.json` (`loop_type`, `command_or_path`).

## Iterate on the loop

- **Faster** — cache setup, skip unrelated init, narrow scope.
- **Sharper** — assert the specific symptom, not merely “didn’t crash”.
- **More deterministic** — pin time, seed RNG, isolate filesystem, freeze network.

A 30-second flaky loop is barely better than none. A 2-second deterministic loop is a debugging superpower.

## Non-deterministic bugs

Raise the **reproduction rate**, not only the perfect repro. Loop the trigger many times, parallelize, add stress, narrow timing. Record `failure_rate` (0.0–1.0) and `runs_observed`. A 50% flake is debuggable; 1% is not — keep raising the rate.

## Run the loop (Phase 2 beat 2)

Confirm:

- The loop shows the failure mode the **user** described.
- The failure repeats across runs (or at a high enough rate).
- `symptom_captured` is verbatim (error, wrong output, metric).

## Cannot build a loop

Set `cannot_build_loop: true`, `loop_type: "none"`, `blocked_reason`, and `user_ask`. Do **not** proceed to 5 Whys without either a working loop or `repro_loop_override_reason` on diagnose state after the user responds.

## Sidecar

See `.diagnose-feedback-loop.json` beside diagnose state. Gate runs at **step 3**.
