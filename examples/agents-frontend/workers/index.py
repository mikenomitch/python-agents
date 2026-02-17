from workers import WorkerEntrypoint, Response

from python_agents import Agent


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        agent = Agent.create(state={"count": 0}, env=self.env, ctx=self.ctx)
        await agent.set_state({"count": 1})
        return Response("Python Agent initialized")
