# LangGraph Agent Patterns — agentic-claim-os

## Table of Contents
1. [State TypedDict](#1-state-typeddict)
2. [Node function](#2-node-function)
3. [Node with shared context (HITL/browser)](#3-node-with-shared-context)
4. [Routing function](#4-routing-function)
5. [Config (pydantic-settings)](#5-config)
6. [Simple pipeline graph](#6-simple-pipeline-graph)
7. [HITL graph with resume](#7-hitl-graph-with-resume)
8. [Models: Input/Result](#8-models-inputresult)
9. [Key imports cheatsheet](#9-key-imports)
10. [Multi-agent orchestrator](#10-multi-agent-orchestrator)
11. [Data contracts between agents](#11-data-contracts-between-agents)
12. [Robust node (retry + rate limiting)](#12-robust-node)

---

## 1. State TypedDict

```python
from typing import Annotated, Any, Literal, NotRequired, Required, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class MyAgentState(TypedDict, total=False):
    # ---- Required (base AgentState) ----
    execution_id: Required[str]
    messages: Required[Annotated[list[BaseMessage], add_messages]]
    status: Required[Literal["running", "completed", "failed", "paused", "needs_intervention"]]

    # ---- Optional base ----
    error: NotRequired[str | None]
    escalate_to_human: NotRequired[bool]
    pause_reason: NotRequired[str | None]

    # ---- Domain-specific input ----
    input_raw: NotRequired[dict[str, Any] | None]
    task: NotRequired[MyTaskInput | None]

    # ---- Processing ----
    intermediate_result: NotRequired[SomeModel | None]

    # ---- Output ----
    result: NotRequired[MyResult | None]
```

**Rules:**
- `total=False` — all fields optional by default, mark required ones with `Required[...]`
- `messages` always uses `add_messages` reducer (appends, not replaces)
- For HITL: add `is_resuming`, `intervention_input`, `intervention`, `paused_at_ms`

---

## 2. Node function

Simple node (no shared context):

```python
from typing import Any
from agents.graphs.base import node_logging
from agents.utils.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

@node_logging()
async def validate_input(state: MyAgentState) -> dict[str, Any]:
    """Validate and parse input."""
    input_raw = state.get("input_raw")
    if not input_raw:
        return {"error": "No input provided"}

    try:
        task = MyTaskInput(**input_raw)
        logger.info("input_validated", execution_id=state.get("execution_id"))
        return {"task": task}
    except Exception as e:
        return {"error": f"Invalid input: {e}"}
```

**Rules:**
- `@node_logging()` always first
- Return only fields that changed
- Error → `return {"error": "description"}` (not raise)
- Log with structlog style: `logger.info("event_name", key=value)`

---

## 3. Node with shared context

For browser/vision agents where nodes share state across calls (screenshots, sessions):

```python
@node_logging()
async def observe(state: MyAgentState, context: dict[str, Any]) -> dict[str, Any]:
    """Observe page state. Context holds browser_session."""
    session = context.get("browser_session")
    if not session:
        return {"error": "No active browser session"}

    screenshot_bytes = await session.screenshot_bytes()
    # Store in context for next node (decide)
    context["last_screenshot_b64"] = base64.b64encode(screenshot_bytes).decode()

    return {"current_url": session.get_url()}
```

Context is injected via `wrap_node` closure in `_build_graph()` — see Graph section.

---

## 4. Routing function

```python
from typing import Literal

def route_after_validate(state: MyAgentState) -> Literal["process", "handle_error"]:
    """Route after validation."""
    if state.get("error"):        # Always check error FIRST
        return "handle_error"
    if not state.get("task"):
        return "handle_error"
    return "process"

def route_after_process(
    state: MyAgentState,
) -> Literal["finalize", "request_intervention", "error"]:
    """Multi-way routing."""
    if state.get("error"):
        return "error"
    if state.get("status") == "needs_intervention":
        return "request_intervention"
    return "finalize"
```

---

## 5. Config

```python
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class MyAgentSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MY_AGENT_")

    max_steps: int = Field(default=50, ge=1, le=200)
    llm_max_tokens: int = Field(default=1024, ge=100, le=8192)
    llm_temperature: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_threshold: float = Field(default=0.8, ge=0.0, le=1.0)

@lru_cache
def get_my_agent_settings() -> MyAgentSettings:
    """Get cached settings instance."""
    return MyAgentSettings()
```

Env prefix convention: `{AGENT_NAME}_` in SCREAMING_SNAKE_CASE.

---

## 6. Simple pipeline graph

No shared context, no resume. Pattern from `three_cs_extractor`.

```python
import functools
from typing import Any
from langgraph.graph import END, StateGraph
from agents.graphs.base import BaseAgentGraph, GraphConfig

class MyAgentGraph(BaseAgentGraph):
    def __init__(self, config: GraphConfig | None = None) -> None:
        if config is None:
            config = GraphConfig(
                name="my_agent",
                version="1.0.0",
                description="Does X",
                timeout_seconds=300.0,
                enable_streaming=True,
            )
        super().__init__(config)

    def _build_graph(self) -> StateGraph[MyAgentState]:
        graph: StateGraph[MyAgentState] = StateGraph(MyAgentState)

        # Add nodes
        graph.add_node("validate_input", validate_input)
        graph.add_node("process", process)
        graph.add_node("finalize", finalize)
        graph.add_node("handle_error", handle_error)

        # Entry point
        graph.set_entry_point("validate_input")

        # Conditional edges
        graph.add_conditional_edges(
            "validate_input",
            route_after_validate,
            {"process": "process", "handle_error": "handle_error"},
        )
        graph.add_conditional_edges(
            "process",
            route_after_process,
            {"finalize": "finalize", "handle_error": "handle_error"},
        )

        # Terminal
        graph.add_edge("finalize", END)
        graph.add_edge("handle_error", END)

        return graph
```

---

## 7. HITL graph with resume

Adds context dict injection and conditional entry point. Pattern from `cua/graph/agent.py`.

```python
import functools
from collections.abc import Callable, Coroutine
from typing import Any, Literal
from langgraph.graph import END, StateGraph
from langgraph.graph.state import StateNode
from agents.graphs.base import BaseAgentGraph, GraphConfig

class MyHITLGraph(BaseAgentGraph):
    def _build_graph(self) -> StateGraph[MyAgentState]:
        graph: StateGraph[MyAgentState] = StateGraph(MyAgentState)

        # Fresh context per graph invocation
        context: dict[str, Any] = {}

        def wrap_node(
            node_fn: Callable[[MyAgentState, dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]],
        ) -> StateNode[MyAgentState, None]:
            @functools.wraps(node_fn)
            async def wrapped(state: MyAgentState) -> dict[str, Any]:
                return await node_fn(state, context)
            return wrapped

        # Add nodes (all wrapped with context)
        graph.add_node("validate_input", wrap_node(validate_input))
        graph.add_node("process", wrap_node(process))
        graph.add_node("request_intervention", wrap_node(request_intervention))
        graph.add_node("process_intervention_input", wrap_node(process_intervention_input))
        graph.add_node("finalize", wrap_node(finalize))

        # Conditional entry point for resume support
        graph.set_conditional_entry_point(
            route_entry_point,
            {
                "validate_input": "validate_input",
                "process_intervention_input": "process_intervention_input",
            },
        )

        # Edges...
        graph.add_conditional_edges(
            "validate_input",
            route_after_validate,
            {"process": "process", "error": "finalize"},
        )
        graph.add_conditional_edges(
            "process_intervention_input",
            route_after_intervention,
            {"process": "process", "finalize": "finalize"},
        )

        # Intervention pauses graph
        graph.add_edge("request_intervention", END)
        graph.add_edge("finalize", END)

        return graph


# Entry point router for HITL
def route_entry_point(
    state: MyAgentState,
) -> Literal["validate_input", "process_intervention_input"]:
    if state.get("is_resuming") and state.get("intervention_input") is not None:
        return "process_intervention_input"
    return "validate_input"
```

---

## 8. Models: Input/Result

```python
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from agents.utils.datetime import utc_now

class MyTaskInput(BaseModel):
    """Input for agent execution."""
    model_config = ConfigDict(str_strip_whitespace=True)

    task_id: str = Field(..., description="Unique task identifier")
    task_description: str = Field(..., min_length=3, max_length=2000)
    max_steps: int = Field(default=50, ge=1, le=200)

class MyResult(BaseModel):
    """Final output from agent execution."""
    model_config = ConfigDict(str_strip_whitespace=True)

    success: bool
    summary: str
    extracted_data: dict[str, Any] = Field(default_factory=dict)
    steps_completed: int = Field(default=0)
    processing_time_ms: int = Field(default=0)
    had_errors: bool = Field(default=False)
    error_message: str | None = Field(default=None)
    generation_timestamp: datetime = Field(default_factory=utc_now)
```

---

## 9. Key imports

```python
# Graph base
from agents.graphs.base import BaseAgentGraph, GraphConfig, node_logging, AgentState
from agents.graphs.base import create_error_handler, should_continue, merge_dicts

# LangGraph
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

# LLM
from agents.providers.factory import get_llm_provider

# State typing
from typing import Annotated, Any, Literal, NotRequired, Required, TypedDict
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

# Pydantic
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Logging
from agents.utils.logging import configure_logging, get_logger
```

---

## 10. Multi-agent orchestrator

Orchestrator graph invokes specialist subgraphs as regular nodes. Each specialist is a fully compiled `BaseAgentGraph`.

```python
# orchestrator/agent.py
from langgraph.graph import END, StateGraph
from agents.graphs.base import BaseAgentGraph, GraphConfig
from agents.graphs.specialists.validator import ValidatorGraph
from agents.graphs.specialists.analyzer import AnalyzerGraph

class OrchestratorGraph(BaseAgentGraph):
    def __init__(self) -> None:
        super().__init__(GraphConfig(name="orchestrator", version="1.0.0", description="..."))
        # Compile specialists once — reused across invocations
        self._validator = ValidatorGraph().compile()
        self._analyzer = AnalyzerGraph().compile()

    def _build_graph(self) -> StateGraph[OrchestratorState]:
        graph: StateGraph[OrchestratorState] = StateGraph(OrchestratorState)

        graph.add_node("validate", self._node_validate)
        graph.add_node("analyze", self._node_analyze)
        graph.add_node("aggregate", aggregate_results)
        graph.add_node("handle_error", handle_error)

        graph.set_entry_point("validate")
        graph.add_conditional_edges(
            "validate",
            route_after_validate,
            {"analyze": "analyze", "handle_error": "handle_error"},
        )
        graph.add_edge("analyze", "aggregate")
        graph.add_edge("aggregate", END)
        graph.add_edge("handle_error", END)
        return graph

    @node_logging()
    async def _node_validate(self, state: OrchestratorState) -> dict:
        result = await self._validator.ainvoke({"input_raw": state.get("input_raw")})
        if result.get("error"):
            return {"error": f"Validator: {result['error']}"}
        return {"validated_data": result.get("result")}

    @node_logging()
    async def _node_analyze(self, state: OrchestratorState) -> dict:
        result = await self._analyzer.ainvoke({"data": state.get("validated_data")})
        if result.get("error"):
            return {"error": f"Analyzer: {result['error']}"}
        return {"analysis": result.get("result")}
```

**Rules:**
- Specialists compiled in `__init__`, not per-invocation
- Orchestrator's state is **flat** — each specialist result mapped to a named field
- Error from specialist propagates as `{"error": "SpecialistName: reason"}`
- Specialists are regular `BaseAgentGraph` subclasses — testable in isolation

---

## 11. Data contracts between agents

Enforce explicit input/output at agent boundaries with Pydantic validation nodes.

```python
# nodes/validate_contract.py
from pydantic import ValidationError
from agents.graphs.specialists.validator import ValidatorInput

@node_logging()
async def validate_specialist_contract(state: OrchestratorState) -> dict:
    """Validate data meets specialist's contract before delegation."""
    try:
        contract = ValidatorInput(
            document_id=state.get("document_id"),
            customer_id=state.get("customer_id"),
            amount=state.get("amount"),
        )
        return {"validator_input": contract.model_dump()}
    except ValidationError as e:
        missing = [err["loc"][0] for err in e.errors()]
        return {"error": f"Missing required fields for validator: {missing}"}
```

**Specialist input model (define in specialist's `models.py`):**

```python
# specialists/validator/models.py
class ValidatorInput(BaseModel):
    """CONTRACT: Orchestrator must provide all these fields."""
    model_config = ConfigDict(str_strip_whitespace=True)

    document_id: str = Field(..., description="Document to validate")
    customer_id: str = Field(..., description="Customer identifier")
    amount: float = Field(..., gt=0, description="Requested amount")

class ValidatorResult(BaseModel):
    """CONTRACT: What orchestrator can expect back."""
    is_valid: bool
    validation_errors: list[str] = Field(default_factory=list)
    validated_at: datetime = Field(default_factory=utc_now)
```

**Rules:**
- Every specialist defines `{Name}Input` + `{Name}Result` in its `models.py`
- Orchestrator validates input before delegation, not after
- Contract violation → `{"error": "Missing fields: [...]"}`, never partial invocation

---

## 12. Robust node

For nodes that call external APIs or LLMs that may rate-limit or fail transiently.

```python
# nodes/call_llm.py
from ratelimit import limits, sleep_and_retry
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

# Tune to provider limits (e.g. Anthropic: 50 RPM tier-1)
_CALLS_PER_MINUTE = 40
_RETRY_ATTEMPTS = 5

def _is_transient_error(exc: BaseException) -> bool:
    """Classify errors worth retrying."""
    msg = str(exc).lower()
    return any(kw in msg for kw in ("rate_limit", "overloaded", "529", "503", "timeout"))

@sleep_and_retry
@limits(calls=_CALLS_PER_MINUTE, period=60)
@retry(
    stop=stop_after_attempt(_RETRY_ATTEMPTS),
    wait=wait_exponential(multiplier=2, min=4, max=30),
    retry=retry_if_exception(_is_transient_error),
    reraise=True,
)
async def _call_with_retry(llm, messages: list) -> str:
    response = await llm.ainvoke(messages)
    return response.content

@node_logging()
async def call_llm(state: MyAgentState) -> dict:
    llm = get_llm_provider()
    messages = build_messages(state)
    try:
        content = await _call_with_retry(llm, messages)
        return {"llm_response": content}
    except Exception as e:
        return {"error": f"LLM call failed after {_RETRY_ATTEMPTS} attempts: {e}"}
```

**Dependencies:**

```toml
# pyproject.toml
ratelimit = ">=2.2.1"
tenacity = ">=8.2.0"
```

**Rules:**
- `@sleep_and_retry` + `@limits` = hard rate cap, auto-sleeps until window resets
- `@retry` wraps only transient errors — don't retry auth failures or bad input
- Node itself is `async`; `_call_with_retry` is sync (ratelimit lib) — wrap with `asyncio.to_thread` if needed
- Tune `_CALLS_PER_MINUTE` per provider; store in `config.py` as `llm_rpm: int`
