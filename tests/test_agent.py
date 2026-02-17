from __future__ import annotations

import pytest

from python_agents import agent as agent_module
from python_agents.agent import Agent
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


@pytest.fixture(autouse=True)
def patch_sdk(monkeypatch):
    monkeypatch.setattr(agent_module, "get_agents_sdk", lambda: FakeSDK())
    monkeypatch.setattr(agent_module, "to_js", lambda value: value)


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
