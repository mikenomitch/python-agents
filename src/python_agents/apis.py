from __future__ import annotations

from typing import Any

from ._ffi import get_agents_sdk, maybe_await, snake_to_camel, to_js


class _JSProxy:
    """Snake-case adapter for JavaScript SDK objects."""

    def __init__(self, js_object: Any):
        self._js_object = js_object

    @property
    def state(self) -> Any:
        return getattr(self._js_object, "state", None)

    @property
    def env(self) -> Any:
        return getattr(self._js_object, "env", None)

    @property
    def ctx(self) -> Any:
        return getattr(self._js_object, "ctx", None)

    async def call(self, method: str, *args: Any) -> Any:
        js_method_name = snake_to_camel(method) if "_" in method else method
        target = getattr(self._js_object, js_method_name)
        js_args = tuple(to_js(arg) if isinstance(arg, dict | list | tuple) else arg for arg in args)
        result = target(*js_args)
        return await maybe_await(result)

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)

        async def _method(*args: Any):
            return await self.call(name, *args)

        return _method


class McpAgent(_JSProxy):
    """Pythonic wrapper around Cloudflare's JavaScript `McpAgent`."""

    @classmethod
    def create(cls, state: dict[str, Any] | None = None, env: Any = None, ctx: Any = None) -> "McpAgent":
        sdk = get_agents_sdk()
        init = {"state": state or {}}
        if env is not None:
            init["env"] = env
        if ctx is not None:
            init["ctx"] = ctx

        js_agent = sdk.createMcpAgent(to_js(init))
        return cls(js_agent)


class AgentWorkflow(_JSProxy):
    """Pythonic wrapper around Cloudflare's JavaScript `AgentWorkflow`."""

    @classmethod
    def create(cls, init: dict[str, Any] | None = None) -> "AgentWorkflow":
        sdk = get_agents_sdk()
        js_workflow = sdk.createAgentWorkflow(to_js(init or {}))
        return cls(js_workflow)


def create_mcp_handler(*args: Any) -> Any:
    """Pythonic equivalent of JavaScript `createMcpHandler`."""

    sdk = get_agents_sdk()
    js_args = tuple(to_js(arg) if isinstance(arg, dict | list | tuple) else arg for arg in args)
    return sdk.createMcpHandler(*js_args)


async def route_agent_email(*args: Any) -> Any:
    """Pythonic equivalent of JavaScript `routeAgentEmail`."""

    sdk = get_agents_sdk()
    js_args = tuple(to_js(arg) if isinstance(arg, dict | list | tuple) else arg for arg in args)
    return await maybe_await(sdk.routeAgentEmail(*js_args))


def create_address_based_email_resolver(*args: Any) -> Any:
    """Pythonic equivalent of JavaScript `createAddressBasedEmailResolver`."""

    sdk = get_agents_sdk()
    js_args = tuple(to_js(arg) if isinstance(arg, dict | list | tuple) else arg for arg in args)
    return sdk.createAddressBasedEmailResolver(*js_args)
