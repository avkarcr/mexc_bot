import functools
import asyncio


def async_retry(attempts, delay=1):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for _ in range(attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    await asyncio.sleep(delay)
            raise last_exception
        return wrapper
    return decorator
