"""Bridge helpers for importing JavaScript factories from Python Workers."""

from __future__ import annotations

from typing import Any

from .agent import Agent


def load_agent(factory_name: str, *args: Any, **kwargs: Any) -> Agent:
    """Load a JavaScript factory from the `js` module and wrap its result.

    Example:
        agent = load_agent("getCounterAgent", env, "user-123")
    """
    from js import globalThis  # type: ignore

    factory = getattr(globalThis, factory_name)
    return Agent.from_factory(factory, *args, **kwargs)
