#!/usr/bin/env python3
"""agent_config_leaks.py - secrets captured in AI-agent config files.

Approved commands land verbatim in `permissions.allow` of .claude/settings*.json
(and in Codex rules); MCP configs carry tokens in env/headers. This finds those
files under the roots, runs gitleaks on each one, drops placeholder hits, adds
the repo exposure (tracked, ignored, GitHub visibility) and prints file:line,
the rule and a MASKED value only - the raw secret never leaves this process.

Usage:
  agent_config_leaks.py [--root DIR ...] [--history] [--json]

Examples:
  agent_config_leaks.py                         # current directory
  agent_config_leaks.py --root ~ --history      # every repo under home + git history
  agent_config_leaks.py --root ~/src/app --json > /tmp/agent-leaks.json

Files: .claude/settings*.json, .mcp.json, .claude.json, CLAUDE.md,
CLAUDE.local.md, AGENTS.md, .codex/config.toml, .codex/rules/*.rules
(found with `rg --files --hidden --no-ignore`; Library, .Trash, caches,
node_modules, .venv, build dirs and .git are skipped).
Detection: `gitleaks stdin` per file, read through a pipe into this process;
a hit whose value looks like a placeholder ($VAR, <...>, {..}, REDACTED,
example, your-..., changeme, ...) is dropped. --history pipes
`git log -p --follow -- <file>` through the same scan and names the commit.
Visibility comes from `gh api repos/<owner>/<repo>` for tracked files with
findings ("unknown" without gh auth).

Output: one line per finding, `path:line  rule  masked  [repo tracked ignored
visibility]`; history findings show `history <sha>` instead of the line.
Summary on stderr.

Exit codes:
  0  no findings
  1  findings
  2  a required tool is missing (rg, gitleaks, git)
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

INCLUDE = [
    "**/.claude/settings*.json",
    "**/.mcp.json",
    "**/.claude.json",
    "**/CLAUDE.md",
    "**/CLAUDE.local.md",
    "**/AGENTS.md",
    "**/.codex/config.toml",
    "**/.codex/rules/*.rules",
]
EXCLUDE = [
    "Library/**", ".Trash/**", ".cache/**", ".npm/**", ".bun/**",
    "**/node_modules/**", "**/.venv/**", "**/Pods/**", "**/DerivedData/**",
    "**/target/**", "**/.git/**",
]
PLACEHOLDER = re.compile(
    r"^(?:\$|\*|<|\{|%|REDACTED|example|placeholder|your[_-]|dummy|changeme"
    r"|None$|null$|true$|false$)",
    re.IGNORECASE,
)
MAX_BYTES = 20 * 1024 * 1024
GITLEAKS = [
    "gitleaks", "stdin", "--no-banner", "--log-level", "error", "--exit-code", "0",
    "--report-format", "json", "--report-path", "-",
]
GITHUB = re.compile(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?/?$")


def mask(secret: str) -> str:
    """Never the value: a 4-char type prefix for long tokens, plus the length."""
    keep = secret[:4] if len(secret) >= 16 else ""
    return f"{keep}…[{len(secret)} chars]"


def scan(data: bytes, cwd: str) -> tuple[list[dict], str | None]:
    """gitleaks on data via stdin; returns [{rule, line, masked}] and an error."""
    try:
        proc = subprocess.run(GITLEAKS, input=data, capture_output=True, cwd=cwd,
                              timeout=120, check=False)
    except subprocess.TimeoutExpired:
        return [], "gitleaks timed out"
    if proc.returncode != 0:
        return [], f"gitleaks exit {proc.returncode}"
    try:
        report = json.loads(proc.stdout or b"[]")
    except ValueError:
        return [], "gitleaks report unparsable"  # never echo the report: it holds values
    hits = []
    for item in report:
        raw = (item.get("Secret") or "").strip().strip("\"'")
        if not raw or PLACEHOLDER.search(raw):
            continue
        hits.append({"rule": item.get("RuleID", "?"), "line": item.get("StartLine", 0),
                     "masked": mask(raw)})
    return hits, None


def git(repo: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, timeout=120,
                          check=False)


def repo_of(path: Path) -> str | None:
    proc = git(str(path.parent), "rev-parse", "--show-toplevel")
    if proc.returncode != 0:
        return None
    return proc.stdout.decode().strip() or None


def history(repo: str, rel: str) -> tuple[list[dict], str | None]:
    proc = git(repo, "log", "-p", "--follow", "--format=commit %H", "--", rel)
    if proc.returncode != 0 or not proc.stdout:
        return [], None
    hits, err = scan(proc.stdout, repo)
    commits = [(n, ln[7:19]) for n, ln in
               enumerate(proc.stdout.decode("utf-8", "replace").splitlines(), 1)
               if ln.startswith("commit ")]
    seen, out = set(), []
    for hit in hits:
        sha = next((c for n, c in reversed(commits) if n <= hit["line"]), "?")
        key = (hit["rule"], hit["masked"], sha)
        if key not in seen:
            seen.add(key)
            out.append({"rule": hit["rule"], "commit": sha, "masked": hit["masked"]})
    return out, err


_visibility: dict[str, str] = {}


def visibility(repo: str) -> str:
    if repo in _visibility:
        return _visibility[repo]
    url = git(repo, "remote", "get-url", "origin").stdout.decode().strip()
    match = GITHUB.search(url)
    value = "no-github-remote"
    if match:
        value = "unknown"
        if shutil.which("gh"):
            proc = subprocess.run(
                ["gh", "api", f"repos/{match[1]}/{match[2]}", "--jq", ".visibility"],
                capture_output=True, timeout=60, check=False)
            value = proc.stdout.decode().strip() or "unknown"
    _visibility[repo] = value
    return value


def inspect(path: Path, with_history: bool) -> dict:
    record = {"path": str(path), "repo": None, "tracked": False, "ignored": False,
              "visibility": None, "findings": [], "history": [], "errors": []}
    try:
        data = path.read_bytes()[:MAX_BYTES]
    except OSError as exc:
        record["errors"].append(f"unreadable: {exc.strerror}")
        return record
    repo = repo_of(path)
    record["findings"], err = scan(data, repo or str(path.parent))
    if err:
        record["errors"].append(err)
    if repo:
        rel = str(path.resolve().relative_to(Path(repo).resolve()))
        record["repo"] = repo
        record["tracked"] = git(repo, "ls-files", "--error-unmatch", "--", rel).returncode == 0
        record["ignored"] = git(repo, "check-ignore", "--no-index", "-q", "--", rel).returncode == 0
        if with_history:
            record["history"], err = history(repo, rel)
            if err:
                record["errors"].append(f"history: {err}")
        if (record["tracked"] and record["findings"]) or record["history"]:
            record["visibility"] = visibility(repo)
    return record


def discover(root: Path) -> list[Path]:
    cmd = ["rg", "--files", "--hidden", "--no-ignore"]
    for glob in INCLUDE:
        cmd += ["-g", glob]
    for glob in EXCLUDE:
        cmd += ["-g", "!" + glob]
    proc = subprocess.run(cmd, cwd=root, capture_output=True, check=False)
    if proc.returncode == 2 and not proc.stdout:
        print(f"agent_config_leaks: rg failed under {root}", file=sys.stderr)
    return [root / line for line in proc.stdout.decode().splitlines() if line]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", action="append", type=Path,
                        help="directory to search (repeatable; default: cwd)")
    parser.add_argument("--history", action="store_true",
                        help="also scan each file's git history")
    parser.add_argument("--json", action="store_true", help="JSON list of files with findings")
    args = parser.parse_args()
    missing = [t for t in ("rg", "gitleaks", "git") if not shutil.which(t)]
    if missing:
        print(f"agent_config_leaks: missing {', '.join(missing)} "
              "(brew install ripgrep gitleaks git)", file=sys.stderr)
        return 2
    roots = [r.expanduser().resolve() for r in (args.root or [Path.cwd()])]
    bad = [str(r) for r in roots if not r.is_dir()]
    if bad:
        parser.error(f"--root is not a directory: {', '.join(bad)}")
    files = sorted({p for root in roots for p in discover(root)})
    with ThreadPoolExecutor(max_workers=8) as pool:
        records = list(pool.map(lambda p: inspect(p, args.history), files))
    flagged = [r for r in records if r["findings"] or r["history"]]
    if args.json:
        print(json.dumps(flagged, indent=2, ensure_ascii=False))
    else:
        for r in flagged:
            exposure = (f"[repo={r['repo'] or '-'} tracked={'yes' if r['tracked'] else 'no'} "
                        f"ignored={'yes' if r['ignored'] else 'no'} "
                        f"visibility={r['visibility'] or '-'}]")
            for f in r["findings"]:
                print(f"{r['path']}:{f['line']}  {f['rule']}  {f['masked']}  {exposure}")
            for h in r["history"]:
                print(f"{r['path']} history {h['commit']}  {h['rule']}  {h['masked']}  {exposure}")
    for r in records:
        for err in r["errors"]:
            print(f"agent_config_leaks: {r['path']}: {err}", file=sys.stderr)
    current = sum(len(r["findings"]) for r in records)
    past = sum(len(r["history"]) for r in records)
    print(f"scanned {len(files)} file(s): {current} current + {past} history finding(s) "
          f"in {len(flagged)} file(s)", file=sys.stderr)
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())
