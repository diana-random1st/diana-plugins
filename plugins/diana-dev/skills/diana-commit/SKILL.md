---
name: diana-commit
description: Safe git commit with pre-commit checks — secrets scan, lint, format, test. Use when committing code. Triggers on 'commit', 'save changes', 'git commit'.
triggers: ["закоммить", "коммит", "закоммить изменения", "сделай коммит", "commit changes"]
---

# Diana Safe Commit

Commit changes with automated safety checks.

## Steps

1. **Show status**: Run `git status` and `git diff --stat` to show what will be committed.

2. **Secrets scan**: Check staged files for credentials.
   - Run: `git diff --cached --name-only | xargs -I{} grep -rlE '(password|secret|token|api.?key|bearer)' {} 2>/dev/null`
   - Check for: `.env` files, `*.pem`, `*.key`, hardcoded tokens
   - If found → STOP. Show user what was found. Do not commit.

3. **Lint & format** (language-dependent):
   - Rust: `cargo fmt --check && cargo clippy -- -D warnings`
   - Python: `ruff check . && ruff format --check .`
   - TypeScript: `bun run lint` or `tsc --noEmit`
   - If lint fails → show errors, offer to auto-fix

4. **Test** (if test suite exists):
   - Rust: `cargo test`
   - Python: `uv run pytest` (if pytest found)
   - TypeScript: `bun test` (if tests found)
   - If tests fail → STOP. Show failures.

5. **Compose message**: Draft a concise commit message.
   - 1 line summary (imperative mood, <72 chars)
   - Optional body explaining why, not what
   - NEVER add Co-Authored-By lines

6. **Commit**: `git add [specific files] && git commit -m "message"`
   - Prefer specific file names over `git add -A`
   - Show final `git log -1 --oneline` to confirm

7. **Update Linear** (if LINEAR_TASK_ID in env):
   - Add comment to Linear task with commit summary
