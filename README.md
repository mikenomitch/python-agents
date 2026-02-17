# cloudflare-python-agents

A thin Python wrapper around Cloudflare's JavaScript Agents SDK for Python Workers.

The goal is maintainability: this package forwards calls over Workers Python FFI to the official JS SDK instead of reimplementing the Agents runtime in Python.

## Why this design

Cloudflare Python Workers can call JavaScript objects through Pyodide FFI.
This library relies on that model and keeps a very small Python layer:

- Python API surface is snake_case and Pythonic.
- Execution and behavior stay in the JS `agents` package.
- Unknown APIs can still be reached via `agent.raw` (escape hatch).

## Install

```bash
pip install cloudflare-python-agents
```

## Worker setup (required)

Because `agents` is a JavaScript package, expose it through a tiny bridge file:

`src/js/python-agents-bridge.mjs`

```js
import { Agent } from "agents";

globalThis.__PYTHON_AGENTS_SDK__ = {
  createAgent(options) {
    return new Agent(options);
  },
};
```

Load this file in your Worker build so `globalThis.__PYTHON_AGENTS_SDK__` exists before Python code executes.

## Quick start

```python
from cloudflare_python_agents import Agent


agent = Agent(
    "user-123",
    initial_state={"messages": []},
    props={"team": "support"},
)

agent.set_state({"messages": [{"role": "user", "text": "hello"}]})
agent.schedule_every("*/5 * * * *", "flush_transcript")
agent.queue("generate_summary", {"max_tokens": 1024})
```

## API mapping

Python wrapper methods map directly to Agent class methods:

- `set_state()` -> `setState()`
- `schedule()` -> `schedule()`
- `schedule_every()` -> `scheduleEvery()`
- `get_schedules()` -> `getSchedules()`
- `cancel_schedule()` -> `cancelSchedule()`
- `queue()` -> `queue()`
- `dequeue()` -> `dequeue()`
- `dequeue_all()` -> `dequeueAll()`
- `get_queue()` -> `getQueue()`
- `broadcast()` -> `broadcast()`
- `run_workflow()` -> `runWorkflow()`
- `wait_for_approval()` -> `waitForApproval()`
- `add_mcp_server()` -> `addMcpServer()`
- `remove_mcp_server()` -> `removeMcpServer()`
- `get_mcp_servers()` -> `getMcpServers()`
- `reply_to_email()` -> `replyToEmail()`

## Frontend usage example (JS/React, unchanged)

Client code remains JavaScript/TypeScript with the official `agents` frontend package.
See `examples/counter/frontend/App.tsx` for a React `useAgent` sample, and
`examples/counter/worker/src/index.py` for Python server-side usage.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
```

## Notes

- This package wraps **server-side Agent APIs**.
- It intentionally does **not** port client SDKs (`AgentClient`, `useAgent`, `useAgentChat`) to Python.
- FFI conversion uses `pyodide.ffi.to_js` when running in Python Workers.
