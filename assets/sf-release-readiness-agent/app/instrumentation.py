"""Shared logging and tracing helpers for agent lifecycle instrumentation."""

import logging

from opentelemetry import trace
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


def log_event(event_id: str, status: str, description: str) -> None:
    """Emit a structured lifecycle or milestone log entry."""
    logger.info("[%s.%s]: %s", event_id, status, description)


def log_milestone(milestone_id: str, achieved: bool, description: str) -> None:
    """Emit an achieved/missed log for a PRD-defined business milestone."""
    status = "achieved" if achieved else "missed"
    log_event(milestone_id, status, description)


class StartupEventLoggingMiddleware:
    """Log agent startup only after the ASGI app reports startup complete."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async def send_with_startup_log(message: Message) -> None:
            if (
                scope.get("type") == "lifespan"
                and message.get("type") == "lifespan.startup.complete"
            ):
                log_event("AGENT", "started", "A2A server startup completed")
            await send(message)

        await self.app(scope, receive, send_with_startup_log)
