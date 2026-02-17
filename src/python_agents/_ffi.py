"""Cloudflare Workers Python FFI helpers.

This module intentionally keeps the JS interop layer tiny so the main API stays
maintainable and close to the JavaScript Agents SDK.
"""

from __future__ import annotations

import re
from collections.abc import Awaitable
from typing import Any


_SNAKE_CASE_RE = re.compile(r"_([a-z])")


def snake_to_camel(value: str) -> str:
    """Convert a snake_case name to camelCase."""

    return _SNAKE_CASE_RE.sub(lambda m: m.group(1).upper(), value)


def to_js(value: Any) -> Any:
    """Convert a Python object to a JavaScript object when running in Workers."""

    import js  # type: ignore
    from pyodide.ffi import to_js as pyodide_to_js  # type: ignore

    if isinstance(value, dict):
        return pyodide_to_js(value, dict_converter=js.Object.fromEntries)
    return pyodide_to_js(value)


async def maybe_await(value: Any) -> Any:
    """Await JS promises and Python awaitables, return plain values unchanged."""

    if isinstance(value, Awaitable):
        return await value
    return value


def get_agents_sdk() -> Any:
    """Return the JS bridge object exposed by agents_bridge.mjs."""

    import js  # type: ignore

    sdk = getattr(js, "__PYTHON_AGENTS_SDK", None)
    if sdk is None:
        raise RuntimeError(
            "JavaScript bridge was not found. Import the bridge module that sets "
            "globalThis.__PYTHON_AGENTS_SDK before using python_agents.Agent."
        )
    return sdk
