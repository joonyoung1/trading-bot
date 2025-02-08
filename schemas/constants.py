from enum import Enum


class ConfigKeys(str, Enum):
    LOG_DIR: str = "LOG_DIR"
    DATA_DIR: str = "DATA_DIR"
    TOKEN: str = "TOKEN"
    CHAT_ID: str = "CHAT_ID"
    ACCESS: str = "ACCESS"
    SECRET: str = "SECRET"
    TICKER: str = "TICKER"
    PIVOT: str = "PIVOT"


class Cols(str, Enum):
    TS: str = "timestamp"
    BAL: str = "balance"
    P: str = "price"
    R: str = "ratio"