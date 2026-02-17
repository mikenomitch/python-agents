# python-agents

A thin Python wrapper for the Cloudflare **JavaScript** Agents SDK, designed for
Python Workers.

## Why this library?

- Keeps maintenance low by delegating behavior to the official JS `agents` package.
- Exposes a Pythonic API (`snake_case`) for server-side Agent operations.
- Uses Cloudflare Python Workers FFI to avoid rewriting SDK internals.

## Install (for local development)

```bash
pip install -e .[dev]
```

## Quick start

### 1) Add the JS bridge in your Worker bundle

Create `src/agents_bridge.mjs`:

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

This exposes the JS SDK to Python through `globalThis`.

### 2) Use `python_agents.Agent` from Python

```python
from python_agents import Agent


async def create_counter_agent(env, ctx):
    agent = Agent.create(state={"count": 0}, env=env, ctx=ctx)
    await agent.set_state({"count": 1})
    return agent
```

The wrapper maps snake_case to JavaScript camelCase methods (for example,
`set_state()` -> `setState()`, `get_schedules()` -> `getSchedules()`).

## Implemented API surface

The wrapper intentionally forwards calls to JS. Exposed helper methods include:

- `set_state`
- `schedule`, `schedule_every`, `get_schedules`, `cancel_schedule`
- `queue`, `dequeue`, `dequeue_all`, `get_queue`
- `broadcast`
- `run_workflow`, `wait_for_approval`
- `add_mcp_server`, `remove_mcp_server`, `get_mcp_servers`
- `reply_to_email`

You can also use `await agent.call("camelCaseName", ...)` for methods that are
not listed.

## Frontend integration example

See [`examples/agents-frontend/`](examples/agents-frontend/README.md) for a
full example using:

- Python Worker server code with this wrapper.
- Existing JS frontend patterns from `agents/react` (`useAgent`).

## Test

```bash
pytest
```
