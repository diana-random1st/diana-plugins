#!/usr/bin/env bash
# precommit_gate.sh - diana-commit gate on the STAGED changes, run before `git commit`.
#
# Usage: precommit_gate.sh [--repo DIR] [--print-gate] [--dry-run]
#
#   1. gitleaks git --pre-commit --staged on the staged diff. Prints RuleID and
#      file:line only; values stay redacted.
#   2. Refuses staged secret files: .env* (except *.example / *.sample /
#      *.template), *.pem, *.key, id_rsa / id_dsa / id_ecdsa / id_ed25519 (+ _sk).
#      Deletions are allowed.
#   3. s5d repos (.s5d/ exists): runs `s5d codebase sync --staged`; if
#      .s5d/codebase then differs from the index -> exit 3, `git add .s5d/codebase`
#      and re-run. --dry-run prints the sync command instead of running it.
#   --print-gate  also prints the repo's own gate commands (does not run them):
#      Makefile targets lint/test/check/pr_check* (root and one level down),
#      .pre-commit-config.yaml, `run:` lines of workflow jobs named *test*/*lint*.
#
# Examples:
#   precommit_gate.sh
#   precommit_gate.sh --repo ~/src/pm/pregmate-api --print-gate
#
# Exit codes:
#   0 clean
#   1 gitleaks found a leak in the staged diff -> do not commit
#   2 a forbidden file is staged -> git restore --staged <file>
#   3 the s5d snapshot changed -> git add .s5d/codebase, then re-run
#   4 cannot run: bad flag, not a git repo, gitleaks/jq/s5d missing or failed
set -uo pipefail

repo=.
print_gate=0
dry_run=0
while [ $# -gt 0 ]; do
  case "$1" in
    --repo) [ $# -ge 2 ] || { echo "precommit_gate: --repo needs a directory" >&2; exit 4; }
            repo=$2; shift 2 ;;
    --print-gate) print_gate=1; shift ;;
    --dry-run) dry_run=1; shift ;;
    -h|--help) sed -n '2,/^set -uo/p' "$0" | sed '$d; s/^# \{0,1\}//'; exit 0 ;;
    *) echo "precommit_gate: unknown argument '$1' (see --help)" >&2; exit 4 ;;
  esac
done

top=$(git -C "$repo" rev-parse --show-toplevel 2>/dev/null) \
  || { echo "precommit_gate: $repo is not inside a git work tree" >&2; exit 4; }
cd "$top" || exit 4
for tool in gitleaks jq; do
  command -v "$tool" >/dev/null \
    || { echo "precommit_gate: $tool not found (brew install $tool)" >&2; exit 4; }
done

show_gate() {
  local found=0 mk dir t wf
  echo "GATE (the repo's own; run it, this script does not):"
  for mk in Makefile */Makefile; do
    [ -f "$mk" ] || continue
    dir=${mk%/Makefile}
    while IFS= read -r t; do
      found=1
      if [ "$mk" = Makefile ]; then echo "  make $t"; else echo "  make -C $dir $t"; fi
    done < <(grep -Eo '^(lint|test|check|pr_check)[A-Za-z0-9_.-]*:([^=]|$)' "$mk" \
               | sed -E 's/:.*$//' | sort -u)
  done
  if [ -f .pre-commit-config.yaml ]; then
    found=1; echo "  pre-commit run   # .pre-commit-config.yaml"
  fi
  for wf in .github/workflows/*.yml .github/workflows/*.yaml; do
    [ -f "$wf" ] || continue
    # run: lines (inline or block scalar) of jobs whose id contains test or lint
    while IFS= read -r t; do found=1; echo "  $t"; done < <(awk '
      function ind(s) { match(s, /^ */); return RLENGTH }
      blk && /^[[:space:]]*$/ { next }
      blk { if (ind($0) > blk_ind) { l = $0; sub(/^ +/, "", l)
                                     print FILENAME " [" job "]: " l; next }
            blk = 0 }
      /^jobs:[[:space:]]*$/ { in_jobs = 1; job_ind = -1; next }
      in_jobs && /^[^[:space:]#]/ { in_jobs = 0 }
      !in_jobs || /^[[:space:]]*(#.*)?$/ { next }
      { i = ind($0); if (job_ind < 0) job_ind = i }
      i == job_ind && /^ *[A-Za-z0-9_.-]+:/ { job = $0; sub(/^ */, "", job)
                                              sub(/:.*/, "", job); next }
      tolower(job) !~ /test|lint/ { next }
      match($0, /^[[:space:]]*(- )?run:[[:space:]]*/) {
        v = substr($0, RLENGTH + 1)
        if (v ~ /^[|>][-+]?[[:space:]]*$/) { blk = 1; blk_ind = i }
        else if (v != "") print FILENAME " [" job "]: " v
      }' "$wf")
  done
  [ "$found" = 1 ] || echo "  none found -> generic fallback (SKILL.md step 3)"
}
[ "$print_gate" = 1 ] && show_gate

# 1. gitleaks on the staged diff; exit code 10 = leaks, anything else non-zero = tool error
report=$(gitleaks git --pre-commit --staged --redact --no-banner --log-level error \
           --exit-code 10 -f json -r - .)
rc=$?
leak=0
case "$rc" in
  0) ;;
  10) leak=1
      echo "LEAK (gitleaks, values redacted):"
      printf '%s' "$report" | jq -r '.[] | "  \(.RuleID)  \(.File):\(.StartLine)"' ;;
  *) echo "precommit_gate: gitleaks failed (exit $rc), see its stderr above" >&2; exit 4 ;;
esac

# 2. forbidden staged files (added/copied/modified/renamed; deletions pass)
forbidden=()
while IFS= read -r -d '' f; do
  case "${f##*/}" in
    .env*.example|.env*.sample|.env*.template) ;;
    .env*|*.pem|*.key|id_rsa|id_dsa|id_ecdsa|id_ed25519|id_ecdsa_sk|id_ed25519_sk)
      forbidden+=("$f") ;;
  esac
done < <(git diff --cached --name-only --diff-filter=ACMR -z)
if [ ${#forbidden[@]} -gt 0 ]; then
  echo "FORBIDDEN staged file(s) (git restore --staged <file>):"
  printf '  %s\n' "${forbidden[@]}"
fi
[ "$leak" = 1 ] && exit 1
[ ${#forbidden[@]} -gt 0 ] && exit 2

# 3. s5d snapshot: sync from the index, then require it staged
s5d_state="n/a"
if [ -d .s5d ]; then
  if [ "$dry_run" = 1 ]; then
    echo "DRY-RUN: would run 's5d codebase sync --staged' in $top"
    s5d_state="dry-run"
  else
    command -v s5d >/dev/null || { echo "precommit_gate: .s5d/ exists but s5d is not on PATH" >&2; exit 4; }
    s5d codebase sync --staged >&2 || { echo "precommit_gate: s5d codebase sync --staged failed" >&2; exit 4; }
    if ! git diff --quiet -- .s5d/codebase \
       || [ -n "$(git ls-files --others --exclude-standard -- .s5d/codebase)" ]; then
      echo "S5D snapshot changed: git add .s5d/codebase, then re-run this gate"
      exit 3
    fi
    s5d_state="synced"
  fi
fi
echo "CLEAN: gitleaks 0 leaks, no forbidden files, s5d $s5d_state"
exit 0
