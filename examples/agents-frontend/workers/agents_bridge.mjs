import {
  Agent,
  AgentWorkflow,
  McpAgent,
  createAddressBasedEmailResolver,
  createMcpHandler,
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
