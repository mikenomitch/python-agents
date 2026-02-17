# Technical internals (advanced)

This page is intentionally separate from the main README so new Python users can focus on building and deploying quickly.

## How `agents-py` works under the hood

Cloudflare Agents runtime behavior is provided by Cloudflare's official JavaScript Agents SDK.

`agents-py` provides a Pythonic layer on top, including:

- Python-friendly naming (`snake_case`)
- decorators (`@callable`, `@tool`)
- convenience helpers for routing and dispatch
- typed-friendly method surfaces

In Worker deployments, a small JS bridge exposes SDK functionality to Python.

## Bridge module example

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

## Who should read this

- You are debugging runtime integration details.
- You need to understand parity with JavaScript SDK behavior.
- You are extending or contributing to `agents-py` internals.

If you're only trying to build and deploy a Python agent, go back to the main [README](../README.md).
