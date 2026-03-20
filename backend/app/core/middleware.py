import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging_config import get_logger

logger = get_logger("middleware")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Logs request start, duration, status, and attaches ``X-Request-ID`` headers."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Invokes the next ASGI handler and logs timing and outcome.

        Args:
            request: Incoming HTTP request; ``request.state.request_id`` is set.
            call_next: Next middleware or route handler.

        Returns:
            Response: Downstream response with diagnostic headers.

        Raises:
            Exception: Re-raised after logging on failure.

        """
        request_id = str(uuid.uuid4())
        start_time = time.time()

        request.state.request_id = request_id

        logger.info(
            f"Request started - ID: {request_id} | "
            f"Method: {request.method} | "
            f"URL: {request.url} | "
            f"Client: {request.client.host if request.client else 'unknown'} | "
            f"User-Agent: {request.headers.get('user-agent', 'unknown')}"
        )

        try:
            response = await call_next(request)

            process_time = time.time() - start_time

            if response.status_code == 422:
                logger.warning(
                    f"Validation error - ID: {request_id} | "
                    f"Status: 422 | "
                    f"Processing time: {process_time:.4f}s"
                )

            logger.info(
                f"Request completed - ID: {request_id} | "
                f"Status: {response.status_code} | "
                f"Processing time: {process_time:.4f}s"
            )

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.4f}"

            return response

        except Exception as exc:
            process_time = time.time() - start_time

            logger.error(
                f"Request failed - ID: {request_id} | "
                f"Error: {str(exc)} | "
                f"Processing time: {process_time:.4f}s",
                exc_info=True,
            )

            raise exc


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Stores request start time on ``request.state`` for downstream use."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Sets ``request.state.start_time`` before delegating.

        Args:
            request: Incoming request.
            call_next: Next handler in the stack.

        Returns:
            Response: Downstream response unchanged.

        """
        request.state.start_time = time.time()

        response = await call_next(request)
        return response
