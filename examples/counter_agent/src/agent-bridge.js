import { Agent, getAgentByName, routeAgentRequest } from "agents";

export class CounterAgent extends Agent {
  initialState = { count: 0 };

  async increment(amount = 1) {
    this.setState({ count: this.state.count + amount });
    return this.state.count;
  }
}

export function getCounterAgent(env, name) {
  return getAgentByName(env.CounterAgent, name);
}

// Expose the factory for Python FFI imports via globalThis.
globalThis.getCounterAgent = getCounterAgent;

export default {
  async fetch(request, env, ctx) {
    return routeAgentRequest(request, env, ctx) || new Response("Not found", { status: 404 });
  },
};
