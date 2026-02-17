/**
 * Cloudflare Agents SDK bridge for Python Workers.
 *
 * Import this module in your Worker bundle before Python code executes.
 */
import { Agent, routeAgentRequest } from "agents";

globalThis.__PYTHON_AGENTS_SDK = {
  Agent,
  routeAgentRequest,
  createAgent(init = {}) {
    return new Agent(init);
  },
};
