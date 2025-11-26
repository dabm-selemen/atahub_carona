"""
Retry Utilities

Decorators and functions for retry logic with exponential backoff.
"""

import asyncio
import functools
import random
from typing import Callable, Type, Tuple
import structlog

logger = structlog.get_logger(__name__)


class RetryableError(Exception):
    """Exception that should trigger retry"""
    pass


def retry_with_backoff(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    retry_on: Tuple[Type[Exception], ...] = (RetryableError, asyncio.TimeoutError),
    logger_name: str = "retry"
):
    """
    Decorator for async functions with exponential backoff retry

    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Exponential backoff multiplier (wait = backoff_factor ** attempt)
        retry_on: Tuple of exception types to retry on
        logger_name: Logger name for logging

    Usage:
        @retry_with_backoff(max_retries=3, backoff_factor=2.0)
        async def my_function():
            # function code
            pass

    Example:
        @retry_with_backoff(max_retries=5)
        async def fetch_data(url):
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return await response.json()
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            func_logger = structlog.get_logger(logger_name)

            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)

                except retry_on as e:
                    if attempt == max_retries - 1:
                        func_logger.error(
                            "retry_exhausted",
                            function=func.__name__,
                            max_retries=max_retries,
                            error=str(e)
                        )
                        raise

                    # Calculate wait time with jitter
                    wait = (backoff_factor ** attempt) * random.uniform(0.5, 1.5)

                    func_logger.warning(
                        "retry_attempt",
                        function=func.__name__,
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        wait_seconds=f"{wait:.2f}",
                        error=str(e)
                    )

                    await asyncio.sleep(wait)

                except Exception as e:
                    func_logger.error(
                        "non_retryable_error",
                        function=func.__name__,
                        error=str(e),
                        error_type=type(e).__name__
                    )
                    raise

        return wrapper
    return decorator


def retry_sync(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    retry_on: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator for synchronous functions with exponential backoff retry

    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Exponential backoff multiplier
        retry_on: Tuple of exception types to retry on

    Usage:
        @retry_sync(max_retries=3)
        def my_function():
            # function code
            pass
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)

                except retry_on as e:
                    if attempt == max_retries - 1:
                        logger.error(
                            "retry_exhausted_sync",
                            function=func.__name__,
                            max_retries=max_retries,
                            error=str(e)
                        )
                        raise

                    wait = (backoff_factor ** attempt) * random.uniform(0.5, 1.5)

                    logger.warning(
                        "retry_attempt_sync",
                        function=func.__name__,
                        attempt=attempt + 1,
                        wait_seconds=f"{wait:.2f}"
                    )

                    time.sleep(wait)

        return wrapper
    return decorator


async def retry_operation(
    operation: Callable,
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    *args,
    **kwargs
):
    """
    Retry an async operation with exponential backoff

    Functional approach (without decorator)

    Args:
        operation: Async function to retry
        max_retries: Maximum retry attempts
        backoff_factor: Backoff multiplier
        *args: Arguments for operation
        **kwargs: Keyword arguments for operation

    Returns:
        Operation result

    Usage:
        result = await retry_operation(
            fetch_data,
            max_retries=5,
            url="https://example.com"
        )
    """
    for attempt in range(max_retries):
        try:
            return await operation(*args, **kwargs)

        except Exception as e:
            if attempt == max_retries - 1:
                raise

            wait = (backoff_factor ** attempt) * random.uniform(0.5, 1.5)

            logger.warning(
                "retry_operation_attempt",
                operation=operation.__name__,
                attempt=attempt + 1,
                wait_seconds=f"{wait:.2f}",
                error=str(e)
            )

            await asyncio.sleep(wait)


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Test retry decorator
    async def test():
        attempt_count = 0

        @retry_with_backoff(max_retries=3, backoff_factor=1.5)
        async def flaky_function():
            nonlocal attempt_count
            attempt_count += 1

            print(f"Attempt {attempt_count}")

            if attempt_count < 3:
                raise RetryableError("Simulated failure")

            return "Success!"

        result = await flaky_function()
        print(f"Result: {result}")
        print(f"Total attempts: {attempt_count}")

    asyncio.run(test())
