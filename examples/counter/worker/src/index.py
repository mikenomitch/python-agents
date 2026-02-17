"""Example Python Worker entrypoint using cloudflare_python_agents.Agent."""

from workers import Response, WorkerEntrypoint

from cloudflare_python_agents import Agent


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # For demo purposes this wraps an Agent instance by name and updates state.
        agent = Agent("counter-demo", initial_state={"count": 0})
        current = agent.state.get("count", 0)
        agent.set_state({"count": current + 1})
        return Response.json({"count": current + 1})
