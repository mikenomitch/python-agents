import pytest

from python_agents import Agent


class JsState:
    def __init__(self, data):
        self._data = data

    def to_py(self):
        return self._data


class FakeJsAgent:
    def __init__(self):
        self.currentState = JsState({"count": 1})

    async def setState(self, *payload):
        return list(payload)

    async def scheduleEvery(self, cron):
        return f"scheduled:{cron}"


@pytest.mark.asyncio
async def test_snake_case_method_forwards_to_camel_case():
    agent = Agent(FakeJsAgent())
    result = await agent.schedule_every("* * * * *")
    assert result == "scheduled:* * * * *"


@pytest.mark.asyncio
async def test_kwargs_are_sent_as_final_options_argument():
    agent = Agent(FakeJsAgent())
    result = await agent.set_state({"count": 2}, source="test")
    assert result == [{"count": 2}, {"source": "test"}]


def test_property_reads_are_converted_to_python_values():
    agent = Agent(FakeJsAgent())
    assert agent.current_state == {"count": 1}
