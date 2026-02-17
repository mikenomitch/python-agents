import { useAgent } from "agents/react";
import { useState } from "react";

type SupportState = { count: number; lastAnswer?: string };

export function App() {
  const [question, setQuestion] = useState("Can I get a refund?");
  const [topic, setTopic] = useState("refund");
  const [policy, setPolicy] = useState("");

  const support = useAgent<any, SupportState>({
    agent: "support-agent",
    name: "demo-user",
  });

  async function increment() {
    const res = await fetch("/api/increment", { method: "POST" });
    const data = await res.json();
    await support.setState({ ...support.state, count: data.count });
  }

  async function askSupport() {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ question, topic }),
    });
    const data = await res.json();
    setPolicy(data.tool_result);

    await support.setState({
      ...support.state,
      lastAnswer: data.answer,
    });
  }

  return (
    <main>
      <h1>Support Agent (Python + Workers AI)</h1>
      <p>Shared count: {support.state?.count ?? 0}</p>
      <button onClick={increment}>Increment</button>

      <hr />

      <label>
        Question
        <input value={question} onChange={(e) => setQuestion(e.target.value)} />
      </label>

      <label>
        Topic
        <select value={topic} onChange={(e) => setTopic(e.target.value)}>
          <option value="refund">refund</option>
          <option value="shipping">shipping</option>
        </select>
      </label>

      <button onClick={askSupport}>Ask (tool + Workers AI)</button>

      <p>
        <strong>Tool result:</strong> {policy || "No tool call yet."}
      </p>
      <p>
        <strong>AI answer:</strong> {support.state?.lastAnswer || "No AI answer yet."}
      </p>
    </main>
  );
}
