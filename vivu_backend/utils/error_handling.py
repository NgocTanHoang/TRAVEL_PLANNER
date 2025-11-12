"""
Error Handling Utilities với Retry Logic
=========================================
Cung cấp retry logic, error classification và circuit breaker cho agents.
"""
import logging
import time
import asyncio
from typing import Callable, Any, Optional, Type, Tuple
from functools import wraps
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Error classification"""
    RETRYABLE = "retryable"  # Có thể retry (network, timeout, etc.)
    NON_RETRYABLE = "non_retryable"  # Không nên retry (validation, auth, etc.)
    CRITICAL = "critical"  # Lỗi nghiêm trọng, dừng ngay


class RetryConfig:
    """Configuration for retry logic"""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_exceptions = retryable_exceptions or (
            ConnectionError,
            TimeoutError,
            OSError,
        )


def classify_error(error: Exception) -> ErrorType:
    """
    Classify error type để quyết định có retry hay không.
    
    Args:
        error: Exception to classify
        
    Returns:
        ErrorType
    """
    error_str = str(error).lower()
    error_type = type(error).__name__
    
    # Retryable errors
    retryable_keywords = [
        'connection', 'timeout', 'network', 'temporary', 'retry',
        'rate limit', 'too many requests', 'service unavailable',
        'gateway', 'bad gateway', 'internal server error'
    ]
    
    if any(keyword in error_str for keyword in retryable_keywords):
        return ErrorType.RETRYABLE
    
    # Non-retryable errors
    non_retryable_keywords = [
        'validation', 'invalid', 'authentication', 'authorization',
        'not found', 'forbidden', 'bad request', 'syntax error'
    ]
    
    if any(keyword in error_str for keyword in non_retryable_keywords):
        return ErrorType.NON_RETRYABLE
    
    # Check exception type
    if isinstance(error, (ConnectionError, TimeoutError, OSError)):
        return ErrorType.RETRYABLE
    
    if isinstance(error, (ValueError, TypeError, KeyError)):
        return ErrorType.NON_RETRYABLE
    
    # Default: non-retryable for safety
    return ErrorType.NON_RETRYABLE


def retry_with_backoff(
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    Decorator để retry function với exponential backoff.
    
    Args:
        config: RetryConfig
        on_retry: Callback khi retry (optional)
        
    Returns:
        Decorated function
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_type = classify_error(e)
                    
                    # Không retry nếu không phải retryable error
                    if error_type != ErrorType.RETRYABLE:
                        logger.error(f"Non-retryable error in {func.__name__}: {e}")
                        raise
                    
                    # Dừng nếu đã hết retries
                    if attempt >= config.max_retries:
                        logger.error(
                            f"Max retries ({config.max_retries}) exceeded for {func.__name__}: {e}"
                        )
                        raise
                    
                    # Tính delay với exponential backoff
                    delay = min(
                        config.initial_delay * (config.exponential_base ** attempt),
                        config.max_delay
                    )
                    
                    logger.warning(
                        f"Retry {attempt + 1}/{config.max_retries} for {func.__name__} "
                        f"after {delay:.2f}s: {e}"
                    )
                    
                    if on_retry:
                        on_retry(e, attempt + 1)
                    
                    await asyncio.sleep(delay)
            
            # Should not reach here, but just in case
            if last_exception:
                raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_type = classify_error(e)
                    
                    # Không retry nếu không phải retryable error
                    if error_type != ErrorType.RETRYABLE:
                        logger.error(f"Non-retryable error in {func.__name__}: {e}")
                        raise
                    
                    # Dừng nếu đã hết retries
                    if attempt >= config.max_retries:
                        logger.error(
                            f"Max retries ({config.max_retries}) exceeded for {func.__name__}: {e}"
                        )
                        raise
                    
                    # Tính delay với exponential backoff
                    delay = min(
                        config.initial_delay * (config.exponential_base ** attempt),
                        config.max_delay
                    )
                    
                    logger.warning(
                        f"Retry {attempt + 1}/{config.max_retries} for {func.__name__} "
                        f"after {delay:.2f}s: {e}"
                    )
                    
                    if on_retry:
                        on_retry(e, attempt + 1)
                    
                    time.sleep(delay)
            
            # Should not reach here, but just in case
            if last_exception:
                raise last_exception
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class CircuitBreaker:
    """
    Simple circuit breaker pattern để tránh overload hệ thống.
    """
    
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half_open
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function với circuit breaker"""
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half_open"
                logger.info("Circuit breaker transitioning to half-open")
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            if self.state == "half_open":
                self.state = "closed"
                self.failure_count = 0
                logger.info("Circuit breaker closed after successful call")
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.error(f"Circuit breaker OPEN after {self.failure_count} failures")
            
            raise

