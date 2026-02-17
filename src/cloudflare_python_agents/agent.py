"""Pythonic wrapper for Cloudflare Agents SDK's `Agent` class."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from ._compat import to_js


class AgentBridge(Protocol):
    """Bridge contract provided by JavaScript glue code."""

    def createAgent(self, options: Any) -> Any: ...


@dataclass(slots=True)
class AgentOptions:
    """Options accepted by the Python Agent wrapper constructor."""

    name: str
    initial_state: dict[str, Any] | None = None
    props: dict[str, Any] | None = None

    def as_js_options(self) -> dict[str, Any]:
        data: dict[str, Any] = {"name": self.name}
        if self.initial_state is not None:
            data["initialState"] = self.initial_state
        if self.props is not None:
            data["props"] = self.props
        return data


class Agent:
    """Thin Python wrapper over a JavaScript `Agent` instance.

    Methods use idiomatic snake_case names and are forwarded to the JavaScript
    object via the Worker FFI.
    """

    def __init__(self, name: str, *, initial_state: dict[str, Any] | None = None, props: dict[str, Any] | None = None, bridge: AgentBridge | None = None):
        self._bridge = bridge or _load_default_bridge()
        options = AgentOptions(name=name, initial_state=initial_state, props=props)
        self._js = self._bridge.createAgent(to_js(options.as_js_options()))

    @classmethod
    def from_js(cls, js_agent: Any) -> "Agent":
        """Wrap an existing JavaScript agent object."""
        obj = cls.__new__(cls)
        obj._bridge = None
        obj._js = js_agent
        return obj

    @property
    def raw(self) -> Any:
        """Expose the underlying JavaScript proxy for escape hatches."""
        return self._js

    @property
    def state(self) -> Any:
        return self._js.state

    @property
    def env(self) -> Any:
        return self._js.env

    @property
    def ctx(self) -> Any:
        return self._js.ctx

    def set_state(self, state: dict[str, Any]) -> Any:
        return self._js.setState(to_js(state))

    def schedule(self, when: Any, callback: str, payload: dict[str, Any] | None = None) -> Any:
        return self._js.schedule(when, callback, to_js(payload or {}))

    def schedule_every(self, schedule: str, callback: str, payload: dict[str, Any] | None = None) -> Any:
        return self._js.scheduleEvery(schedule, callback, to_js(payload or {}))

    def get_schedules(self) -> Any:
        return self._js.getSchedules()

    def cancel_schedule(self, schedule_id: str) -> Any:
        return self._js.cancelSchedule(schedule_id)

    def queue(self, callback: str, payload: dict[str, Any] | None = None) -> Any:
        return self._js.queue(callback, to_js(payload or {}))

    def dequeue(self) -> Any:
        return self._js.dequeue()

    def dequeue_all(self) -> Any:
        return self._js.dequeueAll()

    def get_queue(self) -> Any:
        return self._js.getQueue()

    def broadcast(self, message: Any) -> Any:
        return self._js.broadcast(to_js(message))

    def run_workflow(self, workflow: str, payload: dict[str, Any] | None = None) -> Any:
        return self._js.runWorkflow(workflow, to_js(payload or {}))

    def wait_for_approval(self, key: str, payload: dict[str, Any] | None = None) -> Any:
        return self._js.waitForApproval(key, to_js(payload or {}))

    def add_mcp_server(self, name: str, config: dict[str, Any]) -> Any:
        return self._js.addMcpServer(name, to_js(config))

    def remove_mcp_server(self, name: str) -> Any:
        return self._js.removeMcpServer(name)

    def get_mcp_servers(self) -> Any:
        return self._js.getMcpServers()

    def reply_to_email(self, message: Any) -> Any:
        return self._js.replyToEmail(message)

    def on_request(self, request: Any) -> Any:
        return self._js.onRequest(request)

    def on_connect(self, connection: Any, ctx: Any) -> Any:
        return self._js.onConnect(connection, ctx)

    def on_message(self, connection: Any, message: Any) -> Any:
        return self._js.onMessage(connection, message)

    def on_error(self, connection: Any, error: Any) -> Any:
        return self._js.onError(connection, error)

    def on_close(self, connection: Any, code: int, reason: str, was_clean: bool) -> Any:
        return self._js.onClose(connection, code, reason, was_clean)

    def on_email(self, email: Any) -> Any:
        return self._js.onEmail(email)

    def __getattr__(self, name: str) -> Any:
        """Fallback to direct JS access for APIs not yet wrapped."""
        return getattr(self._js, name)


def _load_default_bridge() -> Any:
    from js import __PYTHON_AGENTS_SDK__  # pylint: disable=import-error

    return __PYTHON_AGENTS_SDK__
