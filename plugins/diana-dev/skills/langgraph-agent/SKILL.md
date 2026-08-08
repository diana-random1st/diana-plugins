---
name: langgraph-agent
description: >
  Create new LangGraph agents following established patterns. Use when asked to create a new agent, graph, or node pipeline. Triggers: 'create agent', 'new agent', 'new graph', 'add agent', 'langgraph agent', 'новый агент', 'создать агента'.
---

# LangGraph Agent Creator

Project: `<project-root>/agents/src/agents/` · Base class: `graphs/base.py`

## Step 1: Clarify before generating

Ask in one message:
1. **Agent name** (snake_case, e.g. `claim_validator`)
2. **What it does** in one sentence
3. **Nodes** needed (list or describe pipeline)
4. **Needs HITL** (human-in-the-loop / resume after intervention)?
5. **Uses LLM vision / browser?** (determines if context dict needed)
6. **Delegates to sub-agents?** (orchestrator pattern)
7. **Nodes call external APIs / LLMs?** (rate-limit / retry needed)

## Step 2: Choose pattern

| Pattern | When | Key trait | Example in codebase |
|---------|------|-----------|---------------------|
| **Simple pipeline** | Linear steps, no resume | Nodes only read/write state | `graphs/three_cs_extractor/` |
| **HITL** | Can pause for human, resume from checkpoint | `set_conditional_entry_point`, context dict | `cua/` |
| **Multi-agent orchestrator** | One graph delegates work to N specialist subgraphs | Parent invokes child graphs via `invoke()` | — |
| **Robust node** | Any node calling external API / LLM that may rate-limit | `@retry` + `@limits` decorator on node | — |

Patterns compose: HITL + robust nodes, orchestrator + data contracts — all valid combos.

## Step 3: Generate files

Target: `<project-root>/agents/src/agents/graphs/{agent_name}/`

```
{agent_name}/
├── __init__.py         # export: {AgentName}Graph, {AgentName}State
├── agent.py            # {AgentName}Graph(BaseAgentGraph)
├── config.py           # {AgentName}Settings + get_{agent_name}_settings()
├── models.py           # State TypedDict, Input/Result Pydantic models
├── prompts.py          # SYSTEM_PROMPT (if LLM used)
└── nodes/
    ├── __init__.py     # export all node functions
    └── {node}.py       # one file per node
```

**Multi-agent orchestrator** adds:
```
{orchestrator_name}/
└── specialists/        # one subgraph per specialist domain
    ├── validator/
    ├── analyzer/
    └── reporter/
```

See **[api_reference.md](references/api_reference.md)** for complete code templates.

## Key rules

- **Nodes return only changed fields** — LangGraph merges, not replaces
- **Error check first in every router**: `if state.get("error"): return "error"`
- **`@node_logging()` on every node** — no exceptions
- **Context dict** — needed only for browser/vision agents (HITL pattern); in simple pipeline nodes take only `state`
- **Config always pydantic-settings** with `ENV_PREFIX_` — never hardcode values
- **`__init__.py`** must export Graph class + State for orchestrator registration

## Step 4: Verify

```bash
cd <project-root>/agents
uv run ruff check src/agents/graphs/{agent_name}/
uv run mypy src/agents/graphs/{agent_name}/
uv run pytest tests/unit/test_{agent_name}.py -v
```

Register new graph in orchestrator: `<project-root>/agents/src/agents/orchestrator/`

## Example: agentic-claim-os Project

In the agentic-claim-os project:
- Project root: `services/agents/`
- Agents: `services/agents/src/agents/graphs/`
- Base class: `services/agents/src/agents/graphs/base.py`
- Orchestrator: `services/agents/src/agents/orchestrator/`
