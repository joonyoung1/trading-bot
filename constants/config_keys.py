from enum import StrEnum


class ConfigKeys(StrEnum):
    LOG_DIR = "LOG_DIR"
    DATA_DIR = "DATA_DIR"
    TOKEN = "TOKEN"
    CHAT_ID = "CHAT_ID"
    ACCESS = "ACCESS"
    SECRET = "SECRET"
    TICKER = "TICKER"
    PIVOT = "PIVOT"


class Cols(StrEnum):
    TS = "timestamp"
    BAL = "balance"
    P = "price"
    R = "ratio"
