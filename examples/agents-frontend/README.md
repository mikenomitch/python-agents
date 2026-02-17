# Example: Python Agent + agents frontend

This example demonstrates using this Python wrapper on the server while keeping
Cloudflare's official frontend SDK in JavaScript.

## Structure

- `workers/agents_bridge.mjs`: exposes JS Agents SDK to Python via global FFI bridge.
- `workers/index.py`: Python Worker code that creates and updates an Agent.
- `src/App.tsx`: frontend using `useAgent` from `agents/react`.

## workers/agents_bridge.mjs

```js
import { Agent, routeAgentRequest } from "agents";

globalThis.__PYTHON_AGENTS_SDK = {
  Agent,
  routeAgentRequest,
  createAgent(init = {}) {
    return new Agent(init);
  },
};
```

## workers/index.py

```python
from workers import WorkerEntrypoint, Response
from python_agents import Agent


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        agent = Agent.create(state={"count": 0}, env=self.env, ctx=self.ctx)
        await agent.set_state({"count": 1})
        return Response("Python Agent initialized")
```

## src/App.tsx

```tsx
import { useAgent } from "agents/react";

type State = { count: number };

export function App() {
  const counter = useAgent<any, State>({
    agent: "counter-agent",
    name: "demo-user",
  });

  return (
    <main>
      <h1>Counter</h1>
      <p>{counter.state?.count ?? 0}</p>
      <button onClick={() => counter.setState({ count: (counter.state?.count ?? 0) + 1 })}>
        Increment
      </button>
    </main>
  );
}
```

This keeps client-side code unchanged and uses standard Agents frontend
patterns.
