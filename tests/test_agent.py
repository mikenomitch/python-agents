from __future__ import annotations

import pytest

from python_agents import agent as agent_module
from python_agents.agent import Agent, call_callable, callable, get_callable_methods
from python_agents.routing import get_agent_by_name, route_agent_request, route_agent_requests
from python_agents._ffi import snake_to_camel


class FakePromise:
    def __init__(self, value):
        self.value = value

    def __await__(self):
        async def _inner():
            return self.value

        return _inner().__await__()


class FakeJSAgent:
    def __init__(self, init):
        self.init = init
        self.state = init.get("state", {})
        self.env = init.get("env")
        self.ctx = init.get("ctx")

    def setState(self, patch):
        self.state.update(patch)
        return FakePromise(self.state)

    def getSchedules(self):
        return ["one", "two"]


class FakeSDK:
    def createAgent(self, init):
        return FakeJSAgent(init)

    def routeAgentRequest(self, request, env, options=None):
        return {"request": request, "env": env, "options": options}

    def getAgentByName(self, namespace, name):
        return FakeJSAgent({"state": {"namespace": namespace, "name": name}})


@pytest.fixture(autouse=True)
def patch_sdk(monkeypatch):
    monkeypatch.setattr(agent_module, "get_agents_sdk", lambda: FakeSDK())
    monkeypatch.setattr(agent_module, "to_js", lambda value: value)

    import python_agents.routing as routing_module

    monkeypatch.setattr(routing_module, "get_agents_sdk", lambda: FakeSDK())


def test_snake_to_camel():
    assert snake_to_camel("set_state") == "setState"
    assert snake_to_camel("get_mcp_servers") == "getMcpServers"


@pytest.mark.asyncio
async def test_create_and_call_set_state():
    agent = Agent.create(state={"count": 1})
    updated = await agent.set_state({"count": 2})
    assert updated["count"] == 2


@pytest.mark.asyncio
async def test_call_non_awaitable_method():
    agent = Agent.create(state={})
    schedules = await agent.get_schedules()
    assert schedules == ["one", "two"]


def test_unknown_method_raises_attribute_error():
    agent = Agent.create(state={})
    with pytest.raises(AttributeError):
        agent.not_real_method


class ExampleCallableAgent:
    @callable
    async def greet(self, name: str) -> str:
        return f"hello {name}"

    @callable(name="sum")
    def add(self, left: int, right: int) -> int:
        return left + right


@pytest.mark.asyncio
async def test_callable_decorator_and_dispatch():
    agent = ExampleCallableAgent()

    methods = get_callable_methods(agent)
    assert sorted(methods.keys()) == ["greet", "sum"]

    greeting = await call_callable(agent, "greet", "python")
    assert greeting == "hello python"

    total = await call_callable(agent, "sum", 2, 3)
    assert total == 5


@pytest.mark.asyncio
async def test_route_helpers_and_get_agent_by_name():
    routed = await route_agent_request("REQ", {"NAMESPACE": "x"}, {"name": "demo"})
    routed_plural = await route_agent_requests("REQ", {"NAMESPACE": "x"}, {"name": "demo"})
    assert routed == routed_plural

    agent = await get_agent_by_name("examples", "demo")
    assert isinstance(agent, Agent)
    assert agent.state["name"] == "demo"
