"""Rate Limiting Middleware for API Endpoints

Uses slowapi for rate limiting with configurable limits per endpoint.

Rate Limit Tiers:
- General endpoints: 100 requests/minute
- Query endpoints: 30 requests/minute
- File uploads: 10 requests/minute
- Heavy compute (code execution): 5 requests/minute
"""

import os

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.utils import get_logger

logger = get_logger(__name__)


# Custom key function that considers both IP and user identification
def get_identifier(request: Request) -> str:
    """Get unique identifier for rate limiting

    Uses IP address as the primary identifier. In production,
    you could extend this to use user IDs from authentication.

    Args:
        request: FastAPI request object

    Returns:
        Unique identifier string
    """
    # Get IP address
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take first IP in chain (original client IP)
        ip = forwarded.split(",")[0].strip()
    else:
        ip = get_remote_address(request)

    # Optional: Add user authentication if available
    # user_id = request.state.user_id if hasattr(request.state, 'user_id') else None
    # if user_id:
    #     return f"user:{user_id}"

    return f"ip:{ip}"


# Create limiter instance
limiter = Limiter(
    key_func=get_identifier,
    default_limits=["100/minute"],  # Default limit for all endpoints
    storage_uri=os.getenv("RATE_LIMIT_STORAGE", "memory://"),  # Use redis:// in production
    strategy="fixed-window",  # Options: fixed-window, moving-window
    headers_enabled=True,  # Add rate limit headers to responses
)


# Custom rate limit exceeded handler
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded errors

    Returns user-friendly error message with retry information.
    """
    logger.warning(
        f"Rate limit exceeded for {get_identifier(request)} "
        f"on {request.url.path}"
    )

    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please try again later.",
            "detail": str(exc.detail),
            "retry_after": getattr(exc, "retry_after", None),
        },
        headers={"Retry-After": str(getattr(exc, "retry_after", 60))},
    )


def setup_rate_limiting(app: FastAPI) -> None:
    """Setup rate limiting for FastAPI app

    Args:
        app: FastAPI application instance
    """
    # Check if rate limiting is enabled
    enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"

    if not enabled:
        logger.info("Rate limiting is disabled (RATE_LIMIT_ENABLED=false)")
        return

    # Add rate limiter to app state
    app.state.limiter = limiter

    # Add exception handler
    app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

    # Add middleware
    app.add_middleware(SlowAPIMiddleware)

    logger.info("Rate limiting enabled with default limit: 100/minute")


# Rate limit decorators for different endpoint types
# Usage: @limiter.limit("30/minute") above route handler

# Preset limits
LIMITS = {
    "general": "100/minute",      # General endpoints (health, status, etc.)
    "query": "30/minute",         # Search, chat, research queries
    "upload": "10/minute",        # File uploads
    "compute": "5/minute",        # Code execution, heavy operations
    "auth": "5/minute",           # Authentication endpoints (if added later)
}


def get_limit(tier: str) -> str:
    """Get rate limit string for a given tier

    Args:
        tier: One of 'general', 'query', 'upload', 'compute', 'auth'

    Returns:
        Rate limit string (e.g., "30/minute")
    """
    return LIMITS.get(tier, LIMITS["general"])
