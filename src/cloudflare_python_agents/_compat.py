"""Runtime compatibility helpers for Cloudflare Python Workers FFI."""

from __future__ import annotations

from importlib.util import find_spec
from typing import Any


def to_js(value: Any) -> Any:
    """Convert Python values into JS-compatible values when pyodide is available."""
    if find_spec("pyodide") is None:
        return value

    from pyodide.ffi import to_js as pyodide_to_js  # type: ignore
    from js import Object  # pylint: disable=import-error

    return pyodide_to_js(value, dict_converter=Object.fromEntries)
