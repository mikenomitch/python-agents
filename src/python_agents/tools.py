from __future__ import annotations

from collections.abc import Callable
import builtins
from functools import wraps
from typing import Any

from ._ffi import maybe_await, to_js


McpToolHandler = Callable[..., Any]


def tool(
    func: McpToolHandler | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    input_schema: Any = None,
) -> McpToolHandler:
    """Mark an instance method as an MCP tool definition.

    The resulting metadata can be registered with ``register_mcp_tools(...)``
    against a JS ``McpServer`` instance (``server.tool(...)``).
    """

    def _decorate(inner: McpToolHandler) -> McpToolHandler:
        exposed_name = name or inner.__name__

        @wraps(inner)
        def _wrapped(*args: Any, **kwargs: Any):
            return inner(*args, **kwargs)

        setattr(_wrapped, "__python_agents_tool__", True)
        setattr(_wrapped, "__python_agents_tool_name__", exposed_name)
        setattr(_wrapped, "__python_agents_tool_description__", description)
        setattr(_wrapped, "__python_agents_tool_input_schema__", input_schema)
        return _wrapped

    if func is None:
        return _decorate
    return _decorate(func)


def get_tool_methods(obj: Any) -> dict[str, McpToolHandler]:
    """Return MCP-tool name -> bound method for an object instance."""

    methods: dict[str, McpToolHandler] = {}
    for attr_name in dir(obj):
        candidate = getattr(obj, attr_name, None)
        if builtins.callable(candidate) and getattr(candidate, "__python_agents_tool__", False):
            exposed_name = getattr(candidate, "__python_agents_tool_name__", attr_name)
            methods[exposed_name] = candidate
    return methods


async def call_tool(obj: Any, name: str, arguments: dict[str, Any] | None = None) -> Any:
    """Invoke a ``@tool`` method by exposed name using MCP-style arguments."""

    methods = get_tool_methods(obj)
    if name not in methods:
        raise KeyError(f"No MCP tool named '{name}'")
    result = methods[name](**(arguments or {}))
    return await maybe_await(result)


def register_mcp_tools(server: Any, obj: Any) -> None:
    """Register all ``@tool`` methods from ``obj`` on a JS MCP server.

    Mirrors the JavaScript shape:
    ``server.tool(name, inputSchema, async (args) => result)``.
    """

    for exposed_name, method in get_tool_methods(obj).items():
        schema = getattr(method, "__python_agents_tool_input_schema__", None)

        async def _handler(arguments: dict[str, Any], _method: McpToolHandler = method):
            result = _method(**(arguments or {}))
            return await maybe_await(result)

        if schema is None:
            server.tool(exposed_name, _handler)
            continue

        js_schema = to_js(schema) if isinstance(schema, dict | list | tuple) else schema
        server.tool(exposed_name, js_schema, _handler)
