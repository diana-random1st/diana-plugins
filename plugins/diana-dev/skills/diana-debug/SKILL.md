---
name: diana-debug
description: Systematic debugging methodology — reproduce, isolate, diagnose root cause before proposing fixes. Use when encountering bugs, test failures, or unexpected behavior. Triggers on 'debug', 'systematic debug', 'root cause', 'why is this failing'.
---

# Diana Systematic Debugging

Root cause first. No guessing, no shotgun fixes.

## Before the first hypothesis

1. `recall` the symptom in Hindsight (`bank_id: diana`): most failures here were seen before.
2. `graphify-out/` exists → query the graph for the failing module before grepping.
3. Read the repo's AGENTS.md / CLAUDE.md and any HANDOFF*.md for known traps.

## Loop

1. **Reproduce.** Run the failing command, capture the full output, note where it ran (local, dev pod, device). A remote env → reproduce there read-only first (e.g. `kubectl -n dev exec deploy/<name> -- python -c '…'`).
2. **Isolate.** Read the error literally; narrow to file:line; a regression → `git bisect run <test-cmd>` (https://git-scm.com/docs/git-bisect).
3. **Diagnose.** One hypothesis at a time, each turned into a check: assert, log line, minimal test. Wrong → next hypothesis, never a random fix.
4. **Fix.** Smallest change at the root cause. Rerun the original failing command, then the related tests.

## Rules

- Same error twice → stop, back to Isolate. The `circuit-breaker` hook blocks the third identical failing command anyway.
- Tag findings [VERIFIED] (tested), [INFERRED] (logical), [SPECULATIVE] (needs a test).
- No error suppression, no "it's the environment" without evidence, restart/rebuild only when evidence points to stale state.
- Stuck after 3 hypotheses → re-read the error, list your assumptions, test each one.

## Close

```
Symptom → Root cause → Fix → Verification (command) → Prevention
```

A root cause that is a durable trap → `retain` it (tag `infra` or `procedure`). Work that will not finish in this session → `handoff` skill.
