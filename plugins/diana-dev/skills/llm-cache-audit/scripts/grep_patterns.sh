#!/usr/bin/env bash
# Ready-made grep checks for LLM prefix-cache anti-patterns.
# Usage: ./grep_patterns.sh [path]   (default: .)
#
# Exit code 0 = no findings. Non-zero = at least one category fired.

set -u
ROOT="${1:-.}"
EXIT=0

hr() { printf '\n=== %s ===\n' "$1"; }
hit() { EXIT=1; }

ripgrep() {
  rg --hidden -n --no-heading \
     -g '!**/{node_modules,.venv,venv,dist,build,target,.git}/**' \
     -g '*.{py,ts,tsx,js,jsx,rs,go,java,kt}' \
     "$@" "$ROOT" 2>/dev/null
}

hr "A1: volatile values in system prompt assembly"
if ripgrep -e 'system[^=]*=.*(datetime\.now|time\.time|uuid\.|trace_id|run_id|session_id|request_id)'; then hit; fi
if ripgrep -e '(SYSTEM_PROMPT|system_prompt|system).{0,80}f["\x27].*\{(datetime|now|time|uuid|trace|session|request)'; then hit; fi

hr "A2: user-specific identity in system prompt"
if ripgrep -e '(SYSTEM_PROMPT|system_prompt|system).{0,80}\{(user\.|tenant|account|company|email)'; then hit; fi

hr "B1: tools / schema serialized without sort_keys"
if ripgrep -e 'json\.dumps\([^)]*\)' | grep -v 'sort_keys' >/dev/null; then
  ripgrep -e 'json\.dumps\([^)]*\)' | grep -v 'sort_keys' | head -20
  hit
fi

hr "B2: tools list built without explicit ordering"
if ripgrep -e 'tools\s*=\s*list\(.*\.values\(\)\)|tools\s*=\s*\[.*for .* in .*\..*\]'; then hit; fi

hr "B3: per-request fields embedded in json_schema / response_format"
if ripgrep -e '("const"|const:)\s*[:=].{0,40}(request_id|trace_id|tenant_id|session_id)'; then hit; fi

hr "B4: dynamic tool filtering inside an agent step"
if ripgrep -e '(tools\s*=\s*\[.*\bif\b|filter_tools|select_tools|pick_tools)\('; then hit; fi

hr "C1: messages prefix mutation (non append-only)"
if ripgrep -e 'messages\[0\]\s*=|messages\.pop\(0\)|messages\[:.*\]\s*='; then hit; fi
if ripgrep -e 'summary_of_previous|compact_history|summarize_history' ; then hit; fi

hr "D1: multiple system-prompt assembly sites (drift risk)"
SYS_SITES=$(ripgrep -lc -e '(SYSTEM_PROMPT|system_prompt|BASE_SYSTEM).*=' | wc -l | tr -d ' ')
if [ "$SYS_SITES" -gt 1 ]; then
  echo "system prompt assembled in $SYS_SITES files — verify single canonical render"
  hit
fi

hr "D2: image multimodal without normalized detail / URL"
if ripgrep -e '"detail"\s*:\s*"(high|low|auto)"'; then echo "(verify detail is the same across call sites)"; fi

hr "E1: round-robin / random routing without cache key"
if ripgrep -e '(RoundRobin|random\.choice|shuffle)\(.*(replicas?|backends?|endpoints?)'; then hit; fi

hr "E2: prompt_cache_key / sticky routing usage"
if ! ripgrep -e 'prompt_cache_key|cache_key|sticky|prefix_aware|affinity' >/dev/null; then
  echo "no prompt_cache_key / sticky routing found — required for multi-replica"
  hit
fi

hr "F1: Anthropic cache_control usage"
if ripgrep -e 'cache_control' >/dev/null; then
  ripgrep -e 'cache_control.*ttl' || echo "(cache_control present, TTL not explicit — default 5min)"
else
  echo "(no cache_control found — fine if not using Anthropic)"
fi

hr "G1: usage / cached_tokens logging"
if ! ripgrep -e 'cached_tokens|cache_read_input_tokens|prompt_cache_hit_tokens|cache_creation_input_tokens'; then
  echo "no cache usage telemetry — blind to hit rate"
  hit
fi

hr "G2: prefix_hash / canonical hash logging"
if ! ripgrep -e 'prefix_hash|prompt_hash|sha256\(.*(tools|system)'; then
  echo "no prefix_hash logging — cannot diagnose drift between steps"
  hit
fi

printf '\n'
if [ "$EXIT" -eq 0 ]; then
  echo "clean: no obvious anti-patterns found by grep"
else
  echo "findings present — review categories above"
fi
exit "$EXIT"
