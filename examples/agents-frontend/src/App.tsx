import { useAgent } from "agents/react";

type State = { count: number };

export function App() {
  const counter = useAgent<any, State>({
    agent: "counter-agent",
    name: "demo-user",
  });

  return (
    <main>
      <h1>Counter</h1>
      <p>{counter.state?.count ?? 0}</p>
      <button
        onClick={() =>
          counter.setState({ count: (counter.state?.count ?? 0) + 1 })
        }
      >
        Increment
      </button>
    </main>
  );
}
