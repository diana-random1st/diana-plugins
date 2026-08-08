---
name: diana-deploy
description: Pre-deploy verification checklist. Use before deploying to staging or production. Triggers on 'deploy', 'pre-deploy check', 'deploy readiness'.
---

# Diana Deploy Checklist

Pre-deployment verification to catch issues before they reach production.

## Steps

1. **Branch check**: confirm current branch (main/release), no uncommitted changes (`git status`), up-to-date (`git fetch && git status -sb`).

2. **Build verification**: run full build — Rust: `cargo build --release`, Python: `uv sync && ruff check .`, TypeScript: `bun install && bun run build`, Flutter: `flutter build`. No warnings or errors.

3. **Test suite**: run ALL tests (`cargo test`, `uv run pytest`, `bun test`). Note coverage and any skipped tests.

4. **Security scan**: check known vulnerabilities (`cargo audit`, `uv pip audit`, `bun audit`), scan for hardcoded secrets, confirm .env files are not committed.

5. **Migration check**: any pending DB migrations, API breaking changes, or config/env changes?

6. **Report**:
   ```
   ✅ READY TO DEPLOY
   - Branch: main (up-to-date)
   - Build: success
   - Tests: 42 passed, 0 failed
   - Security: no issues
   - Migrations: none pending
   ```
   or
   ```
   ❌ NOT READY
   - [list blockers]
   ```

7. **Confirm**: Ask user for explicit deploy permission before executing any deploy command.
