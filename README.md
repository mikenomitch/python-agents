# python-agents

A thin, maintainable Python wrapper around the Cloudflare JavaScript Agents SDK.

## Why this library

Cloudflare Agents is implemented in JavaScript. Python Workers can call JavaScript directly using Pyodide FFI, so this package avoids reimplementing the SDK in Python. Instead, it provides:

- a Pythonic `snake_case` API over JS `camelCase` methods,
- automatic conversion between Python and JS objects,
- a minimal bridge (`load_agent`) for loading JS factories from Python Worker code.

This means new SDK features are usually available immediately through pass-through forwarding.

## Install

```bash
pip install -e .
```

## Quick start

1. Define your real Agent class in JavaScript (normal Cloudflare workflow).
2. Export a JS factory and assign it to `globalThis`.
3. In Python Worker code, call `load_agent(...)` and interact with it naturally.

```python
from python_agents import load_agent

counter = load_agent("getCounterAgent", env, "user-123")
await counter.increment(1)
await counter.set_state({"count": 2})
```

See full setup in [`docs/getting-started.md`](docs/getting-started.md).

## API

### `Agent(js_agent)`

Wraps a JavaScript Agent instance/stub.

- Any Python `snake_case` method call forwards to JS `camelCase`.
- `kwargs` become a final options object argument.
- Return values are converted back to Python when possible.

### `load_agent(factory_name, *args, **kwargs)`

Loads `globalThis[factory_name]` from JavaScript and wraps the result in `Agent`.

## Development

```bash
python -m pip install pytest pytest-asyncio
pytest
```
