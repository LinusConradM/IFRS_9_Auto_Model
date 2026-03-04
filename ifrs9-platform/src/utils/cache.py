"""Redis cache utilities"""
import redis
import json
import os
from typing import Any, Optional
from datetime import timedelta

# Redis connection
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)


def get_cache(key: str) -> Optional[Any]:
    """
    Get value from cache.
    
    Args:
        key: Cache key
        
    Returns:
        Cached value or None if not found
    """
    try:
        value = redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        print(f"Cache get error: {e}")
        return None


def set_cache(key: str, value: Any, expire: Optional[int] = None) -> bool:
    """
    Set value in cache.
    
    Args:
        key: Cache key
        value: Value to cache
        expire: Expiration time in seconds (optional)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        serialized = json.dumps(value, default=str)
        if expire:
            redis_client.setex(key, expire, serialized)
        else:
            redis_client.set(key, serialized)
        return True
    except Exception as e:
        print(f"Cache set error: {e}")
        return False


def delete_cache(key: str) -> bool:
    """
    Delete value from cache.
    
    Args:
        key: Cache key
        
    Returns:
        True if successful, False otherwise
    """
    try:
        redis_client.delete(key)
        return True
    except Exception as e:
        print(f"Cache delete error: {e}")
        return False


def clear_cache_pattern(pattern: str) -> int:
    """
    Delete all keys matching pattern.
    
    Args:
        pattern: Key pattern (e.g., "parameter:*")
        
    Returns:
        Number of keys deleted
    """
    try:
        keys = redis_client.keys(pattern)
        if keys:
            return redis_client.delete(*keys)
        return 0
    except Exception as e:
        print(f"Cache clear error: {e}")
        return 0
