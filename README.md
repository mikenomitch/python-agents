# Build and deploy a Python AI Agent on Cloudflare

This repo shows how to build and run a Python AI agent on Cloudflare Workers, with the Cloudflare Agents runtime handling deployment, scaling, and infrastructure concerns.

This repo gives you a Python-first SDK for [Cloudflare Agents](https://developers.cloudflare.com/agents/?utm_content=agents.cloudflare.com) so you can stay in Python while deploying globally on Cloudflare Workers.

## Why Cloudflare for Python Agents?

- **Runs globally** by default, so latency is usually good without extra setup.
- **No server babysitting**: no VMs, no Kubernetes setup, no custom autoscaling logic.
- **Useful agent features included**: state, scheduling, queues, routing, and MCP support.
- **Feels like Python**: decorators and APIs that follow normal Python conventions.
- **Can grow with you**: starts simple, but works for production workloads too.

---

## What this package is

`agents-py` is a Python interface for Cloudflare Agents in Workers.

You get:

- A Python `Agent` wrapper with methods for:
  - state
  - schedules
  - queues
  - MCP servers and tools
- `@callable` and `@tool` decorators for discoverable methods
- Routing helpers for HTTP/agent dispatch
- A clean API surface that feels Pythonic (`snake_case`, typed-friendly patterns)

> Want architecture details or how the JS bridge works internally?
> See **[Technical internals](docs/technical-internals.md)**.

---

## 5-minute mental model (for newcomers)

Think of a Cloudflare Agent as:

1. **Logic**: your Python methods (what the agent can do)
2. **State**: durable data for conversations/workflows
3. **Entry points**: how requests are routed to your agent
4. **Background work**: schedules + queue jobs
5. **Tool surface**: callable methods and MCP tools

This SDK helps you express each part in Python.

---

## Quick start

### 1) Dependency

Make sure `python-agents` is available in your project dependencies.

### 2) Create an agent and persist state

```python
from python_agents import Agent


async def build_counter(env, ctx):
    agent = Agent.create(state={"count": 0}, env=env, ctx=ctx)
    await agent.set_state({"count": 1})
    return agent
```

### 3) Add callable methods (tool-like actions)

```python
from python_agents import call_callable, callable


class SupportTools:
    @callable
    async def lookup_order(self, order_id: str) -> dict:
        return {"order_id": order_id, "status": "shipped"}

    @callable
    def refund_policy(self) -> str:
        return "Refunds are allowed within 30 days."


async def run_tool_call(tool_name: str, arguments: dict):
    tools = SupportTools()
    return await call_callable(tools, tool_name, **arguments)
```

### 4) Route HTTP requests to your agent

```python
from python_agents import route_agent_request


async def fetch(request, env, ctx):
    return await route_agent_request(
        request,
        env,
        {"namespace": "chat", "name": "assistant"},
    )
```

---

## Core concepts you will use most

### 1) Agent state

Keep memory or workflow status in agent state:

```python
await agent.set_state({"thread_id": "t_123", "step": "triage"})
```

### 2) MCP tools

Expose structured tools for model/tool ecosystems:

```python
from python_agents import register_mcp_tools, tool


class SupportTools:
    @tool(input_schema={"order_id": "string"})
    async def lookup_order(self, order_id: str):
        return {"content": [{"type": "text", "text": f"order:{order_id}"}]}


async def init_mcp(server):
    register_mcp_tools(server, SupportTools())
```

### 3) Scheduled jobs

Run work later or repeatedly:

```python
await agent.schedule({"type": "email-digest"}, "2026-01-01T00:00:00Z")
await agent.schedule_every({"type": "refresh-cache"}, "5 minutes")
```

### 4) Queue-based work

Push long-running or async jobs into a queue:

```python
await agent.queue({"job": "index-document", "doc_id": "doc_42"})
job = await agent.dequeue()
```


## More practical examples (with context)

These are common patterns teams ask for after the first deploy.

### Inspect which callable methods are exposed

Useful when you want to verify which methods your agent/tooling layer can discover.

```python
from python_agents import callable, get_callable_methods


class MathAgent:
    @callable
    async def multiply(self, left: int, right: int) -> int:
        return left * right

    @callable(name="sum")
    def add(self, left: int, right: int) -> int:
        return left + right


agent = MathAgent()
methods = get_callable_methods(agent)
assert set(methods) == {"multiply", "sum"}
```

### Call an MCP tool directly in local tests

Helpful when validating tool behavior without a full MCP transport round-trip.

```python
from python_agents import call_tool


result = await call_tool(SupportTools(), "lookup_order", {"order_id": "123"})
```

### Resolve an agent by name from anywhere in your Worker logic

Use this for internal orchestration, inspection, or administrative operations.

```python
from python_agents import get_agent_by_name


async def inspect_agent_state():
    agent = await get_agent_by_name("chat", "assistant")
    return agent.state
```

### Connect external MCP servers to an agent

This lets your agent discover/use tools hosted by another MCP-capable service.

```python
await agent.add_mcp_server({
    "name": "docs",
    "transport": "http",
    "url": "https://mcp.example.com",
})

servers = await agent.get_mcp_servers()
```

---

## Full API reference (with examples)

This section covers everything exported by `python_agents`.

### `Agent`

Python wrapper around a JavaScript Cloudflare Agent instance.

#### `Agent.create(state=None, env=None, ctx=None) -> Agent`

Create a new `Agent` wrapper.

```python
from python_agents import Agent


agent = Agent.create(state={"count": 0}, env=env, ctx=ctx)
```

#### Properties: `agent.state`, `agent.env`, `agent.ctx`

Read the underlying runtime state, environment bindings, and execution context.

```python
current_state = agent.state
bindings = agent.env
execution_context = agent.ctx
```

#### `await agent.call(method, *args)`

Call a method by name (snake_case names are mapped to JS camelCase for you).

```python
await agent.call("set_state", {"status": "ready"})
await agent.call("schedule_every", {"type": "sync"}, "10 minutes")
```

#### Direct Agent methods

The wrapper exposes common methods directly as `await agent.<method>(...)`:

- `set_state`
- `schedule`
- `schedule_every`
- `get_schedules`
- `cancel_schedule`
- `queue`
- `dequeue`
- `dequeue_all`
- `get_queue`
- `broadcast`
- `run_workflow`
- `wait_for_approval`
- `add_mcp_server`
- `remove_mcp_server`
- `get_mcp_servers`
- `reply_to_email`

```python
await agent.set_state({"step": "triage"})
await agent.schedule({"type": "email-digest"}, "2026-01-01T00:00:00Z")
await agent.schedule_every({"type": "refresh-cache"}, "5 minutes")
await agent.get_schedules()
await agent.cancel_schedule("schedule-id-123")
await agent.queue({"job": "index", "doc_id": "doc_42"})
await agent.dequeue()
await agent.dequeue_all()
await agent.get_queue()
await agent.broadcast({"type": "notification", "payload": {"message": "build complete"}})
await agent.run_workflow({"name": "onboarding", "input": {"user_id": "u_123"}})
await agent.wait_for_approval({"request_id": "approval_1"})
await agent.add_mcp_server({"name": "docs", "transport": "http", "url": "https://mcp.example.com"})
await agent.remove_mcp_server("docs")
await agent.get_mcp_servers()
await agent.reply_to_email({"to": "user@example.com", "subject": "Update", "text": "Your request is complete."})
```

### Callable-method helpers

Use these when you want discoverable methods that can be called by name.

#### `@callable(name=None)`

Mark an instance method as callable.

```python
from python_agents import callable


class Actions:
    @callable
    async def ping(self) -> str:
        return "pong"

    @callable(name="sum")
    def add(self, left: int, right: int) -> int:
        return left + right
```

#### `get_callable_methods(obj) -> dict[str, callable]`

List exposed callable methods by name.

```python
from python_agents import get_callable_methods


methods = get_callable_methods(Actions())
assert set(methods) == {"ping", "sum"}
```

#### `await call_callable(obj, name, *args, **kwargs)`

Call a registered callable method by name.

```python
from python_agents import call_callable


result = await call_callable(Actions(), "sum", 2, 3)
assert result == 5
```

### MCP tool helpers

Use these to expose MCP-compatible tools from Python methods.

#### `@tool(name=None, description=None, input_schema=None)`

Mark a method as an MCP tool and optionally attach metadata.

```python
from python_agents import tool


class SupportTools:
    @tool(
        description="Look up an order by ID",
        input_schema={"order_id": "string"},
    )
    async def lookup_order(self, order_id: str):
        return {"content": [{"type": "text", "text": f"order:{order_id}"}]}
```

#### `get_tool_methods(obj) -> dict[str, callable]`

List tool methods exposed by an object.

```python
from python_agents import get_tool_methods


tools = get_tool_methods(SupportTools())
assert "lookup_order" in tools
```

#### `await call_tool(obj, name, arguments=None)`

Call a tool directly using an MCP-style argument object.

```python
from python_agents import call_tool


result = await call_tool(SupportTools(), "lookup_order", {"order_id": "123"})
```

#### `register_mcp_tools(server, obj) -> None`

Register all `@tool` methods from an object onto an MCP server.

```python
from python_agents import register_mcp_tools


register_mcp_tools(server, SupportTools())
```

### Routing and agent lookup helpers

#### `await route_agent_request(*args)`

Route a single request through Cloudflare's agent router.

```python
from python_agents import route_agent_request


response = await route_agent_request(request, env, {"namespace": "chat", "name": "assistant"})
```

#### `await route_agent_requests(*args)`

Alias of `route_agent_request` (plural naming for parity with some examples/docs).

```python
from python_agents import route_agent_requests


response = await route_agent_requests(request, env, {"namespace": "chat", "name": "assistant"})
```

#### `await get_agent_by_name(*args) -> Agent`

Look up an agent and return it wrapped as `Agent`.

```python
from python_agents import get_agent_by_name


agent = await get_agent_by_name("chat", "assistant")
```

#### `await get_agent_by_id(*args) -> Agent`

Look up an agent by ID and return it wrapped as `Agent`.

```python
from python_agents import get_agent_by_id


agent = await get_agent_by_id("chat", "agent-id-123")
```

### Additional runtime wrappers

These wrap more of the Cloudflare Agents JS SDK in a Python-friendly way.

#### `McpAgent`

Wrapper around JS `McpAgent`.

- `McpAgent.create(state=None, env=None, ctx=None) -> McpAgent`
- `await mcp_agent.call(method, *args)`
- Direct async method access via `await mcp_agent.some_method(...)`
- Properties: `mcp_agent.state`, `mcp_agent.env`, `mcp_agent.ctx`

```python
from python_agents import McpAgent


mcp_agent = McpAgent.create(state={"session": "abc"}, env=env, ctx=ctx)
```

#### `AgentWorkflow`

Wrapper around JS `AgentWorkflow`.

- `AgentWorkflow.create(init=None) -> AgentWorkflow`
- `await workflow.call(method, *args)`
- Direct async method access via `await workflow.some_method(...)`

```python
from python_agents import AgentWorkflow


workflow = AgentWorkflow.create({"name": "onboarding"})
```

#### `create_mcp_handler(*args)`

Python wrapper for JS `createMcpHandler`.

```python
from python_agents import create_mcp_handler


handler = create_mcp_handler({"agent": "support"})
```

#### `await route_agent_email(*args)`

Python wrapper for JS `routeAgentEmail`.

```python
from python_agents import route_agent_email


result = await route_agent_email(message, env, resolver)
```

#### `create_address_based_email_resolver(*args)`

Python wrapper for JS `createAddressBasedEmailResolver`.

```python
from python_agents import create_address_based_email_resolver


resolver = create_address_based_email_resolver({"support@example.com": "support-agent"})
```

## Next steps

- Read Cloudflare Agents docs: <https://developers.cloudflare.com/agents/?utm_content=agents.cloudflare.com>
- Explore examples in this repo: [`examples/`](examples)
- Review internals (optional): **[Technical internals](docs/technical-internals.md)**

If you're coming from "just Python" and want the easiest way to get an agent running on the edge, start here.
