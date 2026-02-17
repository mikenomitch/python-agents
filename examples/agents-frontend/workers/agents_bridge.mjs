import { Agent, routeAgentRequest } from "agents";

globalThis.__PYTHON_AGENTS_SDK = {
  Agent,
  routeAgentRequest,
  createAgent(init = {}) {
    return new Agent(init);
  },
};
