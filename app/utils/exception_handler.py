import asyncio
import time
import functools
import inspect
import logging


def retry(max_attempts: int = 3, delay: float = 1.0, exceptions=(Exception,)):
    def decorator(func):
        module_name = inspect.getmodule(func).__name__
        logger = logging.getLogger(module_name)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            bound_args = inspect.signature(func).bind(*args, **kwargs)
            bound_args.apply_defaults()
            formatted_args = ", ".join(
                f"{k}={v!r}" for k, v in bound_args.arguments.items()
            )
            formatted_call = f"{func.__name__}({formatted_args})"

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt < max_attempts:
                        logger.warning(
                            f"{formatted_call} failed (attempt {attempt}/{max_attempts}): {e}"
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"{formatted_call} failed after {max_attempts} attempts",
                            exc_info=True,
                        )
                        raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            bound_args = inspect.signature(func).bind(*args, **kwargs)
            bound_args.apply_defaults()
            formatted_args = ", ".join(
                f"{k}={v!r}" for k, v in bound_args.arguments.items()
            )
            formatted_call = f"{func.__name__}({formatted_args})"

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt < max_attempts:
                        logger.warning(
                            f"{formatted_call} failed (attempt {attempt}/{max_attempts}): {e}"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"{formatted_call} failed after {max_attempts} attempts",
                            exc_info=True,
                        )
                        raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
