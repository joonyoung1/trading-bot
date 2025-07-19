import os


def _get_required_env(key: str) -> str:
    value = os.getenv(key)
    if value is None:
        raise KeyError(f"Required environment variable '{key}' is not set.")
    return value


class Env:
    # path
    LOG_DIR = os.getenv("LOG_DIR", "log")
    DATA_DIR = os.getenv("DATA_DIR", "data")

    # telegram
    TOKEN = _get_required_env("TOKEN")

    # upbit
    ACCESS = _get_required_env("ACCESS")
    SECRET = _get_required_env("SECRET")

    # trading
    TICKER = _get_required_env("TICKER")
    CURRENCY = TICKER.split("-")[1]
    PIVOT = float(_get_required_env("PIVOT"))
