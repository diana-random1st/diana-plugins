---
name: pi-dev
description: "Delegate hands-on coding (implement, fix, refactor, tests, scaffolding, bulk codegen) to the local pi agent on a local model (Feynt or LM Studio) — free, offline, private. NOT for research, code review, or top-tier cloud reasoning."
triggers: ["delegate to pi", "let pi do it", "пусть pi сделает", "отдай это pi", "делегируй pi разработку"]
contracts:
  mandatory_tools: [Bash]
  verification: "pi ran headless in the target dir; its changes were reviewed by Opus and validated with the project's tests/lint"
  exit_criteria: "Files pi changed are listed, test/lint output is shown, and an Opus correctness verdict is given"
  requires_task: false
  requires_memory: false
---

# pi-dev — Delegate development to the local pi agent

Hand implementation work to **pi** (Earendil coding agent) running on a local model. Zero cost, fully local, private, works offline. Strong for routine dev — but it is a local model, so **its output is reviewed, never trusted blindly.**

## When to use
- A well-scoped feature, bug fix, refactor, scaffold, or test/boilerplate writing.
- Bulk mechanical edits, codegen, "make this file do X".
- Anything you'd hand a junior with a clear spec, where privacy / cost / offline matter.

## When NOT to use
- Research / unfamiliar API → `delegate` (Gemini).
- Code review, audit, security → `tribunal` or the reviewer agent.
- Vague or open-ended tasks — pi needs a concrete spec; frame it on Opus first.
- High-stakes agentic multi-repo work — keep on Opus or a cloud model.

## Preconditions (check once per session)
```bash
pi --list-models        # a local provider must be listed: feynt (Feynt tray app, 127.0.0.1:19234) or lmstudio
lms ls                  # LM Studio models on disk, if you route through lmstudio
```
State on 2026-11-18: the Ornith-1.0-35B GGUF and the other LM Studio chat models were deleted in the 2026-11-16 disk cleanup (`lms ls` shows only an embedding model), and `~/.pi/agent/settings.json` defaults to provider `junie`, which `pi --list-models` does not list. The only local provider is `feynt/local` (32k ctx) — start the Feynt app, then pass the model explicitly: `pi --model feynt/local -p "..."`. `kimi-coding/*` is listed too, but it is cloud, not local.

## How to delegate
Run pi non-interactively **inside the target directory** — pi has read/bash/edit/write and acts on the cwd:
```bash
cd <project-dir> && pi --model feynt/local -p "<precise task>"   # explicit model until a working default is set
```
- Give pi a **concrete spec**: which files, what behavior, acceptance criteria.
  - Bad: `"improve the parser"`.
  - Good: `"In src/parse.ts add parseDate(s) handling ISO + RFC2822, return null on invalid; add 4 vitest cases in parse.test.ts."`
- Structured/parseable result: add `--mode json`.
- Analysis only (no edits): restrict tools — `pi --tools read,grep,find,ls -p "..."`.
- Name a long session: `-n "task name"`.
- Long task (minutes): run it backgrounded and read the output file rather than blocking.

## After pi returns — MANDATORY
1. **List changes:** `git -C <dir> status --porcelain && git -C <dir> diff`.
2. **Validate:** run the project's own gate — `pytest -q` / `ruff check` / `tsc` / `cargo check`.
3. **Opus reviews the diff:** pi runs a local model — check correctness, edge cases, hallucinated APIs, and that it did not overreach scope. Fix inline or re-delegate with a tighter spec.
4. **Report:** files changed · test/lint result (actual output) · your review verdict.

## Safety
- pi **edits files and runs bash in the cwd** — always `cd` into the correct scoped directory; never launch it at `$HOME` or a repo root you don't want mutated.
- Honor repo scope rules — do not let pi loose in off-limits repos.
- Never auto-commit pi's work; review first, commit only with explicit approval.
