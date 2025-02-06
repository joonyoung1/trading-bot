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
class Profit:
    profit: float
    profit_rate: float


@dataclass
class Balance:
    balance: float
    balance_rate: float
    price: float
    price_rate: float
    cash: float
    cash_rate: float
    value: float
    value_rate: float
    quantity: float
    quantity_rate: float


@dataclass
class Status(Profit, Balance):
    n_trades: int


@dataclass
class Dashboard:
    status: Status
    trend: "BytesIO"
