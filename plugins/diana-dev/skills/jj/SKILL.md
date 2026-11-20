---
name: jj
description: Work in jj (Jujutsu VCS) colocated repos — daily flow, history rewriting, bookmarks, git interop. Use when a repo has .jj alongside .git, or user mentions jj/jujutsu. Triggers — 'jj', 'jujutsu', 'jj push', 'jj undo', 'colocated', 'джейджей'.
triggers: ["jj", "jujutsu", "джейджей", "jj status", "jj push", "colocated repo"]
---

# jj (Jujutsu) — Colocated Workflow

The working copy IS a commit (`@`): no staging area, every file in the directory is already in `@`. Every operation is recorded and undoable. Colocated = `.jj` + `.git` in one dir (`[ -d .jj ]`); jj imports/exports git refs on every command.

Reference: CLI https://docs.jj-vcs.dev/latest/cli-reference/, bookmarks and push safety https://docs.jj-vcs.dev/latest/bookmarks/, git interop https://docs.jj-vcs.dev/latest/git-compatibility/. Installed `jj 0.44`; flags below checked against it (`jj <cmd> --help` when in doubt, jj renames flags between releases).

```bash
jj st; jj log; jj diff                 # state; ◆ in log = immutable
jj describe -m "msg"; jj new           # name @, start the next commit
jj edit <change-id>                    # edit an older commit; descendants auto-rebase
jj squash [-i]; jj split; jj absorb    # reshape history
jj rebase -r <id> -o main; jj abandon <id>
jj op log; jj undo                     # undo any operation; jj op restore <op-id>
jj git fetch
jj bookmark set main -r @; jj git push -b main   # bookmarks do not follow commits: set before push
jj git push -c @                       # push @ under a generated bookmark (PR branch)
```

Push is force-with-lease by design: a rewritten bookmark goes through only if the remote still matches the last fetch. A safety-check refusal → `jj git fetch`, inspect `jj log`, resolve, push again. There is no force flag to reach for.

## Rules for Diana

1. **Untracked ≠ safe.** Scratchpads, `.env`, build junk all land in `@`. Run `jj st` before `describe`/push; add noise to `.gitignore`.
2. **Prefer jj over git** in colocated repos; git only for what jj lacks (LFS, submodule edge cases). After any git-side history edit, check `jj log`.
3. **Never `git push --force`** from the git side: use `jj git push` so bookmarks and the op log stay coherent.
4. **Never** run `jj git init` twice or delete `.jj` to "clean up".
5. **No Co-Authored-By**; the description body is the decision log, same as git.
6. **New colocated repo:** `jj git init --colocate` in the existing clone → `jj bookmark track main@origin` → `jj config set --user user.name "$(git config user.name)"` and the same for `user.email` → `jj metaedit --update-author` to fix the first working-copy commit.
