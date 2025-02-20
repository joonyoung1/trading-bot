import os


class Env:
    # path
    LOG_DIR = os.getenv("LOG_DIR", "log")
    DATA_DIR = os.getenv("DATA_DIR", "data")

    # telegram
    TOKEN = os.getenv("TOKEN")

    # upbit
    ACCESS = os.getenv("ACCESS")
    SECRET = os.getenv("SECRET")

    # trading
    TICKER = os.getenv("TICKER")
    CURRENCY = TICKER.split("-")[1]
    PIVOT = float(os.getenv("PIVOT"))
