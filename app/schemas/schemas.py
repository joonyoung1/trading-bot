from dataclasses import dataclass
from datetime import datetime
from pydantic import BaseModel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from io import BytesIO


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

    n_trades: int


@dataclass
class Dashboard:
    trend: "BytesIO"
    status: Status


class Balance(BaseModel):
    currency: str
    balance: float
    locked: float
    avg_buy_price: float
    avg_buy_price_modified: bool
    unit_currency: str

    class Config:
        extra = "ignore"


class Order(BaseModel):
    uuid: str
    side: str
    ord_type: str
    price: float | None = None
    state: str
    market: str
    created_at: datetime
    volume: float | None = None
    remaining_volume: float | None = None
    reserved_fee: float
    remaining_fee: float
    paid_fee: float
    locked: float
    executed_volume: float
    trades_count: int

    class Config:
        extra = "ignore"


class Candle(BaseModel):
    market: str
    candle_date_time_utc: str
    candle_date_time_kst: str
    opening_price: float
    high_price: float
    low_price: float
    trade_price: float
    timestamp: int
    candle_acc_trade_price: float
    candle_acc_trade_volume: float
    unit: int | None = None