# Getting started with `python-agents`

This guide shows how to reuse the JavaScript Cloudflare Agents SDK from a Python Worker using FFI.

## 1) Install dependencies

```bash
npm install agents
pip install -e .
```

## 2) Configure Wrangler for Python + JS modules

Use Python as the Worker entrypoint, and add your JS Agent bridge module.

```jsonc
{
  "main": "./src/worker.py",
  "compatibility_date": "2026-01-01",
  "durable_objects": {
    "bindings": [
      {
        "name": "CounterAgent",
        "class_name": "CounterAgent"
      }
    ]
  },
  "migrations": [
    {
      "tag": "v1",
      "new_sqlite_classes": ["CounterAgent"]
    }
  ]
}
```

## 3) Build your Agent in JavaScript

`python-agents` does **not** replace the server-side Agents SDK; it wraps it.

Create `src/agent-bridge.js`:

```js
import { Agent, getAgentByName, routeAgentRequest } from "agents";

export class CounterAgent extends Agent {
  initialState = { count: 0 };

  async increment(amount = 1) {
    this.setState({ count: this.state.count + amount });
    return this.state.count;
  }
}

export function getCounterAgent(env, name) {
  return getAgentByName(env.CounterAgent, name);
}

globalThis.getCounterAgent = getCounterAgent;

export default {
  async fetch(request, env, ctx) {
    return routeAgentRequest(request, env, ctx) || new Response("Not found", { status: 404 });
  },
};
```

## 4) Use it from Python

Create `src/worker.py`:

```python
from workers import Response, WorkerEntrypoint

from python_agents import load_agent


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        agent = load_agent("getCounterAgent", self.env, "demo-user")

        if request.url.endswith("/increment"):
            count = await agent.increment(1)
            return Response.json({"count": count})

        return Response.json({"state": agent.state})
```

## 5) Frontend (unchanged Agents client SDK)

No client-side Python port is needed. Continue using the Agents frontend SDK:

```tsx
import { useAgent } from "agents/react";
import type { CounterAgent } from "./agent-bridge";

export function CounterView() {
  const agent = useAgent<CounterAgent, { count: number }>({
    agent: "counter-agent",
    name: "demo-user",
  });

  return (
    <button onClick={() => agent.stub.increment(1)}>
      Count: {agent.state?.count ?? 0}
    </button>
  );
}
```

## Notes

- Python method names are snake_case (`set_state`), mapped to JS camelCase (`setState`).
- `kwargs` are sent as a final JS options object.
- To access new SDK features, call them directly through the wrapper without waiting for Python-specific reimplementation.
