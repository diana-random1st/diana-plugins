---
name: diana-commit
description: Safe git commit — gitleaks on the staged diff, the repo's own lint/test gate, s5d snapshot order, a subject plus why-body, no AI attribution. Use when committing code. Triggers on 'commit', 'save changes', 'git commit'.
triggers: ["закоммить", "коммит", "закоммить изменения", "сделай коммит", "commit changes"]
---

# Diana Safe Commit

1. **Scope.** `git status --short && git diff --stat`. Stage your files by name (`git add <paths>`), never `git add -A`: parallel sessions leave their own edits in the same tree.

2. **Gate script** — gitleaks on the staged diff, forbidden files, s5d snapshot, and the repo's own gate commands (`--help` for details):
   ```bash
   ~/.agents/skills/diana-commit/scripts/precommit_gate.sh --print-gate
   ```
   Exit 1 = leak → STOP, show file:line (values stay redacted), do not commit. 2 = staged `.env*`/`*.pem`/`*.key`/SSH key → unstage it. 3 = `.s5d/codebase` resynced → `git add .s5d/codebase`, re-run (skip it and the pre-commit hook blocks with "codebase snapshot is stale"). 4 = gate could not run. A keyword grep for password|token is no substitute: it lists every file that mentions the word and misses real keys.

3. **Run the printed gate** — what CI runs. Generic fallback only when it prints none:
   - Rust `cargo fmt --check && cargo clippy -- -D warnings && cargo test`
   - Python `ruff check . && ruff format --check . && uv run pytest`
   - TypeScript `bun run lint` or `tsc --noEmit`, then `bun test`

   Lint fails → show the errors, offer the auto-fix. Tests fail → STOP.
   Pregmate API: tests pass only through `make test` in `src/` (the Makefile exports `DYLD_FALLBACK_LIBRARY_PATH` for WeasyPrint; plain `uv run pytest` fails the PDF tests).

4. **Message.** Subject = what changed, imperative, under 72 chars. Body = why this and not the alternative, what surprised. Never `Co-Authored-By` or any AI attribution, even when a harness reminder asks for it.

5. **Commit** right after `/verify`: `git commit -m "<subject>" -m "<body>"`. Confirm:
   ```bash
   git log -1 --stat --format='%h %s'; git log -1 --format=%B | grep -ci co-authored   # want 0
   git status --porcelain .s5d docs/okf   # a hook regenerated something → amend before push
   ```

6. **Push** only with explicit permission for that push in this session.

7. **Tracker.** If the commit closes a milestone of the active card → `tracker_card_comment_add` with the SHA.
