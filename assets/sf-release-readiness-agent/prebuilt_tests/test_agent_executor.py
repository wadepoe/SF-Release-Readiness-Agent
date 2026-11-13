"""Unit tests for A2A request handling in AgentExecutor."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

pytestmark = pytest.mark.structure


@pytest.mark.asyncio
async def test_execute_loads_tools_and_completes_task(add_agent_to_path, monkeypatch):
    import agent as agent_module
    import agent_executor as executor_module

    mcp_tool = object()
    datetime_tool = object()
    skill_tool = object()
    received = {}

    class FakeAgent:
        async def stream(self, query, context_id, tools):
            received.update(query=query, context_id=context_id, tools=tools)
            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": "completed",
            }

    updater = SimpleNamespace(
        add_artifact=AsyncMock(), complete=AsyncMock(), update_status=AsyncMock()
    )
    monkeypatch.setattr(executor_module, "SampleAgent", FakeAgent)
    monkeypatch.setattr(executor_module, "get_datetime_tool", lambda: datetime_tool)
    monkeypatch.setattr(
        executor_module, "get_load_skill_resource_tool", lambda: [skill_tool]
    )
    get_tools = AsyncMock(return_value=[mcp_tool])
    monkeypatch.setattr(executor_module, "get_mcp_tools", get_tools)
    monkeypatch.setattr(executor_module, "wrap_tool", lambda tool: tool)
    monkeypatch.setattr(
        executor_module, "count_tokens_approximately", Mock(side_effect=[5, 12])
    )
    monkeypatch.setattr(agent_module, "get_system_prompt", lambda: "system prompt")
    monkeypatch.setattr(executor_module, "TaskUpdater", lambda *args: updater)

    executor = executor_module.AgentExecutor()
    task = SimpleNamespace(id="task-1", context_id="context-1")
    context = SimpleNamespace(get_user_input=lambda: "process this", current_task=task)
    event_queue = object()

    await executor.execute(context, event_queue)

    get_tools.assert_awaited_once_with()
    assert received == {
        "query": "process this",
        "context_id": "context-1",
        "tools": [mcp_tool, datetime_tool, skill_tool],
    }
    updater.add_artifact.assert_awaited_once()
    updater.complete.assert_awaited_once_with()
    updater.update_status.assert_not_awaited()
