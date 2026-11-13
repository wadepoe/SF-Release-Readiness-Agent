"""Unit tests for A2A application construction in main.py."""

from importlib import import_module
from unittest.mock import Mock

import pytest

pytestmark = pytest.mark.structure


def test_main_builds_agent_card_and_bootstraps_after_build(
    add_agent_to_path, monkeypatch
):
    from sap_cloud_sdk import aicore

    events = []
    monkeypatch.delenv("AGENT_PUBLIC_URL", raising=False)
    monkeypatch.setattr(
        aicore, "set_aicore_config", lambda: events.append("aicore_config")
    )
    main_module = import_module("main")

    middleware = []

    class FakeApp:
        def add_middleware(self, middleware_class):
            middleware.append(middleware_class)

    app = FakeApp()

    class FakeServer:
        def build(self):
            events.append("build")
            return app

    server_args = {}
    monkeypatch.setattr(
        main_module,
        "A2AStarletteApplication",
        lambda **kwargs: server_args.update(kwargs) or FakeServer(),
    )
    monkeypatch.setattr(main_module, "DefaultRequestHandler", lambda **kwargs: kwargs)
    monkeypatch.setattr(main_module, "InMemoryTaskStore", lambda: "task-store")
    monkeypatch.setattr(main_module, "AgentExecutor", lambda: "agent-executor")
    monkeypatch.setattr(
        main_module,
        "bootstrap",
        lambda target: events.append("bootstrap") if target is app else None,
    )
    monkeypatch.setattr(main_module.uvicorn, "run", Mock())

    main_module.main.callback(host="127.0.0.1", port=9000)

    assert server_args["agent_card"] is not None
    assert server_args["http_handler"]["agent_executor"] == "agent-executor"
    assert events.index("build") < events.index("bootstrap")
    assert {middleware_class.__name__ for middleware_class in middleware} == {
        "JWTContextMiddleware",
        "StartupEventLoggingMiddleware",
    }
    main_module.uvicorn.run.assert_called_once_with(
        app,
        host="127.0.0.1",
        port=9000,
        http="h11",
        h11_max_incomplete_event_size=65536,
    )
