from cloudflare_python_agents import Agent


class FakeJsAgent:
    def __init__(self):
        self.state = {"count": 0}
        self.env = {"mode": "test"}
        self.ctx = {"requestId": "abc"}
        self.calls = []

    def _record(self, name, *args):
        self.calls.append((name, args))
        return {"name": name, "args": args}

    def setState(self, state):
        return self._record("setState", state)

    def schedule(self, when, callback, payload):
        return self._record("schedule", when, callback, payload)

    def scheduleEvery(self, schedule, callback, payload):
        return self._record("scheduleEvery", schedule, callback, payload)

    def getSchedules(self):
        return self._record("getSchedules")

    def cancelSchedule(self, schedule_id):
        return self._record("cancelSchedule", schedule_id)

    def queue(self, callback, payload):
        return self._record("queue", callback, payload)

    def dequeue(self):
        return self._record("dequeue")

    def dequeueAll(self):
        return self._record("dequeueAll")

    def getQueue(self):
        return self._record("getQueue")

    def broadcast(self, message):
        return self._record("broadcast", message)

    def runWorkflow(self, workflow, payload):
        return self._record("runWorkflow", workflow, payload)

    def waitForApproval(self, key, payload):
        return self._record("waitForApproval", key, payload)

    def addMcpServer(self, name, config):
        return self._record("addMcpServer", name, config)

    def removeMcpServer(self, name):
        return self._record("removeMcpServer", name)

    def getMcpServers(self):
        return self._record("getMcpServers")


class FakeBridge:
    def __init__(self):
        self.last_options = None
        self.agent = FakeJsAgent()

    def createAgent(self, options):
        self.last_options = options
        return self.agent


def test_constructs_js_agent_with_pythonic_options():
    bridge = FakeBridge()
    Agent("user-123", initial_state={"count": 1}, props={"tier": "pro"}, bridge=bridge)
    assert bridge.last_options == {
        "name": "user-123",
        "initialState": {"count": 1},
        "props": {"tier": "pro"},
    }


def test_wraps_core_agent_methods():
    bridge = FakeBridge()
    agent = Agent("user-1", bridge=bridge)

    agent.set_state({"count": 2})
    agent.schedule("2026-01-01T00:00:00.000Z", "send_reminder", {"id": "a"})
    agent.schedule_every("*/5 * * * *", "flush")
    agent.get_schedules()
    agent.cancel_schedule("sch_1")
    agent.queue("do_work", {"batch": 3})
    agent.dequeue()
    agent.dequeue_all()
    agent.get_queue()
    agent.broadcast({"kind": "ping"})
    agent.run_workflow("wf", {"foo": "bar"})
    agent.wait_for_approval("appr")
    agent.add_mcp_server("docs", {"url": "https://example.com"})
    agent.remove_mcp_server("docs")
    agent.get_mcp_servers()

    method_names = [name for (name, _args) in bridge.agent.calls]
    assert method_names == [
        "setState",
        "schedule",
        "scheduleEvery",
        "getSchedules",
        "cancelSchedule",
        "queue",
        "dequeue",
        "dequeueAll",
        "getQueue",
        "broadcast",
        "runWorkflow",
        "waitForApproval",
        "addMcpServer",
        "removeMcpServer",
        "getMcpServers",
    ]


def test_wrap_existing_js_agent():
    js_agent = FakeJsAgent()
    agent = Agent.from_js(js_agent)

    assert agent.state == {"count": 0}
    assert agent.env == {"mode": "test"}
    assert agent.ctx == {"requestId": "abc"}
