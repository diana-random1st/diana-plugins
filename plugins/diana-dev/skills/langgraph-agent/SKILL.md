---
name: langgraph-agent
description: >
  Create a new LangGraph agent graph in agentic-claim-os (services/agents) following its patterns — state, nodes, routing, HITL, orchestrator registration. Triggers: 'langgraph agent', 'new graph', 'new LangGraph node pipeline', 'новый граф', 'агент на langgraph'. NOT for Claude Code subagents (use create-agents).
---

# LangGraph Agent Creator — agentic-claim-os

Repo `~/src/svsg/agentic-claim-os`, agents in `services/agents/src/agents/graphs/`, base class `graphs/base.py` (`BaseAgentGraph`, `GraphConfig`, `node_logging`, `create_error_handler`).

**The repo's own skills are the primary source** and win on any conflict with this file: `.claude/skills/new-agent` (spec → plan, no code), `agent-best-practices` (node/state/HITL/settings conventions), `post-change-checklist` (exact CI commands, live verification, PR rules). Generic LangGraph API: https://docs.langchain.com/oss/python/langgraph/overview.

## Step 1: Clarify in one message

Agent name (snake_case) · what it does in one sentence · nodes · HITL (pause and resume)? · browser/vision (needs the context dict)? · delegates to sub-agents? · nodes call external APIs or LLMs (retry/rate limit)?

## Step 2: Pattern

| Pattern | When | Example |
|---------|------|---------|
| Simple pipeline | linear, no resume | `graphs/three_cs_extractor/` |
| HITL | pause for a human, resume from checkpoint | `src/agents/cua/graph/agent.py` (context dict, conditional entry); `graphs/ford_labor_lookup/` (intervention route) |
| Orchestrator | parent invokes specialist subgraphs | `graphs/master_orchestrator/` |
| Robust node | external API / LLM that may rate-limit | `@retry` + `@limits` on the node |

Patterns compose.

## Step 3: Generate

`graphs/{agent_name}/`: `__init__.py` (export Graph + State), `agent.py`, `config.py` (pydantic-settings, `{AGENT_NAME}_` prefix), `models.py`, `prompts.py` if an LLM is used, `nodes/` one file per node. Code templates: [references/api_reference.md](references/api_reference.md).

Key rules: nodes return only changed fields · every router checks `state.get("error")` first · `@node_logging()` on every node · config never hardcoded.

## Step 4: Register and verify

Export from `graphs/__init__.py`, register in `register_default_agents()` in `src/agents/initialization.py`. Tests go in `services/agents/tests/unit/graphs/{agent_name}/`. Then, from the repo root:

```bash
uv run ruff format --check . && uv run ruff check . && make mypy
(cd services/agents && uv run pytest tests/unit -q)
```
