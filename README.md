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

## Quick example (equivalent to Cloudflare's quick example, plus tool calling + Workers AI)

This mirrors the Cloudflare quick example pattern (agent state + frontend sync), and adds:

- a simple `@callable` tool-style method (`lookup_policy`), and
- a Workers AI call (`env.AI.run(...)`) to generate a short response.

```python
# workers/index.py
import json

from workers import Response, WorkerEntrypoint
from python_agents import Agent, call_callable, callable, route_agent_request


class SupportTools:
    @callable
    def lookup_policy(self, topic: str) -> str:
        policies = {
            "refund": "Refunds are allowed within 30 days with a receipt.",
            "shipping": "Standard shipping takes 3-5 business days.",
        }
        return policies.get(topic.lower(), "No policy found for that topic.")


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # App endpoint for tool call + Workers AI.
        if request.method == "POST" and request.url.endswith("/api/chat"):
            body = await request.json()
            question = body.get("question", "")
            topic = body.get("topic", "refund")

            tool_result = await call_callable(SupportTools(), "lookup_policy", topic)

            ai_result = await self.env.AI.run(
                "@cf/meta/llama-3.1-8b-instruct",
                {
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a concise support assistant.",
                        },
                        {
                            "role": "user",
                            "content": f"Question: {question}\nPolicy: {tool_result}",
                        },
                    ]
                },
            )

            return Response(
                json.dumps(
                    {
                        "tool_result": tool_result,
                        "answer": ai_result.get("response", "No response"),
                    }
                ),
                headers={"content-type": "application/json"},
            )

        # Agent endpoint for realtime state sync with frontend.
        routed = await route_agent_request(request, self.env)
        if routed:
            return routed

        return Response("Not found", status=404)
```

```tsx
// src/App.tsx
import { useAgent } from "agents/react";
import { useState } from "react";

type CounterState = { count: number; lastAnswer?: string };

export function App() {
  const [question, setQuestion] = useState("Can I get a refund?");
  const [topic, setTopic] = useState("refund");

  const agent = useAgent<any, CounterState>({
    agent: "support-agent",
    name: "demo-user",
  });

  async function askSupport() {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ question, topic }),
    });
    const data = await res.json();

    await agent.setState({
      ...agent.state,
      lastAnswer: data.answer,
    });
  }

  return (
    <main>
      <h1>Support Agent</h1>
      <p>Count: {agent.state?.count ?? 0}</p>
      <button onClick={() => agent.setState({ count: (agent.state?.count ?? 0) + 1 })}>
        Increment
      </button>

      <hr />

      <input value={question} onChange={(e) => setQuestion(e.target.value)} />
      <select value={topic} onChange={(e) => setTopic(e.target.value)}>
        <option value="refund">refund</option>
        <option value="shipping">shipping</option>
      </select>
      <button onClick={askSupport}>Ask (tool + Workers AI)</button>

      <p>{agent.state?.lastAnswer ?? "No AI answer yet."}</p>
    </main>
  );
}
```

## MCP tool registration (parity with JS `server.tool(...)`)

Cloudflare's JS examples define MCP tools with `server.tool(name, schema, handler)`.
This package now provides the same pattern in Python with `@tool` + `register_mcp_tools(...)`.

```python
from python_agents import register_mcp_tools, tool


class SupportTools:
    @tool(input_schema={"order_id": "string"})
    async def lookup_order(self, order_id: str):
        return {"content": [{"type": "text", "text": f"order:{order_id}"}]}


async def init_mcp(server):
    register_mcp_tools(server, SupportTools())
```

You can also invoke tools directly during tests or local dispatch:

```python
from python_agents import call_tool

result = await call_tool(SupportTools(), "lookup_order", {"order_id": "123"})
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
  AgentWorkflow,
  McpAgent,
  createAddressBasedEmailResolver,
  createMcpHandler,
  getAgent,
  getAgentByName,
  routeAgentEmail,
  routeAgentRequest,
} from "agents";

globalThis.__PYTHON_AGENTS_SDK = {
  Agent,
  AgentWorkflow,
  McpAgent,
  createAddressBasedEmailResolver,
  createMcpHandler,
  routeAgentEmail,
  routeAgentRequest,
  getAgentByName,
  getAgent,
  createAgent(init = {}) {
    return new Agent(init);
  },
  createMcpAgent(init = {}) {
    return new McpAgent(init);
  },
  createAgentWorkflow(init = {}) {
    return new AgentWorkflow(init);
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

Additional Pythonic wrappers are available for Cloudflare Agents APIs:

- `McpAgent.create(...)` (JS: `McpAgent`)
- `AgentWorkflow.create(...)` (JS: `AgentWorkflow`)
- `create_mcp_handler(...)` (JS: `createMcpHandler`)
- `route_agent_email(...)` (JS: `routeAgentEmail`)
- `create_address_based_email_resolver(...)` (JS: `createAddressBasedEmailResolver`)
