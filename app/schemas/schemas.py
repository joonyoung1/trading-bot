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
    profit_7d: float
    profit_rate_7d: float

    balance: float
    balance_delta_3m: float
    balance_rate_3m: float
    balance_delta_7d: float
    balance_rate_7d: float

    price: float
    price_delta_3m: float
    price_rate_3m: float
    price_delta_7d: float
    price_rate_7d: float

    n_trades: int

    fgi_score: float
    fgi_text: str


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


class FGIResponse(BaseModel):
    pair: str
    tradePrice: float


@dataclass
class FGI:
    score: float
    state: str

    @classmethod
    def from_response(cls, response: FGIResponse) -> "FGI":
        score = response.tradePrice

        state_ranges = {
            (0, 20): "EXTREME FEAR",
            (20, 40): "FEAR",
            (40, 60): "NEUTRAL",
            (60, 80): "GREED",
            (80, 100): "EXTREME GREED",
        }

        state = "UNKNOWN"
        for (min_score, max_score), state_name in state_ranges.items():
            if min_score <= score < max_score:
                state = state_name
                break

        return cls(score=score, state=state)
