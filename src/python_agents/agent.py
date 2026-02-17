from __future__ import annotations

from typing import Any

from ._ffi import get_agents_sdk, maybe_await, snake_to_camel, to_js


class Agent:
    """Pythonic wrapper around Cloudflare's JavaScript `Agent` instance.

    This class is intentionally thin: it keeps behavior in the JS SDK and only
    adds Python naming ergonomics (`snake_case` methods).
    """

    _KNOWN_METHODS = {
        "set_state",
        "schedule",
        "schedule_every",
        "get_schedules",
        "cancel_schedule",
        "queue",
        "dequeue",
        "dequeue_all",
        "get_queue",
        "broadcast",
        "run_workflow",
        "wait_for_approval",
        "add_mcp_server",
        "remove_mcp_server",
        "get_mcp_servers",
        "reply_to_email",
    }

    def __init__(self, js_agent: Any):
        self._js_agent = js_agent

    @classmethod
    def create(cls, state: dict[str, Any] | None = None, env: Any = None, ctx: Any = None) -> "Agent":
        """Create a wrapped JS `Agent` instance.

        In Workers, call this in your Python code after loading the JS bridge.
        """

        sdk = get_agents_sdk()
        init = {"state": state or {}}
        if env is not None:
            init["env"] = env
        if ctx is not None:
            init["ctx"] = ctx

        js_agent = sdk.createAgent(to_js(init))
        return cls(js_agent)

    @property
    def state(self) -> Any:
        return self._js_agent.state

    @property
    def env(self) -> Any:
        return self._js_agent.env

    @property
    def ctx(self) -> Any:
        return self._js_agent.ctx

    async def call(self, method: str, *args: Any) -> Any:
        """Call a JS agent method by Pythonic name (snake_case) or raw JS name."""

        js_method_name = snake_to_camel(method) if "_" in method else method
        target = getattr(self._js_agent, js_method_name)
        result = target(*args)
        return await maybe_await(result)

    def __getattr__(self, name: str):
        if name not in self._KNOWN_METHODS:
            raise AttributeError(name)

        async def _method(*args: Any):
            return await self.call(name, *args)

        return _method
