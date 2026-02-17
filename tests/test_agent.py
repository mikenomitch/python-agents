from __future__ import annotations

import asyncio

import pytest

from python_agents import agent as agent_module
from python_agents import apis as apis_module
from python_agents import tools as tools_module
from python_agents._ffi import snake_to_camel
from python_agents.agent import Agent, call_callable, callable, get_callable_methods
from python_agents.apis import (
    AgentWorkflow,
    McpAgent,
    create_address_based_email_resolver,
    create_mcp_handler,
    route_agent_email,
)
from python_agents.tools import call_tool, get_tool_methods, register_mcp_tools, tool
from python_agents.routing import (
    get_agent_by_name,
    route_agent_request,
    route_agent_requests,
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
        self.state = init.get("state", {})
        self.env = init.get("env")
        self.ctx = init.get("ctx")

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

    def routeAgentRequest(self, request, env, options=None):
        return {"request": request, "env": env, "options": options}

    def getAgentByName(self, namespace, name):
        return FakeJSAgent({"state": {"namespace": namespace, "name": name}})


class FakeMcpServer:
    def __init__(self):
        self.tools = {}

    def tool(self, name, schema_or_handler, maybe_handler=None):
        if maybe_handler is None:
            self.tools[name] = {"schema": None, "handler": schema_or_handler}
        else:
            self.tools[name] = {"schema": schema_or_handler, "handler": maybe_handler}


@pytest.fixture(autouse=True)
def patch_sdk(monkeypatch):
    monkeypatch.setattr(agent_module, "get_agents_sdk", lambda: FakeSDK())
    monkeypatch.setattr(agent_module, "to_js", lambda value: value)
    monkeypatch.setattr(apis_module, "get_agents_sdk", lambda: FakeSDK())
    monkeypatch.setattr(apis_module, "to_js", lambda value: value)
    monkeypatch.setattr(tools_module, "to_js", lambda value: value)

    import python_agents.routing as routing_module

    monkeypatch.setattr(routing_module, "get_agents_sdk", lambda: FakeSDK())


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


class ExampleCallableAgent:
    @callable
    async def greet(self, name: str) -> str:
        return f"hello {name}"

    @callable(name="sum")
    def add(self, left: int, right: int) -> int:
        return left + right


def test_callable_decorator_and_dispatch():
    async def _run():
        agent = ExampleCallableAgent()

        methods = get_callable_methods(agent)
        assert sorted(methods.keys()) == ["greet", "sum"]

        greeting = await call_callable(agent, "greet", "python")
        assert greeting == "hello python"

        total = await call_callable(agent, "sum", 2, 3)
        assert total == 5

    asyncio.run(_run())


def test_route_helpers_and_get_agent_by_name():
    async def _run():
        routed = await route_agent_request("REQ", {"NAMESPACE": "x"}, {"name": "demo"})
        routed_plural = await route_agent_requests(
            "REQ", {"NAMESPACE": "x"}, {"name": "demo"}
        )
        assert routed == routed_plural

        agent = await get_agent_by_name("examples", "demo")
        assert isinstance(agent, Agent)
        assert agent.state["name"] == "demo"

    asyncio.run(_run())


def test_mcp_agent_wrapper():
    async def _run():
        mcp_agent = McpAgent.create(
            state={"ok": True}, env={"name": "dev"}, ctx={"id": "ctx-1"}
        )
        servers = await mcp_agent.get_servers()
        assert servers == ["server-a"]
        assert mcp_agent.state == {"ok": True}
        assert mcp_agent.env == {"name": "dev"}
        assert mcp_agent.ctx == {"id": "ctx-1"}

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


class ExampleMcpTools:
    @tool(input_schema={"order_id": "string"})
    async def lookup_order(self, order_id: str):
        return {"content": [{"type": "text", "text": f"order:{order_id}"}]}

    @tool(name="refund_policy")
    def policy(self):
        return {"content": [{"type": "text", "text": "30 days"}]}


def test_tool_decorator_dispatch_and_registration():
    async def _run():
        tools = ExampleMcpTools()
        methods = get_tool_methods(tools)
        assert sorted(methods.keys()) == ["lookup_order", "refund_policy"]

        result = await call_tool(tools, "lookup_order", {"order_id": "123"})
        assert result["content"][0]["text"] == "order:123"

        server = FakeMcpServer()
        register_mcp_tools(server, tools)

        assert set(server.tools.keys()) == {"lookup_order", "refund_policy"}
        assert server.tools["lookup_order"]["schema"] == {"order_id": "string"}
        assert server.tools["refund_policy"]["schema"] is None

        lookup_registered = await server.tools["lookup_order"]["handler"]({"order_id": "777"})
        assert lookup_registered["content"][0]["text"] == "order:777"

    asyncio.run(_run())


def test_call_tool_missing_name_raises_key_error():
    async def _run():
        with pytest.raises(KeyError):
            await call_tool(ExampleMcpTools(), "does_not_exist")

    asyncio.run(_run())
