"""Verify tool failures reach the next model turn without AI Core access."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from pydantic import BaseModel, PrivateAttr

pytestmark = pytest.mark.structure


class _NoArguments(BaseModel):
    """Generic no-argument tool schema."""


class _RecordingFakeChatModel(GenericFakeChatModel):
    """A minimal tool-calling fake model that records each model input."""

    _inputs: list = PrivateAttr(default_factory=list)

    def bind_tools(self, tools, *, tool_choice=None, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self._inputs.append(messages)
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)


@pytest.mark.asyncio
async def test_gateway_tool_error_is_passed_to_model(add_agent_to_path):
    from langchain.agents import create_agent
    from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
    from langchain_core.tools import StructuredTool
    from util import call_mcp_tool

    client = MagicMock()
    client.call_mcp_tool = AsyncMock(
        side_effect=RuntimeError("destination returned 401")
    )
    mcp_tool = MagicMock()
    mcp_tool.name = "read_record"

    async def invoke_failing_mcp_tool():
        return await call_mcp_tool(client, mcp_tool)

    tool = StructuredTool(
        name="read_record",
        description="Read a record.",
        args_schema=_NoArguments,
        func=lambda: None,
        coroutine=invoke_failing_mcp_tool,
        handle_tool_error=True,
    )
    model = _RecordingFakeChatModel(
        messages=iter(
            [
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "read_record",
                            "args": {},
                            "id": "tool-call-1",
                            "type": "tool_call",
                        }
                    ],
                ),
                AIMessage(content="The tool returned a 401 error."),
            ]
        )
    )
    graph = create_agent(model, tools=[tool], system_prompt="Use the tool if needed.")

    result = await graph.ainvoke(
        {"messages": [HumanMessage(content="Read the sample record.")]}
    )

    assert result["messages"][-1].content == "The tool returned a 401 error."
    model_received_tool_error = [
        message for message in model._inputs[-1] if isinstance(message, ToolMessage)
    ]
    assert len(model_received_tool_error) == 1
    assert model_received_tool_error[0].name == "read_record"
    assert "401" in str(model_received_tool_error[0].content)
