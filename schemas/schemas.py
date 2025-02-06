from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from io import BytesIO


@dataclass(frozen=True)
class ConfigKeys:
    LOG_DIR: str = "LOG_DIR"
    DATA_DIR: str = "DATA_DIR"

    TOKEN: str = "TOKEN"
    CHAT_ID: str = "CHAT_ID"

    ACCESS: str = "ACCESS"
    SECRET: str = "SECRET"
    TICKER: str = "TICKER"

    PIVOT: str = "PIVOT"


@dataclass(frozen=True)
class Cols:
    TS: str = "timestamp"
    BAL: str = "balance"
    P: str = "price"
    R: str = "ratio"


@dataclass
class Status:
    profit_3m: float
    profit_rate_3m: float
    profit_24h: float
    profit_rate_24h: float

    balance: float
    balance_delta_3m: float
    balance_rate_3m: float
    balance_delta_24h: float
    balance_rate_24h: float

    price: float
    price_delta_3m: float
    price_rate_3m: float
    price_delta_24h: float
    price_rate_24h: float


@dataclass
class Dashboard:
    trend: "BytesIO"
    status: Status
