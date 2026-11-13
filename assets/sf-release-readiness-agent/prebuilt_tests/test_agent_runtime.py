"""Public behavior tests for the generic agent runtime."""

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, BaseMessage
from pydantic import PrivateAttr

pytestmark = pytest.mark.structure


class _ScriptedChatModel(GenericFakeChatModel):
    """Return scripted AI messages without using an external model provider."""

    _inputs: list[list[BaseMessage]] = PrivateAttr(default_factory=list)

    def bind_tools(self, tools, *, tool_choice=None, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self._inputs.append(messages)
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)


class _FailingChatModel(_ScriptedChatModel):
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self._inputs.append(messages)
        raise RuntimeError("simulated model failure")


def _make_agent(monkeypatch, model: GenericFakeChatModel):
    import agent as agent_module

    monkeypatch.setattr(agent_module, "ChatLiteLLM", lambda *args, **kwargs: model)
    return agent_module.SampleAgent()


@pytest.mark.asyncio
async def test_stream_returns_scripted_model_response(add_agent_to_path, monkeypatch):
    model = _ScriptedChatModel(messages=iter([AIMessage(content="generic reply")]))
    agent = _make_agent(monkeypatch, model)

    chunks = [chunk async for chunk in agent.stream("question", "context", tools=[])]

    assert chunks[0]["content"] == "Processing..."
    assert chunks[-1] == {
        "is_task_complete": True,
        "require_user_input": False,
        "content": "generic reply",
    }


@pytest.mark.asyncio
async def test_invoke_returns_completed_response(add_agent_to_path, monkeypatch):
    model = _ScriptedChatModel(messages=iter([AIMessage(content="generic reply")]))
    agent = _make_agent(monkeypatch, model)

    response = await agent.invoke("question", "context", tools=[])

    assert response.status == "completed"
    assert response.message == "generic reply"


@pytest.mark.asyncio
async def test_stream_returns_safe_response_when_model_fails(
    add_agent_to_path, monkeypatch
):
    model = _FailingChatModel(messages=iter([]))
    agent = _make_agent(monkeypatch, model)

    chunks = [chunk async for chunk in agent.stream("question", "context", tools=[])]

    assert chunks[-1] == {
        "is_task_complete": True,
        "require_user_input": False,
        "content": "I encountered an error while processing your request.",
    }
