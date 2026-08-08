---
name: diana-review
description: Security-focused code review with secrets scanning and guard checks. Use when reviewing code changes, PRs, or before merging. Triggers on 'review', 'code review', 'check security'.
---

# Diana Code Review

Perform a comprehensive code review with security focus.

## Steps

1. **Identify scope**: Determine what to review.
   - If user specified files → review those files
   - If no files specified → run `git diff --name-only HEAD~1` to get changed files
   - For PR review → run `git diff $(git merge-base HEAD main)..HEAD --name-only`

2. **Secrets scan**: Run `diana dev hook secrets-scan` on changed files to detect leaked credentials.
   - If secrets found → STOP and report immediately. Do not continue review.

3. **Security review** (spawn reviewer agent):
   - OWASP Top 10 vulnerabilities
   - Input validation and sanitization
   - Authentication/authorization issues
   - SQL injection, XSS, command injection
   - Hardcoded credentials or tokens

4. **Correctness review**:
   - Edge cases and error handling
   - Race conditions in async/concurrent code
   - Null/undefined handling
   - Off-by-one errors
   - Resource leaks

5. **Quality check**:
   - Consistency with existing codebase patterns
   - Unnecessary complexity or over-engineering
   - Missing tests for new functionality
   - Breaking changes without migration

6. **Report**: Format findings as:
   ```
   🔴 CRITICAL: [file:line] description
   🟡 WARNING: [file:line] description
   🟢 SUGGESTION: [file:line] description
   ```

## Memory Integration

After review, save significant findings to beliefs:
```
belief__observe(name="Code review: [context]", category="decision", body="[findings]")
```
