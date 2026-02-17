"""
EduCore Backend - Rate Limiting Middleware
Redis-backed rate limiting with sliding window algorithm
"""
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any
from functools import wraps

from fastapi import Request, HTTPException, status, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings
from app.core.cache import get_redis_client

logger = logging.getLogger(__name__)


class RateLimitExceeded(HTTPException):
    """Custom exception for rate limit exceeded"""
    def __init__(
        self,
        detail: str = "Rate limit exceeded",
        retry_after: int = 60,
        limit: int = 0,
        remaining: int = 0
    ):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(int(datetime.utcnow().timestamp()) + retry_after)
            }
        )


class RateLimiter:
    """
    Redis-backed rate limiter using sliding window algorithm.

    Supports multiple rate limiting strategies:
    - Per IP address
    - Per user (authenticated)
    - Per endpoint
    - Global
    """

    def __init__(self):
        self.redis = get_redis_client()
        self.enabled = self.redis is not None

    def _get_key(self, identifier: str, window_type: str = "default") -> str:
        """Generate Redis key for rate limiting"""
        return f"edusms:ratelimit:{window_type}:{identifier}"

    async def is_allowed(
        self,
        identifier: str,
        limit: int,
        window_seconds: int = 60,
        window_type: str = "default"
    ) -> tuple[bool, int, int]:
        """
        Check if request is allowed under rate limit.

        Args:
            identifier: Unique identifier (IP, user_id, endpoint, etc.)
            limit: Maximum requests allowed in window
            window_seconds: Time window in seconds
            window_type: Type of rate limit (for key namespacing)

        Returns:
            Tuple of (is_allowed, remaining_requests, retry_after_seconds)
        """
        if not self.enabled:
            return True, limit, 0

        try:
            key = self._get_key(identifier, window_type)
            now = datetime.utcnow().timestamp()
            window_start = now - window_seconds

            pipe = self.redis.pipeline()

            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, window_start)

            # Count requests in current window
            pipe.zcard(key)

            # Add current request
            pipe.zadd(key, {str(now): now})

            # Set expiry on the key
            pipe.expire(key, window_seconds + 1)

            results = pipe.execute()
            current_count = results[1]

            if current_count >= limit:
                # Get oldest request in window to calculate retry-after
                oldest = self.redis.zrange(key, 0, 0, withscores=True)
                if oldest:
                    retry_after = int(oldest[0][1] + window_seconds - now) + 1
                else:
                    retry_after = window_seconds
                return False, 0, retry_after

            remaining = max(0, limit - current_count - 1)
            return True, remaining, 0

        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # Fail open - allow request if Redis is unavailable
            return True, limit, 0

    async def reset(self, identifier: str, window_type: str = "default") -> bool:
        """Reset rate limit for an identifier"""
        if not self.enabled:
            return False

        try:
            key = self._get_key(identifier, window_type)
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Rate limit reset error: {e}")
            return False

    async def get_status(
        self,
        identifier: str,
        limit: int,
        window_seconds: int = 60,
        window_type: str = "default"
    ) -> Dict[str, Any]:
        """Get current rate limit status"""
        if not self.enabled:
            return {
                "enabled": False,
                "limit": limit,
                "remaining": limit,
                "reset_at": None
            }

        try:
            key = self._get_key(identifier, window_type)
            now = datetime.utcnow().timestamp()
            window_start = now - window_seconds

            # Clean and count
            self.redis.zremrangebyscore(key, 0, window_start)
            current_count = self.redis.zcard(key)

            remaining = max(0, limit - current_count)
            reset_at = datetime.utcnow() + timedelta(seconds=window_seconds)

            return {
                "enabled": True,
                "limit": limit,
                "remaining": remaining,
                "current_count": current_count,
                "reset_at": reset_at.isoformat(),
                "window_seconds": window_seconds
            }

        except Exception as e:
            logger.error(f"Rate limit status error: {e}")
            return {
                "enabled": False,
                "error": str(e)
            }


# Global rate limiter instance
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for global rate limiting.
    Applies rate limits per IP address by default.
    """

    # Endpoints to skip rate limiting
    SKIP_PATHS = {
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/health",
        "/favicon.ico"
    }

    # Stricter limits for sensitive endpoints
    STRICT_ENDPOINTS = {
        "/api/v1/auth/login": (5, 60),  # 5 per minute
        "/api/v1/auth/register": (3, 60),  # 3 per minute
        "/api/v1/auth/forgot-password": (3, 60),  # 3 per minute
        "/api/v1/auth/reset-password": (3, 60),  # 3 per minute
        "/api/v1/auth/mfa/verify": (5, 60),  # 5 per minute
    }

    def __init__(
        self,
        app,
        requests_per_minute: int = 100,
        enable_user_limits: bool = True
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.enable_user_limits = enable_user_limits
        self.limiter = rate_limiter

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, handling proxies"""
        # Check for forwarded headers (reverse proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request if authenticated"""
        # This would be set by authentication middleware
        return getattr(request.state, "user_id", None)

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for excluded paths
        path = request.url.path
        if path in self.SKIP_PATHS or path.startswith("/static"):
            return await call_next(request)

        client_ip = self._get_client_ip(request)

        # Check for strict endpoint limits first
        if path in self.STRICT_ENDPOINTS:
            limit, window = self.STRICT_ENDPOINTS[path]
            allowed, remaining, retry_after = await self.limiter.is_allowed(
                f"{client_ip}:{path}",
                limit=limit,
                window_seconds=window,
                window_type="strict"
            )
            if not allowed:
                logger.warning(
                    f"Rate limit exceeded for {path} from {client_ip}"
                )
                raise RateLimitExceeded(
                    detail=f"Too many requests to {path}. Please try again later.",
                    retry_after=retry_after,
                    limit=limit,
                    remaining=0
                )

        # Global per-IP rate limit
        allowed, remaining, retry_after = await self.limiter.is_allowed(
            client_ip,
            limit=self.requests_per_minute,
            window_seconds=60,
            window_type="global"
        )

        if not allowed:
            logger.warning(f"Global rate limit exceeded for {client_ip}")
            raise RateLimitExceeded(
                detail="Too many requests. Please slow down.",
                retry_after=retry_after,
                limit=self.requests_per_minute,
                remaining=0
            )

        # Per-user rate limit (if authenticated)
        if self.enable_user_limits:
            user_id = self._get_user_id(request)
            if user_id:
                # Higher limit for authenticated users
                user_limit = self.requests_per_minute * 2
                allowed, remaining, retry_after = await self.limiter.is_allowed(
                    user_id,
                    limit=user_limit,
                    window_seconds=60,
                    window_type="user"
                )
                if not allowed:
                    logger.warning(f"User rate limit exceeded for {user_id}")
                    raise RateLimitExceeded(
                        detail="Too many requests. Please slow down.",
                        retry_after=retry_after,
                        limit=user_limit,
                        remaining=0
                    )

        # Process request and add rate limit headers
        response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response


def rate_limit(
    limit: int = 10,
    window_seconds: int = 60,
    key_func: Optional[Callable] = None,
    scope: str = "default"
):
    """
    Decorator for rate limiting specific endpoints.

    Usage:
        @router.get("/resource")
        @rate_limit(limit=5, window_seconds=60)
        async def get_resource(request: Request):
            ...

    Args:
        limit: Maximum requests allowed in window
        window_seconds: Time window in seconds
        key_func: Optional function to generate rate limit key from request
        scope: Namespace for rate limit keys
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find request in args or kwargs
            request = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if not request:
                return await func(*args, **kwargs)

            # Generate key
            if key_func:
                identifier = key_func(request)
            else:
                # Default: IP + endpoint
                ip = request.client.host if request.client else "unknown"
                identifier = f"{ip}:{request.url.path}"

            # Check rate limit
            allowed, remaining, retry_after = await rate_limiter.is_allowed(
                identifier,
                limit=limit,
                window_seconds=window_seconds,
                window_type=scope
            )

            if not allowed:
                raise RateLimitExceeded(
                    detail="Rate limit exceeded for this endpoint",
                    retry_after=retry_after,
                    limit=limit,
                    remaining=0
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator


# Pre-configured rate limit decorators
def login_rate_limit(func: Callable) -> Callable:
    """Rate limit for login endpoints: 5 attempts per minute"""
    return rate_limit(limit=5, window_seconds=60, scope="login")(func)


def api_rate_limit(func: Callable) -> Callable:
    """Standard API rate limit: 100 requests per minute"""
    return rate_limit(limit=100, window_seconds=60, scope="api")(func)


def bulk_operation_rate_limit(func: Callable) -> Callable:
    """Rate limit for bulk operations: 10 per minute"""
    return rate_limit(limit=10, window_seconds=60, scope="bulk")(func)


def export_rate_limit(func: Callable) -> Callable:
    """Rate limit for data exports: 5 per hour"""
    return rate_limit(limit=5, window_seconds=3600, scope="export")(func)
