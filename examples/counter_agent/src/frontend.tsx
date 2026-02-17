import { useAgent } from "agents/react";
import type { CounterAgent } from "./agent-bridge";

export function CounterView() {
  const agent = useAgent<CounterAgent, { count: number }>({
    agent: "counter-agent",
    name: "demo-user",
  });

  return (
    <button onClick={() => agent.stub.increment(1)}>
      Count: {agent.state?.count ?? 0}
    </button>
  );
}
