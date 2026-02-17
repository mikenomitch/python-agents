import { Agent } from "agents";

/**
 * Expose a tiny bridge consumed by Python via `from js import __PYTHON_AGENTS_SDK__`.
 *
 * This keeps maintenance low: Python forwards all logic to the official JS SDK.
 */
globalThis.__PYTHON_AGENTS_SDK__ = {
  createAgent(options) {
    return new Agent(options);
  },
};
