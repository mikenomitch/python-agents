from workers import Response, WorkerEntrypoint

from python_agents import load_agent


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # Routes to the same JS Agent class used by web clients.
        counter = load_agent("getCounterAgent", self.env, "demo-user")

        if request.url.endswith("/increment"):
            count = await counter.increment(1)
            return Response.json({"count": count})

        return Response.json({"state": counter.state})
