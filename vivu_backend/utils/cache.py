"""
Cache Utilities
================
Redis cache wrapper with in-memory fallback for caching API results and other frequently accessed data.
Supports Redis for production and in-memory cache for development.
"""
import os
import json
import hashlib
import logging
from typing import Any, Optional, Dict
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Try to import redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory cache fallback")

# In-memory cache fallback (thread-safe dict)
_in_memory_cache: Dict[str, Dict[str, Any]] = {}
_in_memory_cache_lock = None

try:
    import threading
    _in_memory_cache_lock = threading.Lock()
except ImportError:
    pass


# Global redis client
_redis_client = None


def get_redis_client():
    """Get or create Redis client."""
    global _redis_client
    
    if not REDIS_AVAILABLE:
        return None
    
    if _redis_client is None:
        try:
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            redis_db = int(os.getenv('REDIS_DB', 0))
            redis_password = os.getenv('REDIS_PASSWORD', None)
            
            _redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            _redis_client.ping()
            logger.info(f"Redis connected: {redis_host}:{redis_port}")
        
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}, using in-memory cache")
            _redis_client = None
    
    return _redis_client


def cache_get(key: str) -> Optional[Any]:
    """
    Get value from cache (Redis or in-memory).
    
    Args:
        key: Cache key
    
    Returns:
        Cached value or None
    """
    # Try Redis first
    client = get_redis_client()
    if client:
        try:
            value = client.get(key)
            if value:
                logger.debug(f"Cache hit (Redis): {key[:50]}")
                return json.loads(value)
        except Exception as e:
            logger.warning(f"Redis cache get error: {e}")
    
    # Fallback to in-memory cache
    if _in_memory_cache_lock:
        with _in_memory_cache_lock:
            cached_data = _in_memory_cache.get(key)
    else:
        cached_data = _in_memory_cache.get(key)
    
    if cached_data:
        # Check expiration
        expires_at = cached_data.get('expires_at')
        if expires_at and datetime.now() > expires_at:
            # Expired, remove it
            if _in_memory_cache_lock:
                with _in_memory_cache_lock:
                    _in_memory_cache.pop(key, None)
            else:
                _in_memory_cache.pop(key, None)
            return None
        
        logger.debug(f"Cache hit (in-memory): {key[:50]}")
        return cached_data.get('value')
    
    return None


def _serialize_for_cache(value: Any) -> Any:
    """
    Recursively serialize value for JSON caching.
    Converts datetime objects to ISO format strings.
    
    Args:
        value: Value to serialize
        
    Returns:
        JSON-serializable value
    """
    if isinstance(value, datetime):
        return value.isoformat()
    elif isinstance(value, dict):
        return {k: _serialize_for_cache(v) for k, v in value.items()}
    elif isinstance(value, (list, tuple)):
        return [_serialize_for_cache(item) for item in value]
    elif isinstance(value, set):
        return [_serialize_for_cache(item) for item in value]
    else:
        # Try to serialize, if it fails, convert to string
        try:
            json.dumps(value)
            return value
        except (TypeError, ValueError):
            # If not JSON serializable, convert to string
            return str(value)


def cache_set(key: str, value: Any, ttl: int = 3600) -> bool:
    """
    Set value in cache (Redis or in-memory).
    
    Args:
        key: Cache key
        value: Value to cache (will be serialized, datetime objects converted to ISO strings)
        ttl: Time to live in seconds (default: 1 hour)
    
    Returns:
        True if successful, False otherwise
    """
    # Try Redis first
    client = get_redis_client()
    if client:
        try:
            # Serialize value, converting datetime objects to strings
            serialized_value = _serialize_for_cache(value)
            value_str = json.dumps(serialized_value, ensure_ascii=False, default=str)
            client.setex(key, ttl, value_str)
            logger.debug(f"Cache set (Redis): {key[:50]}, TTL: {ttl}s")
            return True
        except Exception as e:
            logger.warning(f"Redis cache set error: {e}")
    
    # Fallback to in-memory cache
    try:
        expires_at = datetime.now() + timedelta(seconds=ttl)
        cached_data = {
            'value': value,
            'expires_at': expires_at,
            'created_at': datetime.now()
        }
        
        if _in_memory_cache_lock:
            with _in_memory_cache_lock:
                _in_memory_cache[key] = cached_data
        else:
            _in_memory_cache[key] = cached_data
        
        # Clean up old entries if cache is too large (>10000 entries)
        if len(_in_memory_cache) > 10000:
            _cleanup_in_memory_cache()
        
        logger.debug(f"Cache set (in-memory): {key[:50]}, TTL: {ttl}s")
        return True
    except Exception as e:
        logger.warning(f"In-memory cache set error: {e}")
        return False


def _cleanup_in_memory_cache():
    """Clean up expired entries from in-memory cache."""
    now = datetime.now()
    expired_keys = []
    
    if _in_memory_cache_lock:
        with _in_memory_cache_lock:
            for key, cached_data in _in_memory_cache.items():
                expires_at = cached_data.get('expires_at')
                if expires_at and now > expires_at:
                    expired_keys.append(key)
            
            for key in expired_keys:
                _in_memory_cache.pop(key, None)
    else:
        for key, cached_data in _in_memory_cache.items():
            expires_at = cached_data.get('expires_at')
            if expires_at and now > expires_at:
                expired_keys.append(key)
        
        for key in expired_keys:
            _in_memory_cache.pop(key, None)
    
    if expired_keys:
        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")


def cache_delete(key: str) -> bool:
    """
    Delete key from cache.
    
    Args:
        key: Cache key
    
    Returns:
        True if successful, False otherwise
    """
    # Try Redis first
    client = get_redis_client()
    if client:
        try:
            client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis cache delete error: {e}")
    
    # Fallback to in-memory cache
    if _in_memory_cache_lock:
        with _in_memory_cache_lock:
            _in_memory_cache.pop(key, None)
    else:
        _in_memory_cache.pop(key, None)
    
    return True


def cache_clear_pattern(pattern: str) -> int:
    """
    Clear all keys matching pattern.
    
    Args:
        pattern: Redis pattern (e.g., "rag_retrieve:*")
    
    Returns:
        Number of keys deleted
    """
    deleted_count = 0
    
    # Try Redis first
    client = get_redis_client()
    if client:
        try:
            keys = client.keys(pattern)
            if keys:
                deleted_count = client.delete(*keys)
        except Exception as e:
            logger.warning(f"Redis cache clear pattern error: {e}")
    
    # Also clear in-memory cache (simple pattern matching)
    if '*' in pattern:
        prefix = pattern.replace('*', '')
        keys_to_delete = []
        
        if _in_memory_cache_lock:
            with _in_memory_cache_lock:
                for key in _in_memory_cache.keys():
                    if key.startswith(prefix):
                        keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    _in_memory_cache.pop(key, None)
        else:
            for key in _in_memory_cache.keys():
                if key.startswith(prefix):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                _in_memory_cache.pop(key, None)
        
        deleted_count += len(keys_to_delete)
    
    return deleted_count


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate cache key from prefix and arguments.
    
    Args:
        prefix: Key prefix
        *args: Positional arguments
        **kwargs: Keyword arguments
    
    Returns:
        Cache key string
    """
    # Create hash from arguments
    key_parts = [prefix]
    if args:
        key_parts.extend(str(arg) for arg in args)
    if kwargs:
        sorted_kwargs = sorted(kwargs.items())
        key_parts.extend(f"{k}={v}" for k, v in sorted_kwargs)
    
    key_str = ":".join(key_parts)
    
    # Create hash if key is too long
    if len(key_str) > 200:
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    return key_str


def cached(ttl: int = 3600, key_prefix: Optional[str] = None):
    """
    Decorator for caching function results.
    
    Args:
        ttl: Time to live in seconds (default: 1 hour)
        key_prefix: Prefix for cache key (default: function name)
    
    Usage:
        @cached(ttl=7200, key_prefix='geocode')
        def geocode_address(address):
            ...
    """
    def decorator(func):
        prefix = key_prefix or func.__name__
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = generate_cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache_get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}: {cache_key[:50]}")
                return cached_result
            
            # Call function and cache result
            result = func(*args, **kwargs)
            
            # Cache result (only if result is not None)
            if result is not None:
                cache_set(cache_key, result, ttl=ttl)
                logger.debug(f"Cached result for {func.__name__}: {cache_key[:50]}")
            
            return result
        
        return wrapper
    return decorator


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    stats = {
        'redis_available': REDIS_AVAILABLE,
        'redis_connected': get_redis_client() is not None,
        'in_memory_size': len(_in_memory_cache)
    }
    
    # Try to get Redis stats
    client = get_redis_client()
    if client:
        try:
            info = client.info()
            stats['redis_used_memory'] = info.get('used_memory_human', 'N/A')
            stats['redis_keys'] = client.dbsize()
        except Exception:
            pass
    
    return stats
