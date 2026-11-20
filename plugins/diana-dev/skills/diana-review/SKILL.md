---
name: diana-review
description: Security-focused review of a diff — gitleaks, OWASP-grounded security pass, correctness, fit with the repo, findings report. Use when reviewing code changes, PRs, or before merging. Triggers on 'review', 'code review', 'check security'.
---

# Diana Code Review

1. **Scope.**
   - Files named by the user → those.
   - Uncommitted work (the usual case) → `git diff HEAD --stat`, then `git diff HEAD`.
   - Branch → `git diff $(git merge-base HEAD origin/main)...HEAD`; PR number → `gh pr diff <n>`.

   Read the repo's AGENTS.md / CLAUDE.md and any repo-local review skill or agent (`.claude/skills/*review*`, `agents/*review*`) first: they hold the project's rules.

2. **Secrets.** A leak → STOP and report before anything else:
   ```bash
   gitleaks git --pre-commit --redact --no-banner .            # working tree; add --staged for the index
   gitleaks git --log-opts="<base>..HEAD" --redact --no-banner  # committed range
   ```

3. **Review.** For a large diff spawn a reviewer agent and hand it the diff, not your conclusions.
   - Security: OWASP Top 10 (https://top10.owasp.org/), specifics in https://cheatsheetseries.owasp.org/.
   - Correctness: edge cases, error paths, concurrency, resource leaks.
   - Fit: local patterns, no over-engineering, tests for new behaviour, no unannounced breaking change.

   Prove a suspected bug with a test or a probe run before calling it CRITICAL.

4. **Report.** One line per finding, tagged [VERIFIED] (reproduced) or [INFERRED]:
   ```
   CRITICAL: file:line — issue — fix
   WARNING: file:line — ...
   SUGGESTION: file:line — ...
   ```

5. **Memory.** A durable lesson (trap, project rule) → Hindsight `retain`, `bank_id: diana`, tag `project` or `feedback`, one fact per call.

Heavier: `/code-review` (built-in, effort levels), `crossreview` (several agents, blind), `tribunal` (multi-model arbitration for high-risk calls).
