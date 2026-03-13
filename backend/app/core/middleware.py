import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging_config import get_logger

logger = get_logger("middleware")


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log HTTP requests and responses.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process HTTP request and log details.
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
    """
    Middleware to add request context information.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add request context information.
        """
        request.state.start_time = time.time()

        response = await call_next(request)
        return response