---
name: diana-debug
description: Systematic debugging methodology — reproduce, isolate, diagnose root cause before proposing fixes. Use when encountering bugs, test failures, or unexpected behavior. Triggers on 'debug', 'systematic debug', 'root cause', 'why is this failing'.
---

# Diana Systematic Debugging

Root-cause first. No guessing, no shotgun fixes.

## Methodology

### Phase 1: Reproduce
1. Get exact error message/behavior description
2. Identify reproduction steps
3. Run the failing command/test and capture FULL output
4. Confirm: can we reproduce consistently?

### Phase 2: Isolate
1. **Read the error literally** — what does it actually say?
2. **Narrow scope**: which file, function, line?
3. **Check prerequisites**: dependencies installed? Config correct? Environment set up?
4. **Binary search**: if large scope, bisect to find the breaking change
   - `git bisect` for regressions
   - Comment out sections for isolation

### Phase 3: Diagnose
1. **Form hypothesis** — one specific theory about the cause
2. **Test hypothesis** — add logging, assertions, or minimal test case
3. **Verify** — does the evidence support the hypothesis?
4. If hypothesis wrong → form new one. DO NOT try random fixes.

### Phase 4: Fix
1. **Smallest possible change** that addresses root cause
2. **Verify fix**: run the original failing command → should pass
3. **Check for regressions**: run related tests
4. **Explain**: why did this happen, why does this fix work

## Rules

- Same error 2+ times → STOP workarounds. Go back to Phase 2.
- Never propose a fix without understanding the cause.
- Mark findings: [VERIFIED] (tested), [INFERRED] (logical), [SPECULATIVE] (needs testing).
- If stuck after 3 hypotheses → step back, re-read error, check assumptions.
- Log debugging steps for future reference.

## Anti-patterns (DO NOT)

- ❌ "Try this and see if it works" without theory
- ❌ Multiple changes at once (can't tell what fixed it)
- ❌ Suppressing errors instead of fixing cause
- ❌ Blaming environment without evidence
- ❌ Restarting/rebuilding as first step (do this only if evidence points to stale state)

## Output format

```
## Debug Report

**Symptom**: [exact error]
**Root Cause**: [verified cause]
**Fix**: [what was changed and why]
**Verification**: [test/command that proves fix works]
**Prevention**: [how to avoid this in future, if applicable]
```
