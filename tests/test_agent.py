from __future__ import annotations

import asyncio

import pytest

from python_agents import agent as agent_module
from python_agents import apis as apis_module
from python_agents._ffi import snake_to_camel
from python_agents.agent import Agent
from python_agents.apis import (
    AgentWorkflow,
    McpAgent,
    create_address_based_email_resolver,
    create_mcp_handler,
    route_agent_email,
)


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


class FakeJSMcpAgent:
    def __init__(self, init):
        self.init = init

    def getServers(self):
        return ["server-a"]


class FakeJSWorkflow:
    def __init__(self, init):
        self.init = init

    def run(self, payload):
        return FakePromise({"ran": payload})


class FakeSDK:
    def createAgent(self, init):
        return FakeJSAgent(init)

    def createMcpAgent(self, init):
        return FakeJSMcpAgent(init)

    def createAgentWorkflow(self, init):
        return FakeJSWorkflow(init)

    def createMcpHandler(self, config):
        return {"handler": config}

    def routeAgentEmail(self, message, env):
        return FakePromise({"message": message, "env": env})

    def createAddressBasedEmailResolver(self, mapping):
        return {"resolver": mapping}


@pytest.fixture(autouse=True)
def patch_sdk(monkeypatch):
    monkeypatch.setattr(agent_module, "get_agents_sdk", lambda: FakeSDK())
    monkeypatch.setattr(agent_module, "to_js", lambda value: value)
    monkeypatch.setattr(apis_module, "get_agents_sdk", lambda: FakeSDK())
    monkeypatch.setattr(apis_module, "to_js", lambda value: value)


def test_snake_to_camel():
    assert snake_to_camel("set_state") == "setState"
    assert snake_to_camel("get_mcp_servers") == "getMcpServers"


def test_create_and_call_set_state():
    async def _run():
        agent = Agent.create(state={"count": 1})
        updated = await agent.set_state({"count": 2})
        assert updated["count"] == 2

    asyncio.run(_run())


def test_call_non_awaitable_method():
    async def _run():
        agent = Agent.create(state={})
        schedules = await agent.get_schedules()
        assert schedules == ["one", "two"]

    asyncio.run(_run())


def test_unknown_method_raises_attribute_error():
    agent = Agent.create(state={})
    with pytest.raises(AttributeError):
        agent.not_real_method


def test_mcp_agent_wrapper():
    async def _run():
        mcp_agent = McpAgent.create(state={"ok": True})
        servers = await mcp_agent.get_servers()
        assert servers == ["server-a"]

    asyncio.run(_run())


def test_agent_workflow_wrapper():
    async def _run():
        workflow = AgentWorkflow.create({"name": "demo"})
        result = await workflow.run({"job": "sync"})
        assert result == {"ran": {"job": "sync"}}

    asyncio.run(_run())


def test_email_and_mcp_handler_helpers():
    async def _run():
        handler = create_mcp_handler({"name": "my-mcp"})
        assert handler == {"handler": {"name": "my-mcp"}}

        routed = await route_agent_email({"to": "x@example.com"}, {"ENV": "dev"})
        assert routed == {"message": {"to": "x@example.com"}, "env": {"ENV": "dev"}}

        resolver = create_address_based_email_resolver({"x@example.com": "agent-id"})
        assert resolver == {"resolver": {"x@example.com": "agent-id"}}

    asyncio.run(_run())
