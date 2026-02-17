import json

from workers import Response, WorkerEntrypoint

from python_agents import Agent, call_callable, callable, route_agent_request


class SupportTools:
    @callable
    def lookup_policy(self, topic: str) -> str:
        policies = {
            "refund": "Refunds are allowed within 30 days with a receipt.",
            "shipping": "Standard shipping takes 3-5 business days.",
        }
        return policies.get(topic.lower(), "No policy found for that topic.")


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        if request.method == "POST" and request.url.endswith("/api/chat"):
            body = await request.json()
            question = body.get("question", "")
            topic = body.get("topic", "refund")

            tool_result = await call_callable(SupportTools(), "lookup_policy", topic)

            ai_result = await self.env.AI.run(
                "@cf/meta/llama-3.1-8b-instruct",
                {
                    "messages": [
                        {"role": "system", "content": "You are a concise support assistant."},
                        {
                            "role": "user",
                            "content": f"Question: {question}\nPolicy: {tool_result}",
                        },
                    ]
                },
            )

            return Response(
                json.dumps(
                    {
                        "tool_result": tool_result,
                        "answer": ai_result.get("response", "No response"),
                    }
                ),
                headers={"content-type": "application/json"},
            )

        agent = Agent.create(state={"count": 0, "lastAnswer": ""}, env=self.env, ctx=self.ctx)
        if request.method == "POST" and request.url.endswith("/api/increment"):
            state = agent.state or {"count": 0, "lastAnswer": ""}
            count = state.get("count", 0) + 1
            await agent.set_state({**state, "count": count})
            return Response(json.dumps({"count": count}), headers={"content-type": "application/json"})

        routed = await route_agent_request(request, self.env)
        if routed:
            return routed

        return Response("Not found", status=404)
