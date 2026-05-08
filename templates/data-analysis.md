# Data Analysis Protocol

Structured data analysis techniques for the diagnose skill. Complements the reasoning methodologies (FMEA, Bayesian, 5-Why) with concrete data extraction and quantitative analysis methods.

## Core Principle

> Reasoning without data is speculation. Data without reasoning is noise. Use data to generate hypotheses, then reason about causality.

> **Source data takes precedence over synthesis.** When both raw data (logs, metrics, code, test output) and synthesized conclusions (agent summaries, LLM ratings) are available, present and weight the raw data first. Synthesized conclusions are secondary signals — useful for orientation, but never authoritative on their own. If a synthesized conclusion contradicts the raw data, the raw data wins.

## 1. Log Analysis

### When to Use
Any issue with observable symptoms in logs (errors, warnings, unexpected behavior).

### Protocol

**Step 1: Identify relevant log sources**
| Symptom Type | Log Sources |
|-------------|-------------|
| Crash / exception | stderr, application logs, syslog, crash dumps |
| Slow response | Access logs, application performance logs |
| Data issue | Audit logs, transaction logs, DB query logs |
| Auth / security | Auth logs, access logs, security event logs |
| Deployment issue | Deploy logs, CI/CD logs, container logs |

**Step 2: Establish the time window**
- When was the last known-good state?
- When was the issue first reported?
- Search window: [last-good - 1hr] to [now]

**Step 3: Extract error patterns**
```bash
# Top error messages by frequency
grep -i "error\|exception\|fatal\|panic" <logfile> | sort | uniq -c | sort -rn | head -20

# Error frequency over time (per-minute buckets)
grep -i "error" <logfile> | awk '{print $1, $2}' | cut -d: -f1,2 | sort | uniq -c

# Stack trace extraction
grep -A 10 "Traceback\|Exception\|at .*\.java:" <logfile> | head -100
```

**Step 4: Compare working vs. broken periods**
```bash
# Count errors in working period
grep -c "ERROR" <logfile-before>

# Count errors in broken period
grep -c "ERROR" <logfile-after>

# Pattern diff: what's new?
diff <(grep "ERROR" <logfile-before> | sed 's/[0-9]//g' | sort -u) \
     <(grep "ERROR" <logfile-after> | sed 's/[0-9]//g' | sort -u)
```

**Step 5: Correlate with events**
Cross-reference error spike onset with: deploys, config changes, dependency updates, traffic changes, external service incidents.

### Output Format
```
## Log Analysis
- **Sources examined:** [list]
- **Time window:** [start] to [end]
- **Top errors:** [frequency-ranked list]
- **Pattern change:** [what's new vs. baseline]
- **Spike onset:** [timestamp] — correlates with [event]
```

## 2. Git History Analytics

### When to Use
Regression identification, understanding code churn, finding change-correlated failures.

### Techniques

**Hotspot analysis** — files that change most often correlate with bug density:
```bash
# Most frequently changed files (last 90 days)
git log --since="90 days ago" --format=format: --name-only | grep -v '^$' | sort | uniq -c | sort -rn | head -20

# Churn in a specific directory
git log --since="30 days ago" --format=format: --name-only -- src/ | grep -v '^$' | sort | uniq -c | sort -rn | head -20
```

**Temporal coupling** — files that always change together reveal hidden dependencies:
```bash
# Files that changed in the same commit (find co-change pairs)
git log --format=format: --name-only | grep -v '^$' | sort -u > /tmp/files_per_commit
# Then look for pairs that appear together > 3 times across commits
```

**Regression window** — narrow the search with git bisect:
```bash
# Interactive bisect
git bisect start
git bisect bad HEAD
git bisect good <last-known-good-commit>
# Then test at each step

# Automated bisect with test command
git bisect start HEAD <good-commit> -- && git bisect run <test-command>
```

**Blame analysis** — who last touched the failing code:
```bash
git blame -L <start>,<end> <file>
git log --follow -p -- <file>  # Full history of a file
```

**Change window correlation**:
```bash
# Commits in the symptom onset window
git log --oneline --since="2024-01-15" --until="2024-01-16"

# Diff between known-good and current
git diff <good-commit>..HEAD --stat
git diff <good-commit>..HEAD -- <specific-file>
```

### Output Format
```
## Git Analysis
- **Hotspots:** [top 5 most-changed files]
- **Temporal coupling:** [file pairs that always change together]
- **Regression window:** [good-commit]..[bad-commit] (N commits)
- **Suspect commits:** [list with descriptions]
- **Blame:** [who last modified the relevant lines]
```

## 3. Performance Profiling

### When to Use
Latency regressions, memory growth, CPU spikes, resource exhaustion.

### Tool Selection by Language

| Language | CPU Profiler | Memory Profiler | Tracing |
|----------|-------------|-----------------|---------|
| Python | `cProfile`, `py-spy` | `tracemalloc`, `objgraph` | `opentelemetry` |
| Node.js | `--prof`, `clinic flame` | `--inspect` + Chrome DevTools | `opentelemetry` |
| Go | `pprof` (CPU + memory) | `pprof` (heap) | `opentelemetry` |
| Java | `async-profiler`, `jfr` | `jmap`, `MAT` | `opentelemetry` |
| Rust | `perf`, `flamegraph` | `valgrind`, `heaptrack` | `tracing` crate |
| General | `perf` (Linux) | `valgrind` | OS-level tracing |

### Reading Flame Graphs
- **Wide bars** = functions consuming the most time (hot paths)
- **Deep stacks** = many layers of function calls (look for unexpected depth)
- **Plateaus** = single function dominating (possible bottleneck or busy-wait)
- **Compare before/after** flame graphs to spot what changed

### Latency Percentiles
| Percentile | What It Tells You |
|-----------|------------------|
| p50 (median) | Typical user experience |
| p95 | Tail latency — affects 1 in 20 requests |
| p99 | Worst-case latency — often reveals resource contention |
| p99.9 | Extreme outliers — GC pauses, lock contention, cold starts |

**Key insight:** If p50 is fine but p99 is bad, the issue is likely resource contention (locks, GC, connection pools), not algorithmic complexity.

### Memory Analysis Patterns
- **Steady growth** = leak (objects retained but never freed)
- **Sawtooth** = normal GC behavior (allocate, collect, repeat)
- **Step function** = cache fills or one-time allocation (usually fine)
- **Spike then flat** = startup allocation (usually fine)

### Output Format
```
## Performance Analysis
- **Tool used:** [profiler]
- **Baseline:** [metrics from healthy state]
- **Current:** [metrics from degraded state]
- **Hot paths:** [top 3 functions by time/memory]
- **Percentiles:** p50=[X]ms, p95=[X]ms, p99=[X]ms
- **Verdict:** [bottleneck identified / no regression / needs deeper investigation]
```

## 4. Metric Correlation

### When to Use
When multiple metrics are available and the goal is to identify which metric changes correlate with the symptom.

### Protocol

**Step 1: Establish baseline**
Document "normal" values for key metrics during a healthy period:
```
## Metric Baseline (healthy period: [dates])
| Metric | Normal Range | Source |
|--------|-------------|--------|
| Error rate | 0.01-0.05% | monitoring |
| p95 latency | 50-80ms | APM |
| CPU utilization | 20-40% | infrastructure |
| Memory usage | 2.1-2.4GB | infrastructure |
| Queue depth | 0-5 | message broker |
| DB connections | 8-12 active | connection pool |
```

**Step 2: Capture degraded-state metrics**
Same metrics during the symptom window.

**Step 3: Identify correlated changes**
Which metrics moved together? Use this decision tree:
- **Error rate up + latency up** → Downstream dependency issue or resource exhaustion
- **Error rate up + latency normal** → Logic bug or data issue (fast failures)
- **Latency up + error rate normal** → Resource contention (locks, pool exhaustion, GC)
- **CPU up + everything else normal** → Compute-bound regression (algorithm, loop, parsing)
- **Memory up + latency up** → Memory pressure causing GC or swapping
- **Queue depth up + latency up** → Consumer bottleneck (processing slower than production)

**Step 4: Rate-of-change analysis**
- **Step function** (sudden jump) → Deployment, config change, or dependency failure
- **Gradual degradation** (linear growth) → Leak, accumulation, or capacity issue
- **Oscillation** (cyclic) → Retry storms, thundering herd, periodic job interference

## 5. Dependency & Environment Analysis

### When to Use
Issues that correlate with deployments, dependency updates, or environment changes.

### Techniques

**Lock file diff:**
```bash
# What dependencies changed?
git diff <good-commit>..HEAD -- package-lock.json yarn.lock Pipfile.lock Cargo.lock go.sum
```

**Known vulnerability correlation:**
```bash
# Check for known issues in dependencies
npm audit          # Node.js
pip audit          # Python (pip-audit)
cargo audit        # Rust
```

**Environment diff:**
Compare environment variables, config files, and runtime versions between working and broken states.

**Transitive dependency investigation:**
A direct dependency didn't change, but one of its dependencies did. Check:
```bash
# Node.js: what changed transitively?
diff <(git show <good>:package-lock.json | jq '.dependencies' | sort) \
     <(cat package-lock.json | jq '.dependencies' | sort)
```

## 6. Statistical Reasoning

### Lightweight statistical concepts for diagnostic reasoning (no tools required)

**Sample size awareness:**
- 5 errors in 1,000 requests (0.5%) — could be noise
- 50 errors in 1,000 requests (5%) — definitely a signal
- Rule of thumb: < 30 observations → be cautious about conclusions

**Base rate reasoning:**
- "This error happens 0.1% of the time" → Is that new? If the base rate was 0.08%, the change is small.
- Always ask: "What was the rate BEFORE the change?"

**Simpson's Paradox:**
- An aggregate trend can reverse when split by cohort
- Example: Overall error rate down, but error rate UP for mobile users (hidden by desktop improvement)
- Always slice metrics by relevant dimensions before concluding

**Regression to the mean:**
- Extreme observations tend to be followed by less extreme ones
- "The fix worked — error rate dropped!" → Would it have dropped anyway?
- Compare to a control period or use A/B methodology

**Correlation ≠ Causation:**
- Two metrics moving together doesn't mean one causes the other
- Apply the counterfactual test: "If we removed cause X, would the effect still occur?"
- Look for confounders: a third factor causing both

## Bundled Scripts

### `scripts/diagnose/log_analyzer.py`
Structured log analysis: top-N error patterns, frequency histogram, first/last occurrence, spike detection.

Usage: `python3 scripts/diagnose/log_analyzer.py --file <logfile> [--window <start> <end>] [--pattern <regex>]`

### `scripts/diagnose/git_hotspots.py`
Git history analytics: churn-ranked file list, temporal coupling pairs, recent committers.

Usage: `python3 scripts/diagnose/git_hotspots.py [--path <dir>] [--days <N>]`
