# agents-py

`agents-py` is a Python-first interface for building Cloudflare Agents from Python Workers.
It keeps the Cloudflare runtime behavior in the official JavaScript SDK, while giving you a clean API
(`snake_case`, decorators, helper utilities, and typed-friendly patterns).

## Installation

### From source (today)

```bash
pip install -e .
```

### For contributors

```bash
pip install -e .[dev]
```

## What you get

- A Python `Agent` wrapper around the Cloudflare Agents runtime object.
- `@callable` decorator for discoverable callable methods.
- Python routing helpers:
  - `route_agent_request`
  - `route_agent_requests` (alias)
  - `get_agent_by_name`
  - `get_agent_by_id`
- Built-in wrappers for schedules, queue operations, MCP, workflows, and state.

## Quick start: create and mutate an agent

```python
from python_agents import Agent


async def build_counter(env, ctx):
    agent = Agent.create(state={"count": 0}, env=env, ctx=ctx)
    await agent.set_state({"count": 1})
    return agent
```

## Tool-calling example

A practical pattern is to model tools as `@callable` methods and let your LLM choose one.

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
    # tool_name from model output; arguments parsed from JSON
    return await call_callable(tools, tool_name, **arguments)
```

## `@callable` methods

Use `@callable` to mark methods that should be exposed as callable endpoints by your own routing layer.

```python
from python_agents import callable, call_callable, get_callable_methods


class MathAgent:
    @callable
    async def multiply(self, left: int, right: int) -> int:
        return left * right

    @callable(name="sum")
    def add(self, left: int, right: int) -> int:
        return left + right


async def demo_callable_dispatch():
    agent = MathAgent()

    # Introspection
    methods = get_callable_methods(agent)
    assert set(methods) == {"multiply", "sum"}

    # Dynamic dispatch by exposed callable name
    result = await call_callable(agent, "sum", 2, 3)
    assert result == 5
```

## Routing helpers

```python
from python_agents import get_agent_by_name, route_agent_request


async def fetch(request, env, ctx):
    # Route HTTP requests to an agent namespace/name
    return await route_agent_request(
        request,
        env,
        {"namespace": "chat", "name": "assistant"},
    )


async def inspect_agent(env):
    agent = await get_agent_by_name("chat", "assistant")
    return agent.state
```

## Worker bridge setup

Cloudflare executes the core agent runtime from the JS SDK. To expose that runtime to Python,
add a small bridge module to your Worker bundle.

`src/agents_bridge.mjs`:

```js
import {
  Agent,
  routeAgentRequest,
  getAgentByName,
  getAgent,
} from "agents";

globalThis.__PYTHON_AGENTS_SDK = {
  Agent,
  routeAgentRequest,
  getAgentByName,
  getAgent,
  createAgent(init = {}) {
    return new Agent(init);
  },
};
```

## Scheduling tasks

```python
from python_agents import Agent


async def schedule_jobs(env, ctx):
    agent = Agent.create(state={}, env=env, ctx=ctx)

    # Run once at a specific time
    await agent.schedule({"type": "email-digest", "user_id": "u_123"}, "2026-01-01T00:00:00Z")

    # Run repeatedly every 5 minutes
    await agent.schedule_every({"type": "refresh-cache"}, "5 minutes")

    return await agent.get_schedules()
```

## Queueing tasks

```python
from python_agents import Agent


async def queue_work(env, ctx):
    agent = Agent.create(state={}, env=env, ctx=ctx)

    await agent.queue({"job": "index-document", "doc_id": "doc_42"})

    pending = await agent.get_queue()
    next_item = await agent.dequeue()

    return {"pending": pending, "processed": next_item}
```

## Connecting to an MCP server

```python
from python_agents import Agent


async def attach_mcp(env, ctx):
    agent = Agent.create(state={}, env=env, ctx=ctx)

    await agent.add_mcp_server({
        "name": "docs",
        "transport": "http",
        "url": "https://mcp.example.com",
    })

    servers = await agent.get_mcp_servers()
    return servers
```

## Full wrapped methods

`Agent` currently exposes wrappers for:

- `set_state`
- `schedule`, `schedule_every`, `get_schedules`, `cancel_schedule`
- `queue`, `dequeue`, `dequeue_all`, `get_queue`
- `broadcast`
- `run_workflow`, `wait_for_approval`
- `add_mcp_server`, `remove_mcp_server`, `get_mcp_servers`
- `reply_to_email`

For methods not listed above, use:

```python
await agent.call("camelCaseMethodName", arg1, arg2)
# or
await agent.call("snake_case_method_name", arg1, arg2)
```

## Testing

```bash
pytest
```

## Publishing notes (PyPI-ready project layout)

This repository is prepared for packaging with `hatchling` via `pyproject.toml`.
A standard release flow looks like:

```bash
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*
python -m twine upload dist/*
```
