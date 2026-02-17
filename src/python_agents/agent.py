"""Pythonic proxy for Cloudflare's JavaScript Agent class."""

from __future__ import annotations

import inspect
import re
from typing import Any, Callable

from .conversion import from_js, to_js


_SNAKE_RE = re.compile(r"_([a-z])")


def _snake_to_camel(name: str) -> str:
    return _SNAKE_RE.sub(lambda m: m.group(1).upper(), name)


class Agent:
    """Thin wrapper around a JavaScript Agent (or Agent stub).

    This class intentionally forwards nearly all operations to JavaScript so
    new Agents SDK functionality is available without rewriting Python code.
    """

    def __init__(self, js_agent: Any):
        self._js_agent = js_agent

    @classmethod
    def from_factory(cls, factory: Callable[..., Any], *args: Any, **kwargs: Any) -> "Agent":
        """Create an Agent wrapper from a JavaScript factory exported via FFI."""
        js_agent = factory(*args, **kwargs)
        return cls(js_agent)

    def __getattr__(self, name: str) -> Any:
        js_name = _snake_to_camel(name)
        target = getattr(self._js_agent, js_name)

        if callable(target):

            async def _call(*args: Any, **kwargs: Any) -> Any:
                js_args = [to_js(arg) for arg in args]
                if kwargs:
                    js_args.append(to_js(kwargs))
                result = target(*js_args)
                if inspect.isawaitable(result):
                    result = await result
                return from_js(result)

            return _call

        return from_js(target)

    @property
    def raw(self) -> Any:
        """Access the underlying JavaScript object directly."""
        return self._js_agent
