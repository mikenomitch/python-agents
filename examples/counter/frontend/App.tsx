import { useAgent } from "agents/react";

export function App() {
  const agent = useAgent({
    agent: "counter",
    name: "counter-demo",
  });

  return (
    <div>
      <h1>Python Agent Counter</h1>
      <p>Count: {agent.state?.count ?? 0}</p>
      <button onClick={() => agent.setState({ count: (agent.state?.count ?? 0) + 1 })}>
        Increment
      </button>
    </div>
  );
}
