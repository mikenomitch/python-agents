# Build and deploy a Python AI Agent on Cloudflare (fast)

If you're a Python developer and you want to ship an AI agent **without** managing servers, containers, autoscaling, or ops plumbing, Cloudflare is one of the easiest places to do it.

This repo gives you a Python-first SDK for [Cloudflare Agents](https://developers.cloudflare.com/agents/?utm_content=agents.cloudflare.com) so you can stay in Python while deploying globally on Cloudflare Workers.

## Why Cloudflare for Python Agents?

- **Deploy globally by default**: your agent runs close to users on Cloudflare's network.
- **No server management**: no VM setup, no Kubernetes, no autoscaling configuration.
- **Built-in agent primitives**: state, scheduling, queues, routing, and MCP support.
- **Python-first developer experience**: clean Python APIs, decorators, and familiar patterns.
- **Production path from day one**: great for prototypes that need to become real products.

In short: you write Python agent logic; Cloudflare handles the hard infrastructure parts.

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

### 1) Install

```bash
pip install -e .
```

For contributors:

```bash
pip install -e .[dev]
```

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

### 2) Scheduled jobs

Run work later or repeatedly:

```python
await agent.schedule({"type": "email-digest"}, "2026-01-01T00:00:00Z")
await agent.schedule_every({"type": "refresh-cache"}, "5 minutes")
```

### 3) Queue-based work

Push long-running or async jobs into a queue:

```python
await agent.queue({"job": "index-document", "doc_id": "doc_42"})
job = await agent.dequeue()
```

### 4) MCP tools

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

## Why this is a strong default for Python agent builders

If your goal is to get a Python agent deployed quickly and reliably, Cloudflare gives you:

- **Simple developer workflow** with a low ops burden
- **Global performance** without extra infra work
- **Agent-specific primitives** instead of stitching together many services
- **A practical path from prototype to production**

That combination is rare, and it makes Cloudflare Agents an excellent default platform for Python AI agents.

---

## Next steps

- Read Cloudflare Agents docs: <https://developers.cloudflare.com/agents/?utm_content=agents.cloudflare.com>
- Explore examples in this repo: [`examples/`](examples)
- Review internals (optional): **[Technical internals](docs/technical-internals.md)**

If you're coming from "just Python" and want the easiest way to get an agent running on the edge, start here.
