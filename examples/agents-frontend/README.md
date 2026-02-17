# Example: Python Agent + frontend + tool call + Workers AI

This example is a more in-depth application than the simple counter starter.
It demonstrates:

- a Python Worker using `agents-py`,
- frontend realtime state sync via `useAgent`,
- a simple tool-like callable (`lookup_policy`), and
- a Workers AI call (`env.AI.run(...)`) using the tool result as context.

## Structure

- `workers/agents_bridge.mjs`: exposes JS Agents SDK to Python via global FFI bridge.
- `workers/index.py`: Worker routes requests, executes callable tool logic, and calls Workers AI.
- `src/App.tsx`: frontend UI for counter state and support Q&A.

## Flow

1. The UI sends support questions to `POST /api/chat`.
2. The Worker calls `lookup_policy(topic)` via `call_callable(...)`.
3. The Worker calls Workers AI with the user question + tool output.
4. The UI stores AI output in shared agent state (`lastAnswer`) so connected clients stay in sync.
