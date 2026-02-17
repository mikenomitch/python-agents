"""Helpers for converting values between Python and JavaScript in Workers."""

from __future__ import annotations

from typing import Any


def to_js(value: Any) -> Any:
    """Convert Python values to JavaScript values when Pyodide is available."""
    try:
        from js import Object  # type: ignore
        from pyodide.ffi import to_js as pyodide_to_js  # type: ignore

        return pyodide_to_js(value, dict_converter=Object.fromEntries)
    except Exception:
        return value


def from_js(value: Any) -> Any:
    """Convert JavaScript proxies to Python values where possible."""
    if hasattr(value, "to_py"):
        return value.to_py()  # pyright: ignore[reportAttributeAccessIssue]
    return value
