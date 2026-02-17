"""
EduCore Backend - Redis Cache Utilities
Caching layer for improved performance
"""
import json
import logging
from typing import Any, Optional, Callable, TypeVar, Union
from functools import wraps
from datetime import timedelta
import hashlib

try:
    import redis
    from redis import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    Redis = None

from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar('T')

# Global Redis client
_redis_client: Optional[Redis] = None


def get_redis_client() -> Optional[Redis]:
    """Get or create Redis client singleton"""
    global _redis_client

    if not REDIS_AVAILABLE:
        logger.warning("Redis package not installed. Caching disabled.")
        return None

    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD,
                ssl=settings.REDIS_SSL,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
            )
            # Test connection
            _redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Caching disabled.")
            _redis_client = None

    return _redis_client


class CacheManager:
    """Redis cache manager with helper methods"""

    def __init__(self):
        self.client = get_redis_client()
        self.enabled = self.client is not None

    def _make_key(self, namespace: str, key: str) -> str:
        """Create a namespaced cache key"""
        return f"edusms:{namespace}:{key}"

    def get(self, namespace: str, key: str) -> Optional[Any]:
        """
        Get a value from cache

        Args:
            namespace: Cache namespace (e.g., 'dashboard', 'user')
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self.enabled:
            return None

        try:
            cache_key = self._make_key(namespace, key)
            value = self.client.get(cache_key)

            if value is not None:
                return json.loads(value)
            return None

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set a value in cache

        Args:
            namespace: Cache namespace
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time to live in seconds (default from settings)

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            cache_key = self._make_key(namespace, key)
            ttl = ttl or settings.CACHE_DEFAULT_TTL

            self.client.setex(
                cache_key,
                ttl,
                json.dumps(value, default=str),
            )
            return True

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, namespace: str, key: str) -> bool:
        """Delete a key from cache"""
        if not self.enabled:
            return False

        try:
            cache_key = self._make_key(namespace, key)
            self.client.delete(cache_key)
            return True

        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern

        Args:
            pattern: Redis pattern (e.g., 'edusms:dashboard:*')

        Returns:
            Number of keys deleted
        """
        if not self.enabled:
            return 0

        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0

        except Exception as e:
            logger.error(f"Cache delete pattern error: {e}")
            return 0

    def invalidate_school(self, school_id: str) -> int:
        """Invalidate all cache for a school"""
        return self.delete_pattern(f"edusms:*:{school_id}:*")

    def invalidate_user(self, user_id: str) -> int:
        """Invalidate all cache for a user"""
        return self.delete_pattern(f"edusms:user:{user_id}:*")

    def invalidate_dashboard(self, school_id: str) -> int:
        """Invalidate dashboard cache for a school"""
        return self.delete_pattern(f"edusms:dashboard:{school_id}:*")

    def get_or_set(
        self,
        namespace: str,
        key: str,
        factory: Callable[[], T],
        ttl: Optional[int] = None,
    ) -> T:
        """
        Get value from cache or compute and cache it

        Args:
            namespace: Cache namespace
            key: Cache key
            factory: Function to compute value if not cached
            ttl: Time to live in seconds

        Returns:
            Cached or computed value
        """
        cached = self.get(namespace, key)
        if cached is not None:
            return cached

        value = factory()
        self.set(namespace, key, value, ttl)
        return value

    def increment(self, namespace: str, key: str, amount: int = 1) -> int:
        """Increment a counter"""
        if not self.enabled:
            return 0

        try:
            cache_key = self._make_key(namespace, key)
            return self.client.incr(cache_key, amount)
        except Exception as e:
            logger.error(f"Cache increment error: {e}")
            return 0

    def decrement(self, namespace: str, key: str, amount: int = 1) -> int:
        """Decrement a counter"""
        if not self.enabled:
            return 0

        try:
            cache_key = self._make_key(namespace, key)
            return self.client.decr(cache_key, amount)
        except Exception as e:
            logger.error(f"Cache decrement error: {e}")
            return 0


# Global cache manager instance
cache = CacheManager()


def cached(
    namespace: str,
    key_builder: Optional[Callable[..., str]] = None,
    ttl: Optional[int] = None,
):
    """
    Decorator for caching function results

    Args:
        namespace: Cache namespace
        key_builder: Function to build cache key from function args
        ttl: Time to live in seconds

    Example:
        @cached("dashboard", lambda school_id: f"{school_id}:summary", ttl=60)
        async def get_dashboard_summary(school_id: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default: hash all args
                key_data = json.dumps({"args": args, "kwargs": kwargs}, default=str)
                cache_key = hashlib.md5(key_data.encode()).hexdigest()

            # Try to get from cache
            cached_value = cache.get(namespace, cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            cache.set(namespace, cache_key, result, ttl)

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                key_data = json.dumps({"args": args, "kwargs": kwargs}, default=str)
                cache_key = hashlib.md5(key_data.encode()).hexdigest()

            # Try to get from cache
            cached_value = cache.get(namespace, cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = func(*args, **kwargs)

            # Cache result
            cache.set(namespace, cache_key, result, ttl)

            return result

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# Cache key builders
class CacheKeys:
    """Common cache key patterns"""

    @staticmethod
    def dashboard_summary(school_id: str, date_range: str) -> str:
        return f"{school_id}:summary:{date_range}"

    @staticmethod
    def user_profile(user_id: str) -> str:
        return f"{user_id}:profile"

    @staticmethod
    def user_permissions(user_id: str) -> str:
        return f"{user_id}:permissions"

    @staticmethod
    def school_settings(school_id: str) -> str:
        return f"{school_id}:settings"

    @staticmethod
    def student_summary(student_id: str) -> str:
        return f"{student_id}:summary"

    @staticmethod
    def class_roster(class_id: str) -> str:
        return f"{class_id}:roster"

    @staticmethod
    def fee_summary(school_id: str, term_id: str) -> str:
        return f"{school_id}:{term_id}:fees"

    @staticmethod
    def attendance_today(school_id: str, date: str) -> str:
        return f"{school_id}:attendance:{date}"
