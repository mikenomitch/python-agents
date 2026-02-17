from __future__ import annotations

from typing import Any

from ._ffi import get_agents_sdk, maybe_await, snake_to_camel
from .agent import Agent


async def _call_sdk(method: str, *args: Any) -> Any:
    sdk = get_agents_sdk()
    js_method_name = snake_to_camel(method) if "_" in method else method
    target = getattr(sdk, js_method_name)
    result = target(*args)
    return await maybe_await(result)


async def route_agent_request(*args: Any) -> Any:
    """Route a request to an Agent using Cloudflare SDK routing."""

    return await _call_sdk("route_agent_request", *args)


async def route_agent_requests(*args: Any) -> Any:
    """Plural alias for route_agent_request for naming parity with docs/examples."""

    return await route_agent_request(*args)


async def get_agent_by_name(*args: Any) -> Agent:
    """Look up an Agent by name and return it wrapped as :class:`python_agents.Agent`."""

    js_agent = await _call_sdk("get_agent_by_name", *args)
    return Agent(js_agent)


async def get_agent_by_id(*args: Any) -> Agent:
    """Look up an Agent by id and return it wrapped as :class:`python_agents.Agent`."""

    js_agent = await _call_sdk("get_agent", *args)
    return Agent(js_agent)
