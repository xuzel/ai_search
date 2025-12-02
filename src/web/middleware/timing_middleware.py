"""Request Timing Middleware

Middleware to log the response time for all API requests.
Automatically captures request start time and logs the duration when response is sent.
"""

import time
import os
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.utils.logger import get_logger

logger = get_logger(__name__)


class TimingMiddleware(BaseHTTPMiddleware):
    """Middleware to measure and log request processing time

    This middleware automatically logs the time taken to process each request,
    including the HTTP method, path, query parameters (if any), status code,
    and duration in seconds.

    Configuration:
        LOG_REQUEST_TIMING: Enable/disable timing logs (default: true)
        LOG_LEVEL: Control log verbosity (set in .env)

    Example log output:
        [TIMING] POST /query - 2.450s - Status: 200 - Query: "天气查询"
        [TIMING] POST /search - 5.123s - Status: 200
        [TIMING] GET /health - 0.001s - Status: 200
    """

    def __init__(self, app: ASGIApp, enabled: bool = True):
        """Initialize timing middleware

        Args:
            app: FastAPI application
            enabled: Whether timing logging is enabled (default: True)
        """
        super().__init__(app)
        self.enabled = enabled

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log timing information

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            HTTP response
        """
        # Skip timing if disabled
        if not self.enabled:
            return await call_next(request)

        # Record start time with high precision
        start_time = time.perf_counter()

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log error timing
            duration = time.perf_counter() - start_time
            logger.error(
                f"[TIMING] {request.method} {request.url.path} - "
                f"{duration:.3f}s - Status: ERROR - Exception: {str(e)}"
            )
            raise

        # Calculate duration
        duration = time.perf_counter() - start_time

        # Extract query info if available (for POST requests with query parameter)
        query_info = ""
        if request.method == "POST":
            # Try to get query from various possible locations
            try:
                # Check if there's a query parameter in the URL
                query_param = request.query_params.get("query", "")
                if query_param:
                    query_info = f' - Query: "{query_param[:50]}..."' if len(query_param) > 50 else f' - Query: "{query_param}"'
            except:
                pass

        # Format timing information
        status_code = response.status_code
        method = request.method
        path = request.url.path

        # Use different log levels based on duration
        # INFO: normal requests (< 5s)
        # WARNING: slow requests (5-10s)
        # ERROR: very slow requests (> 10s)
        if duration > 10:
            log_level = logger.error
            prefix = "[TIMING-SLOW]"
        elif duration > 5:
            log_level = logger.warning
            prefix = "[TIMING-SLOW]"
        else:
            log_level = logger.info
            prefix = "[TIMING]"

        # Log timing information
        log_message = (
            f"{prefix} {method} {path} - "
            f"{duration:.3f}s - Status: {status_code}{query_info}"
        )
        log_level(log_message)

        # Also print to ensure visibility (remove this after debugging)
        print(log_message, flush=True)

        return response


def setup_timing_middleware(app: ASGIApp) -> None:
    """Setup timing middleware for the application

    Args:
        app: FastAPI application instance

    Configuration via environment variables:
        LOG_REQUEST_TIMING: Enable/disable timing (default: "true")
    """
    # Check if timing is enabled via environment variable
    enabled = os.getenv("LOG_REQUEST_TIMING", "true").lower() in ("true", "1", "yes")

    if enabled:
        logger.info("Request timing middleware enabled")
        app.add_middleware(TimingMiddleware, enabled=True)
    else:
        logger.info("Request timing middleware disabled")
