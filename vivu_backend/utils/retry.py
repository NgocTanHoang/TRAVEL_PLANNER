"""
Retry Mechanism với Exponential Backoff
Xử lý retry cho API calls và external services
"""
import logging
import time
from typing import Callable, Any, Optional, Type, Tuple
from functools import wraps

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Decorator để retry function với exponential backoff.
    
    Args:
        max_retries: Số lần retry tối đa (default: 3)
        backoff_factor: Hệ số tăng delay (default: 2.0)
        initial_delay: Delay ban đầu (giây) (default: 1.0)
        max_delay: Delay tối đa (giây) (default: 60.0)
        exceptions: Tuple các exceptions sẽ retry (default: tất cả Exception)
        on_retry: Callback được gọi trước mỗi retry (optional)
    
    Returns:
        Decorated function
    
    Example:
        @retry_with_backoff(max_retries=3, backoff_factor=2.0)
        def api_call():
            # API call logic
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        # Hết số lần retry
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries} retries: {e}",
                            exc_info=True
                        )
                        raise
                    
                    # Call on_retry callback nếu có
                    if on_retry:
                        try:
                            on_retry(attempt + 1, e, delay)
                        except Exception:
                            pass
                    
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    time.sleep(delay)
                    
                    # Tính delay cho lần retry tiếp theo (exponential backoff)
                    delay = min(delay * backoff_factor, max_delay)
            
            # Nếu đến đây thì có vấn đề
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


def retry_async_with_backoff(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Decorator để retry async function với exponential backoff.
    
    Args:
        max_retries: Số lần retry tối đa (default: 3)
        backoff_factor: Hệ số tăng delay (default: 2.0)
        initial_delay: Delay ban đầu (giây) (default: 1.0)
        max_delay: Delay tối đa (giây) (default: 60.0)
        exceptions: Tuple các exceptions sẽ retry (default: tất cả Exception)
        on_retry: Callback được gọi trước mỗi retry (optional)
    
    Returns:
        Decorated async function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            import asyncio
            
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        # Hết số lần retry
                        logger.error(
                            f"Async function {func.__name__} failed after {max_retries} retries: {e}",
                            exc_info=True
                        )
                        raise
                    
                    # Call on_retry callback nếu có
                    if on_retry:
                        try:
                            on_retry(attempt + 1, e, delay)
                        except Exception:
                            pass
                    
                    logger.warning(
                        f"Async function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    await asyncio.sleep(delay)
                    
                    # Tính delay cho lần retry tiếp theo (exponential backoff)
                    delay = min(delay * backoff_factor, max_delay)
            
            # Nếu đến đây thì có vấn đề
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


class RetryConfig:
    """Configuration cho retry mechanism"""
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BACKOFF_FACTOR = 2.0
    DEFAULT_INITIAL_DELAY = 1.0
    DEFAULT_MAX_DELAY = 60.0
    
    # Retry configs cho các loại services khác nhau
    API_RETRY = {
        'max_retries': 3,
        'backoff_factor': 2.0,
        'initial_delay': 1.0,
        'max_delay': 30.0
    }
    
    LLM_RETRY = {
        'max_retries': 2,
        'backoff_factor': 2.0,
        'initial_delay': 2.0,
        'max_delay': 60.0
    }
    
    DATABASE_RETRY = {
        'max_retries': 5,
        'backoff_factor': 1.5,
        'initial_delay': 0.5,
        'max_delay': 10.0
    }
    
    VECTOR_DB_RETRY = {
        'max_retries': 3,
        'backoff_factor': 2.0,
        'initial_delay': 1.0,
        'max_delay': 20.0
    }

