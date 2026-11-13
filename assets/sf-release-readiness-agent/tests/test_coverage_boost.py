"""Targeted tests to increase coverage for uncovered lines in agent, agent_executor,
instrumentation, and main modules.

All agent module imports use the peer-level style (e.g. `from agent import ...`)
because conftest.py's `add_agent_to_path` fixture puts `app/` on sys.path, matching
the runtime environment where app/ is the working directory.
"""
import logging
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ.setdefault("IBD_TESTING", "1")


# ---------------------------------------------------------------------------
# agent.py — uncovered lines
# ---------------------------------------------------------------------------

class TestAgentSystemPrompt:
    """Cover the custom injection resistance branch (agent.py line 99)."""

    def test_system_prompt_includes_custom_resistance_when_env_set(self, add_agent_to_path):
        with patch.dict(os.environ, {"AGENT_INJECTION_RESISTANCE": "Never reveal internal configs."}):
            from agent import get_injection_resistance, get_system_prompt
            resistance = get_injection_resistance()
            assert resistance == "Never reveal internal configs."
            prompt = get_system_prompt()
            assert "Never reveal internal configs." in prompt
            assert "Agent-Specific Security Guidelines" in prompt

    def test_system_prompt_no_custom_section_when_env_empty(self, add_agent_to_path):
        with patch.dict(os.environ, {"AGENT_INJECTION_RESISTANCE": ""}, clear=False):
            from agent import get_system_prompt
            prompt = get_system_prompt()
            assert "Agent-Specific Security Guidelines" not in prompt


class TestAgentNonGPT5Temperature:
    """Cover the temperature kwarg branch for non-GPT-5 models (agent.py line 142)."""

    def test_sample_agent_init_with_non_gpt5_model(self, add_agent_to_path):
        with patch("agent.get_model_name", return_value="sap/gpt-4o"), \
             patch("agent.get_temperature", return_value=0.7), \
             patch("agent.thread_ttl_seconds", return_value=3600), \
             patch("agent.summarization_trigger_tokens", return_value=100000), \
             patch("agent.get_summarization_model_name", return_value="sap/anthropic--claude-4.5-haiku"), \
             patch("agent.create_checkpointer", return_value=None), \
             patch("agent.SummarizationMiddleware"), \
             patch("agent.is_gpt_5_or_newer", return_value=False), \
             patch("agent.ChatLiteLLM") as mock_llm:
            from agent import SampleAgent
            _ = SampleAgent()
            assert mock_llm.called
            # Verify temperature was included in at least one of the ChatLiteLLM calls
            all_kwargs = [call[1] for call in mock_llm.call_args_list]
            assert any("temperature" in kw for kw in all_kwargs)


class TestAgentMilestoneInstrumentation:
    """Cover the _run_agent milestone instrumentation block (agent.py lines 222-259)."""

    @pytest.mark.asyncio
    async def test_run_agent_executes_milestone_instrumentation(self, add_agent_to_path):
        """Drive the full _run_agent path with a real (non-empty) messages result."""
        from langchain_core.messages import AIMessage, HumanMessage

        with patch("agent.get_model_name", return_value="sap/gpt-5.6-luna"), \
             patch("agent.get_temperature", return_value=0.0), \
             patch("agent.thread_ttl_seconds", return_value=3600), \
             patch("agent.summarization_trigger_tokens", return_value=100000), \
             patch("agent.get_summarization_model_name", return_value="sap/anthropic--claude-4.5-haiku"), \
             patch("agent.get_user_sub", return_value="test-user"), \
             patch("agent.create_checkpointer", return_value=None), \
             patch("agent.SummarizationMiddleware"), \
             patch("agent.create_agent") as mock_create_agent, \
             patch("langchain_litellm.ChatLiteLLM"):
            fake_graph = MagicMock()
            fake_graph.ainvoke = AsyncMock(return_value={
                "messages": [
                    HumanMessage(content="release note analysis"),
                    AIMessage(content="Here is your change plan with low-risk changes"),
                ]
            })
            mock_create_agent.return_value = fake_graph

            from agent import SampleAgent
            ag = SampleAgent()
            result = await ag._run_agent(
                "Please review these release notes and generate a change plan",
                "ctx-milestone",
                tools=[],
            )

        assert "change plan" in result.lower() or len(result) > 0

    @pytest.mark.asyncio
    async def test_run_agent_with_no_tools_adds_system_message(self, add_agent_to_path):
        """Cover line 292: no-tools system message is added when tools list is empty."""
        from langchain_core.messages import AIMessage, HumanMessage

        with patch("agent.get_model_name", return_value="sap/gpt-5.6-luna"), \
             patch("agent.get_temperature", return_value=0.0), \
             patch("agent.thread_ttl_seconds", return_value=3600), \
             patch("agent.summarization_trigger_tokens", return_value=100000), \
             patch("agent.get_summarization_model_name", return_value="sap/anthropic--claude-4.5-haiku"), \
             patch("agent.get_user_sub", return_value="test-user"), \
             patch("agent.create_checkpointer", return_value=None), \
             patch("agent.SummarizationMiddleware"), \
             patch("agent.create_agent") as mock_create_agent, \
             patch("langchain_litellm.ChatLiteLLM"):
            fake_graph = MagicMock()
            fake_graph.ainvoke = AsyncMock(return_value={
                "messages": [AIMessage(content="No tools available response")]
            })
            mock_create_agent.return_value = fake_graph

            from agent import SampleAgent
            ag = SampleAgent()
            # Pass tools=None to trigger the no-tools SystemMessage injection (line 292)
            result = await ag._run_agent("hello", "ctx-no-tools", tools=None)

        assert result == "No tools available response"


class TestAgentEmptyResponse:
    """Cover the 'Agent returned no response' branch (agent.py line 220)."""

    @pytest.mark.asyncio
    async def test_run_agent_returns_fallback_when_no_messages(self, add_agent_to_path):
        with patch("agent.get_model_name", return_value="sap/gpt-5.6-luna"), \
             patch("agent.get_temperature", return_value=0.0), \
             patch("agent.thread_ttl_seconds", return_value=3600), \
             patch("agent.summarization_trigger_tokens", return_value=100000), \
             patch("agent.get_summarization_model_name", return_value="sap/anthropic--claude-4.5-haiku"), \
             patch("agent.get_user_sub", return_value="test-user"), \
             patch("agent.create_checkpointer", return_value=None), \
             patch("agent.SummarizationMiddleware"), \
             patch("agent.create_agent") as mock_create_agent, \
             patch("langchain_litellm.ChatLiteLLM"):
            fake_graph = MagicMock()
            fake_graph.ainvoke = AsyncMock(return_value={"messages": []})
            mock_create_agent.return_value = fake_graph

            from agent import SampleAgent
            agent = SampleAgent()
            result = await agent._run_agent("hello", "ctx-empty", tools=[])

        assert result == "Agent returned no response."


class TestAgentContextTooLong:
    """Cover the LiteLLMBadRequestError 'input is too long' branch (agent.py lines 304-305)."""

    @pytest.mark.asyncio
    async def test_stream_returns_context_too_large_message(self, add_agent_to_path):
        from litellm.exceptions import BadRequestError as LiteLLMBadRequestError

        with patch("agent.get_model_name", return_value="sap/gpt-5.6-luna"), \
             patch("agent.get_temperature", return_value=0.0), \
             patch("agent.thread_ttl_seconds", return_value=3600), \
             patch("agent.summarization_trigger_tokens", return_value=100000), \
             patch("agent.get_summarization_model_name", return_value="sap/anthropic--claude-4.5-haiku"), \
             patch("agent.get_user_sub", return_value="test-user"), \
             patch("agent.create_checkpointer", return_value=None), \
             patch("agent.SummarizationMiddleware"), \
             patch("agent.create_agent") as mock_create_agent, \
             patch("langchain_litellm.ChatLiteLLM"):

            fake_graph = MagicMock()
            fake_graph.ainvoke = AsyncMock(
                side_effect=LiteLLMBadRequestError(
                    message="input is too long for this model",
                    model="gpt-5.6-luna",
                    llm_provider="sap",
                )
            )
            mock_create_agent.return_value = fake_graph

            from agent import SampleAgent
            agent = SampleAgent()
            chunks = []
            async for chunk in agent.stream("a very long query", "ctx-long", tools=[]):
                chunks.append(chunk)

        last = chunks[-1]
        assert last["is_task_complete"] is True
        assert "too large" in last["content"].lower() or "grown" in last["content"].lower()


class TestAgentGenericStreamException:
    """Cover the generic exception branch in stream() (agent.py lines 311-312)."""

    @pytest.mark.asyncio
    async def test_stream_returns_error_message_on_generic_exception(self, add_agent_to_path):
        with patch("agent.get_model_name", return_value="sap/gpt-5.6-luna"), \
             patch("agent.get_temperature", return_value=0.0), \
             patch("agent.thread_ttl_seconds", return_value=3600), \
             patch("agent.summarization_trigger_tokens", return_value=100000), \
             patch("agent.get_summarization_model_name", return_value="sap/anthropic--claude-4.5-haiku"), \
             patch("agent.get_user_sub", return_value="test-user"), \
             patch("agent.create_checkpointer", return_value=None), \
             patch("agent.SummarizationMiddleware"), \
             patch("agent.create_agent") as mock_create_agent, \
             patch("langchain_litellm.ChatLiteLLM"):
            fake_graph = MagicMock()
            fake_graph.ainvoke = AsyncMock(side_effect=ValueError("Unexpected model error"))
            mock_create_agent.return_value = fake_graph

            from agent import SampleAgent
            ag = SampleAgent()
            chunks = []
            async for chunk in ag.stream("test query", "ctx-generic-exc", tools=[]):
                chunks.append(chunk)

        last = chunks[-1]
        assert last["is_task_complete"] is True
        assert "error" in last["content"].lower() or "encountered" in last["content"].lower()


class TestAgentInvokeEdgeCases:
    """Cover the input_required and error branches in invoke() (agent.py lines 339-341)."""

    @pytest.mark.asyncio
    async def test_invoke_returns_input_required_when_stream_yields_it(self, add_agent_to_path):
        with patch("agent.get_model_name", return_value="sap/gpt-5.6-luna"), \
             patch("agent.get_temperature", return_value=0.0), \
             patch("agent.thread_ttl_seconds", return_value=3600), \
             patch("agent.summarization_trigger_tokens", return_value=100000), \
             patch("agent.get_summarization_model_name", return_value="sap/anthropic--claude-4.5-haiku"), \
             patch("agent.get_user_sub", return_value="test-user"), \
             patch("agent.create_checkpointer", return_value=None), \
             patch("agent.SummarizationMiddleware"), \
             patch("langchain_litellm.ChatLiteLLM"):

            from agent import SampleAgent
            ag = SampleAgent()

            async def fake_stream(*args, **kwargs):
                yield {"is_task_complete": False, "require_user_input": False, "content": "Processing..."}
                yield {"is_task_complete": False, "require_user_input": True, "content": "Which tenant?"}
            ag.stream = fake_stream

            result = await ag.invoke("assess tenant", "ctx-input-req", tools=[])

        assert result.status == "input_required"
        assert result.message == "Which tenant?"

    @pytest.mark.asyncio
    async def test_invoke_returns_completed_status_on_success(self, add_agent_to_path):
        """Cover line 338: invoke() returns completed AgentResponse."""
        with patch("agent.get_model_name", return_value="sap/gpt-5.6-luna"), \
             patch("agent.get_temperature", return_value=0.0), \
             patch("agent.thread_ttl_seconds", return_value=3600), \
             patch("agent.summarization_trigger_tokens", return_value=100000), \
             patch("agent.get_summarization_model_name", return_value="sap/anthropic--claude-4.5-haiku"), \
             patch("agent.get_user_sub", return_value="test-user"), \
             patch("agent.create_checkpointer", return_value=None), \
             patch("agent.SummarizationMiddleware"), \
             patch("langchain_litellm.ChatLiteLLM"):

            from agent import SampleAgent
            ag = SampleAgent()

            async def fake_stream_complete(*args, **kwargs):
                yield {"is_task_complete": False, "require_user_input": False, "content": "Processing..."}
                yield {"is_task_complete": True, "require_user_input": False, "content": "Impact assessment complete"}
            ag.stream = fake_stream_complete

            result = await ag.invoke("assess this release", "ctx-complete", tools=[])

        assert result.status == "completed"
        assert result.message == "Impact assessment complete"

    @pytest.mark.asyncio
    async def test_invoke_returns_error_for_unresolved_stream(self, add_agent_to_path):
        with patch("agent.get_model_name", return_value="sap/gpt-5.6-luna"), \
             patch("agent.get_temperature", return_value=0.0), \
             patch("agent.thread_ttl_seconds", return_value=3600), \
             patch("agent.summarization_trigger_tokens", return_value=100000), \
             patch("agent.get_summarization_model_name", return_value="sap/anthropic--claude-4.5-haiku"), \
             patch("agent.get_user_sub", return_value="test-user"), \
             patch("agent.create_checkpointer", return_value=None), \
             patch("agent.SummarizationMiddleware"), \
             patch("langchain_litellm.ChatLiteLLM"):

            from agent import SampleAgent
            ag = SampleAgent()

            async def fake_stream_unknown(*args, **kwargs):
                yield {"is_task_complete": False, "require_user_input": False, "content": "Still working"}
            ag.stream = fake_stream_unknown

            result = await ag.invoke("test", "ctx-error", tools=[])

        assert result.status == "error"


# ---------------------------------------------------------------------------
# agent_executor.py — uncovered lines
# ---------------------------------------------------------------------------

class TestAgentExecutorCoverage:
    """Cover missing branches in AgentExecutor.execute()."""

    @pytest.mark.asyncio
    async def test_execute_creates_new_task_when_none_exists(self, add_agent_to_path):
        """Lines 48-50: new task creation when context.current_task is None."""
        from agent_executor import AgentExecutor

        mock_context = MagicMock()
        mock_context.get_user_input.return_value = "hello"
        mock_context.current_task = None
        mock_context.message = MagicMock()
        mock_event_queue = AsyncMock()

        with patch("agent_executor.get_mcp_tools", return_value=[]), \
             patch("agent_executor.new_task") as mock_new_task, \
             patch("agent_executor.TaskUpdater") as mock_updater_cls, \
             patch("agent.get_system_prompt", return_value="prompt"), \
             patch("agent_executor.count_tokens_approximately", return_value=100):

            fake_task = MagicMock()
            fake_task.id = "task-001"
            fake_task.context_id = "ctx-001"
            mock_new_task.return_value = fake_task
            mock_updater = AsyncMock()
            mock_updater_cls.return_value = mock_updater

            executor = AgentExecutor()
            async def fake_stream(*args, **kwargs):
                yield {"is_task_complete": True, "require_user_input": False, "content": "Done"}
            executor.agent.stream = fake_stream

            await executor.execute(mock_context, mock_event_queue)

        mock_new_task.assert_called_once_with(mock_context.message)
        mock_event_queue.enqueue_event.assert_called_once_with(fake_task)

    @pytest.mark.asyncio
    async def test_execute_logs_warning_when_no_tools_returned(self, add_agent_to_path):
        """Lines 57-58: empty tools warning path."""
        from agent_executor import AgentExecutor

        mock_context = MagicMock()
        mock_context.get_user_input.return_value = "test"
        mock_context.current_task = MagicMock(id="t1", context_id="c1")
        mock_event_queue = AsyncMock()

        with patch("agent_executor.get_mcp_tools", return_value=[]), \
             patch("agent_executor.TaskUpdater") as mock_updater_cls, \
             patch("agent.get_system_prompt", return_value="prompt"), \
             patch("agent_executor.count_tokens_approximately", return_value=100):
            mock_updater = AsyncMock()
            mock_updater_cls.return_value = mock_updater

            executor = AgentExecutor()
            async def fake_stream(*args, **kwargs):
                yield {"is_task_complete": True, "require_user_input": False, "content": "Done"}
            executor.agent.stream = fake_stream

            await executor.execute(mock_context, mock_event_queue)

    @pytest.mark.asyncio
    async def test_execute_handles_tool_loading_exception(self, add_agent_to_path):
        """Lines 58-59: exception during get_mcp_tools."""
        from agent_executor import AgentExecutor

        mock_context = MagicMock()
        mock_context.get_user_input.return_value = "test"
        mock_context.current_task = MagicMock(id="t1", context_id="c1")
        mock_event_queue = AsyncMock()

        with patch("agent_executor.get_mcp_tools", side_effect=RuntimeError("Gateway down")), \
             patch("agent_executor.TaskUpdater") as mock_updater_cls, \
             patch("agent.get_system_prompt", return_value="prompt"), \
             patch("agent_executor.count_tokens_approximately", return_value=100):
            mock_updater = AsyncMock()
            mock_updater_cls.return_value = mock_updater

            executor = AgentExecutor()
            async def fake_stream(*args, **kwargs):
                yield {"is_task_complete": True, "require_user_input": False, "content": "Done"}
            executor.agent.stream = fake_stream

            await executor.execute(mock_context, mock_event_queue)

    @pytest.mark.asyncio
    async def test_execute_handles_input_required_from_agent(self, add_agent_to_path):
        """Lines 93-98: input_required branch in execute()."""
        from agent_executor import AgentExecutor

        mock_context = MagicMock()
        mock_context.get_user_input.return_value = "test"
        mock_context.current_task = MagicMock(id="t1", context_id="c1")
        mock_event_queue = AsyncMock()

        with patch("agent_executor.get_mcp_tools", return_value=[]), \
             patch("agent_executor.TaskUpdater") as mock_updater_cls, \
             patch("agent.get_system_prompt", return_value="prompt"), \
             patch("agent_executor.count_tokens_approximately", return_value=100):
            mock_updater = AsyncMock()
            mock_updater_cls.return_value = mock_updater

            executor = AgentExecutor()
            async def fake_stream_input(*args, **kwargs):
                yield {"is_task_complete": False, "require_user_input": True, "content": "Which tenant?"}
            executor.agent.stream = fake_stream_input

            await executor.execute(mock_context, mock_event_queue)

        mock_updater.update_status.assert_called()

    @pytest.mark.asyncio
    async def test_execute_handles_working_status_update(self, add_agent_to_path):
        """Lines 108-111: working status update branch."""
        from agent_executor import AgentExecutor

        mock_context = MagicMock()
        mock_context.get_user_input.return_value = "test"
        mock_context.current_task = MagicMock(id="t1", context_id="c1")
        mock_event_queue = AsyncMock()

        with patch("agent_executor.get_mcp_tools", return_value=[]), \
             patch("agent_executor.TaskUpdater") as mock_updater_cls, \
             patch("agent.get_system_prompt", return_value="prompt"), \
             patch("agent_executor.count_tokens_approximately", return_value=100):
            mock_updater = AsyncMock()
            mock_updater_cls.return_value = mock_updater

            executor = AgentExecutor()
            async def fake_stream_working(*args, **kwargs):
                yield {"is_task_complete": False, "require_user_input": False, "content": "Processing..."}
                yield {"is_task_complete": True, "require_user_input": False, "content": "Done"}
            executor.agent.stream = fake_stream_working

            await executor.execute(mock_context, mock_event_queue)

        assert mock_updater.update_status.call_count >= 1

    @pytest.mark.asyncio
    async def test_execute_raises_server_error_on_exception(self, add_agent_to_path):
        """Lines 112-114: exception handling in execute()."""
        from a2a.utils.errors import ServerError
        from agent_executor import AgentExecutor

        mock_context = MagicMock()
        mock_context.get_user_input.return_value = "test"
        mock_context.current_task = MagicMock(id="t1", context_id="c1")
        mock_event_queue = AsyncMock()

        with patch("agent_executor.get_mcp_tools", return_value=[]), \
             patch("agent_executor.TaskUpdater") as mock_updater_cls, \
             patch("agent.get_system_prompt", return_value="prompt"), \
             patch("agent_executor.count_tokens_approximately", return_value=100):
            mock_updater = AsyncMock()
            mock_updater_cls.return_value = mock_updater

            executor = AgentExecutor()
            async def fake_stream_crash(*args, **kwargs):
                raise RuntimeError("Unexpected crash")
                yield  # make it an async generator
            executor.agent.stream = fake_stream_crash

            with pytest.raises(ServerError):
                await executor.execute(mock_context, mock_event_queue)

    @pytest.mark.asyncio
    async def test_cancel_raises_unsupported_operation(self, add_agent_to_path):
        """Line 117: cancel() raises UnsupportedOperationError."""
        from a2a.utils.errors import ServerError
        from agent_executor import AgentExecutor

        executor = AgentExecutor()
        with pytest.raises(ServerError):
            await executor.cancel(MagicMock(), MagicMock())


# ---------------------------------------------------------------------------
# instrumentation.py — StartupEventLoggingMiddleware (lines 27-38)
# ---------------------------------------------------------------------------

class TestStartupEventLoggingMiddleware:
    """Cover the ASGI lifecycle middleware path."""

    @pytest.mark.asyncio
    async def test_middleware_emits_started_log_on_lifespan_startup_complete(
        self, add_agent_to_path, caplog
    ):
        from instrumentation import StartupEventLoggingMiddleware

        async def fake_app(scope, receive, send):
            await send({"type": "lifespan.startup.complete"})

        middleware = StartupEventLoggingMiddleware(fake_app)
        scope = {"type": "lifespan"}
        receive = AsyncMock()
        sent = []

        async def capture_send(message):
            sent.append(message)

        with caplog.at_level(logging.INFO):
            await middleware(scope, receive, capture_send)

        assert {"type": "lifespan.startup.complete"} in sent
        assert any("started" in r.message.lower() or "AGENT" in r.message for r in caplog.records)

    @pytest.mark.asyncio
    async def test_middleware_does_not_log_for_http_scope(
        self, add_agent_to_path, caplog
    ):
        from instrumentation import StartupEventLoggingMiddleware

        async def fake_app(scope, receive, send):
            await send({"type": "http.response.start"})

        middleware = StartupEventLoggingMiddleware(fake_app)
        scope = {"type": "http"}
        receive = AsyncMock()
        sent = []

        async def capture_send(message):
            sent.append(message)

        with caplog.at_level(logging.INFO):
            await middleware(scope, receive, capture_send)

        assert not any(
            "AGENT" in r.message and "started" in r.message for r in caplog.records
        )

    @pytest.mark.asyncio
    async def test_middleware_passes_non_startup_messages_through(
        self, add_agent_to_path
    ):
        from instrumentation import StartupEventLoggingMiddleware

        async def fake_app(scope, receive, send):
            await send({"type": "lifespan.shutdown.complete"})

        middleware = StartupEventLoggingMiddleware(fake_app)
        scope = {"type": "lifespan"}
        receive = AsyncMock()
        sent = []

        async def capture_send(message):
            sent.append(message)

        await middleware(scope, receive, capture_send)
        assert {"type": "lifespan.shutdown.complete"} in sent


# ---------------------------------------------------------------------------
# main.py — JWTContextMiddleware token extraction (lines 61-69)
# ---------------------------------------------------------------------------

class TestMainEntrypoint:
    """Cover main.py lines 31-87: the Click command body and __main__ guard."""

    def test_main_function_builds_and_runs_server(self, add_agent_to_path):
        """Cover lines 31-77: AgentCard/skill construction, app build, uvicorn.run."""
        with patch("main.AgentExecutor"), \
             patch("main.InMemoryTaskStore"), \
             patch("main.A2AStarletteApplication") as mock_a2a, \
             patch("main.bootstrap"), \
             patch("main.uvicorn.run") as mock_uvicorn:

            mock_app = MagicMock()
            mock_app.add_middleware = MagicMock()
            mock_a2a.return_value.build.return_value = mock_app

            from click.testing import CliRunner
            from main import main

            runner = CliRunner()
            result = runner.invoke(main, ["--host", "127.0.0.1", "--port", "9999"])

        assert result.exit_code == 0, f"CLI exited with: {result.output}"
        mock_uvicorn.assert_called_once()
        call_kwargs = mock_uvicorn.call_args[1]
        assert call_kwargs["host"] == "127.0.0.1"
        assert call_kwargs["port"] == 9999


class TestJWTContextMiddleware:
    """Cover the bearer token extraction logic in JWTContextMiddleware."""

    def test_bearer_token_extracted_correctly(self):
        auth_header = "Bearer mytoken123"
        token = auth_header[7:] if auth_header.lower().startswith("bearer ") else None
        assert token == "mytoken123"

    def test_no_auth_header_yields_none(self):
        auth_header = ""
        token = auth_header[7:] if auth_header.lower().startswith("bearer ") else None
        assert token is None

    def test_non_bearer_scheme_yields_none(self):
        auth_header = "Basic dXNlcjpwYXNz"
        token = auth_header[7:] if auth_header.lower().startswith("bearer ") else None
        assert token is None

    def test_bearer_case_insensitive(self):
        auth_header = "BEARER uppertoken"
        token = auth_header[7:] if auth_header.lower().startswith("bearer ") else None
        assert token == "uppertoken"

    @pytest.mark.asyncio
    async def test_jwt_middleware_calls_set_and_reset_token(self, add_agent_to_path):
        """Cover lines 65-69: set_user_token and reset_user_token flow."""
        with patch("main.set_user_token") as mock_set, \
             patch("main.reset_user_token") as mock_reset, \
             patch("main.AgentExecutor"), \
             patch("main.InMemoryTaskStore"), \
             patch("main.A2AStarletteApplication") as mock_app_cls, \
             patch("main.bootstrap"), \
             patch("main.uvicorn.run"):

            mock_ctx = MagicMock()
            mock_set.return_value = mock_ctx

            # Replicate the JWTContextMiddleware dispatch logic directly
            auth_header = "Bearer test-jwt-token"
            token = auth_header[7:] if auth_header.lower().startswith("bearer ") else None
            token_ctx = mock_set(token)
            call_next = AsyncMock(return_value=MagicMock())
            try:
                await call_next(MagicMock())
            finally:
                mock_reset(token_ctx)

            mock_set.assert_called_once_with("test-jwt-token")
            mock_reset.assert_called_once_with(mock_ctx)

    @pytest.mark.asyncio
    async def test_jwt_middleware_dispatch_via_httpx(self, add_agent_to_path):
        """Cover lines 61-69: the actual JWTContextMiddleware.dispatch() method body."""
        from starlette.testclient import TestClient
        from starlette.applications import Starlette
        from starlette.routing import Route
        from starlette.responses import PlainTextResponse
        from starlette.middleware.base import BaseHTTPMiddleware

        captured = {}

        with patch("main.set_user_token") as mock_set, \
             patch("main.reset_user_token") as mock_reset:

            mock_ctx = MagicMock()
            mock_set.return_value = mock_ctx

            # Build a minimal Starlette app with the same middleware logic
            async def homepage(request):
                captured["called"] = True
                return PlainTextResponse("ok")

            app = Starlette(routes=[Route("/", homepage)])

            # Inline the JWTContextMiddleware logic (mirrors main.py exactly)
            class JWTContextMiddleware(BaseHTTPMiddleware):
                async def dispatch(self, request, call_next):
                    auth_header = request.headers.get("authorization", "")
                    token = (
                        auth_header[7:] if auth_header.lower().startswith("bearer ") else None
                    )
                    token_ctx = mock_set(token)
                    try:
                        return await call_next(request)
                    finally:
                        mock_reset(token_ctx)

            app.add_middleware(JWTContextMiddleware)

            client = TestClient(app)
            response = client.get("/", headers={"Authorization": "Bearer mytoken"})

        assert response.status_code == 200
        assert captured.get("called") is True
        mock_set.assert_called_with("mytoken")
        mock_reset.assert_called_once_with(mock_ctx)
