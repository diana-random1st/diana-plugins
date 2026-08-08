---
name: llm-cache-audit
description: "Audit an LLM or agent project for prefix-cache anti-patterns — volatile data in the prompt prefix, unstable tool serialization, history mutation, missing observability."
triggers: ["cache audit", "prefix cache", "llm cache", "kv cache", "cached_tokens low", "prompt caching review"]
---

# LLM Cache Audit

Systematic audit for prefix-cache anti-patterns. Cache works only when: (1) requests share an identical prefix, (2) the request lands on a warm replica, (3) the cache survives until next request.

## When to use

Low `cached_tokens` despite a stable-looking prompt, TTFT complaints in agentic flows, before migrating providers, code review of projects calling OpenAI / Anthropic / Gemini / DeepSeek / OpenRouter / vLLM.

## Steps

**1. Scope.** Files given → audit them. Otherwise: `rg -l "openai|anthropic|google\.generativeai|deepseek|openrouter|vllm|litellm" --type py --type ts --type rs`.

**2. Detect provider and cache mode.** OpenAI = auto prefix cache. Anthropic = explicit `cache_control`, per-block breakpoints, ×1.25/×2 write surcharge. Gemini = implicit best-effort vs explicit cache objects. DeepSeek = auto, disk-backed. OpenRouter = sticky routing, top-level `cache_control` only works on direct Anthropic. vLLM = Automatic Prefix Caching.

**3. Category A — volatile data in prompt prefix (cache-killer #1).** Grep for `datetime.now | time.time | uuid.uuid4 | trace_id | run_id | session_id` in system prompt assembly. User-specific fields (`user.name`, `tenant_id`) in system prompt prevent cross-user sharing. Rule: static content → earliest position; dynamic data → user message or metadata.

**4. Category B — unstable tools list.** `dict.values()` without `sorted()` → non-deterministic order. `json.dumps` without `sort_keys=True`. `response_format` with per-request `const` values. Dynamic per-step tool filtering in 15+ step loops is an anti-pattern — use masking, constrained decoding, `allowed_tools`, or fixed route sets. More than ~50 tools → flag for deferred loading.

**5. Category C — history mutation.** Append-only? Find places rewriting `messages[0]` or early entries. Summarization applied early breaks prefix — apply only to tail or treat as new session. Tool results should be compacted while preserving paths/IDs/URLs.

**6. Category D — template drift.** Single canonical system prompt rendering path — multiple paths (web vs API vs worker) producing different bytes. Multimodal params (`detail: low|high`, image URLs with query strings) normalized. Mode switching via messages/state, never by mutating base system prompt.

**7. Category E — routing and concurrency.** Multi-replica: `prompt_cache_key` (OpenAI) or sticky routing in use. Parallel `asyncio.gather` launched after first warm-up call. OpenRouter: per-block breakpoints more portable than top-level.

**8. Category F — TTL and KV budget.** Anthropic bursty traffic >5 min: break-even `h_min = 0.25·P_miss / (1.25·P_miss − P_hit)` (~22% for Sonnet 4.6). OpenAI gpt-5/gpt-5.2: extended retention up to 24 h available. vLLM: KV eviction metrics in place?

**9. Category G — observability.** Each agent step logs `cached_tokens` / `cache_read_input_tokens`. Hash of canonical prefix (`tools + system`) logged and stable. Alert fires when hit rate drops. CI smoke test fails when `cached_tokens` drop below floor.

**10. Effective cost (if in scope).** `C = S·[(1−h)·P_miss + h·P_hit] + D·P_miss + O·P_out`. Anthropic cache write: `P_write = P_miss × 1.25` (5-min) or `× 2` (1-h). Extract S/D/O/h from logs.

**11. Report** — see `references/report-format.md`. Severity: CRITICAL (cache broken) → HIGH (hit rate degraded) → MEDIUM (provider gap) → SUGGESTION (observability).

**12. Persist findings.** `belief__observe` for recurring anti-patterns or project-specific quirks.

## What not to do

Do not recommend disabling cache. Do not recommend dynamic per-step tool filtering for 15+ step agents without computing cache-miss cost. Do not treat `cached_tokens > 0` as proof of health — measure hit rate. Do not conflate `cache_creation_input_tokens` (write, expensive) with `cache_read_input_tokens` (read, cheap).

## Helper scripts

`scripts/prefix_hash.py` — deterministic hash of `tools + system + first user message`. `scripts/grep_patterns.sh` — grep commands for categories A–E.
