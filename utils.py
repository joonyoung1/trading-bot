from decimal import Decimal
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
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt < max_attempts:
                        logger.warning(
                            f"{func.__name__} filed (attempt {attempt}/{max_attempts}): {e}"
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts"
                        )
                        raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt < max_attempts:
                        logger.warning(
                            f"{func.__name__} filed (attempt {attempt}/{max_attempts}): {e}"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts"
                        )
                        raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def get_price_step(current_price: float) -> float:
    if current_price >= 2_000_000:
        return 1_000
    elif current_price >= 1_000_000:
        return 500
    elif current_price >= 500_000:
        return 100
    elif current_price >= 100_000:
        return 50
    elif current_price >= 10_000:
        return 10
    elif current_price >= 1_000:
        return 1
    elif current_price >= 100:
        return 0.1
    elif current_price >= 10:
        return 0.01
    elif current_price >= 1:
        return 0.001
    elif current_price >= 0.1:
        return 0.0001
    elif current_price >= 0.01:
        return 0.00001
    elif current_price >= 0.001:
        return 0.000001
    elif current_price >= 0.0001:
        return 0.0000001
    else:
        return 0.00000001


def get_upper_price(price: float) -> float:
    step = get_price_step(price)
    return precise_addition(price, step)


def get_lower_price(price: float) -> float:
    step = get_price_step(price - 1e-6)
    return precise_substraction(price, step)


def precise_addition(a: float, b: float) -> float:
    return float(Decimal(str(a)) + Decimal(str(b)))


def precise_substraction(a: float, b: float) -> float:
    return float(Decimal(str(a)) - Decimal(str(b)))
