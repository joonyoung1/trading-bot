from io import BytesIO
from typing import TYPE_CHECKING
from dataclasses import dataclass

import numpy as np
from scipy.integrate import quad
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

from config import config
from utils import calc_ratio

matplotlib.use("Agg")

if TYPE_CHECKING:
    from broker import Broker
    from tracker import Tracker


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
    trend: BytesIO


class DataProcessor:
    def __init__(self, broker: "Broker", tracker: "Tracker") -> None:
        self.broker = broker
        self.tracker = tracker

    async def process(self) -> Dashboard:
        histories = await self.tracker.get_recent_histories()
        estimated_profit = self.estimate_balance_at_past_price(histories)
        balance = await self.get_balance_status(histories)
        n_trades = self.count_recent_trades(histories)

        histories = self.adaptive_sampling(histories)
        trend_plot = self.generate_trend_plot(histories)

        status = Status(**vars(estimated_profit), **vars(balance), n_trades=n_trades)
        return Dashboard(trend=trend_plot, status=status)

    def estimate_balance_at_past_price(self, histories: pd.DataFrame) -> Profit:
        target_price = histories.iloc[0]["price"]
        origin_balance = histories.iloc[0]["value"]
        current_price = histories.iloc[-1]["price"]
        current_balance = histories.iloc[-1]["value"]

        pivot_price = config.get("PIVOT")

        def integrand(price: float):
            ratio = calc_ratio(price, pivot_price)
            return (1 - ratio) / price

        integral, _ = quad(integrand, current_price, target_price)
        estimated_balance = current_balance * np.exp(integral)
        profit = estimated_balance - origin_balance

        return Profit(
            profit=profit,
            profit_rate=(profit / origin_balance) * 100,
        )

    async def get_balance_status(self, histories: pd.DataFrame) -> Balance:
        balances = await self.broker.get_balances()
        if balances[0]["currency"] == "KRW":
            cash_info, coin_info = balances[0], balances[1]
        else:
            cash_info, coin_info = balances[1], balances[0]

        price = await self.broker.get_current_price(f"KRW-{coin_info['currency']}")
        quantity = float(coin_info["balance"]) + float(coin_info["locked"])
        value = price * quantity
        cash = float(cash_info["balance"]) + float(cash_info["locked"])
        balance = cash + value

        oldest = histories.iloc[0]
        _balance = oldest["value"]
        _price = oldest["price"]
        _cash = _balance * oldest["ratio"]
        _value = _balance - _cash
        _quantity = _value / _price

        return Balance(
            balance=balance,
            balance_rate=(balance / _balance - 1) * 100,
            price=price,
            price_rate=(price / _price - 1) * 100,
            cash=cash,
            cash_rate=(cash / _cash - 1) * 100,
            value=value,
            value_rate=(value / _value - 1) * 100,
            quantity=quantity,
            quantity_rate=(quantity / _quantity - 1) * 100,
        )

    def count_recent_trades(self, histories: pd.DataFrame) -> int:
        latest = histories["timestamp"].iloc[-1]
        cutoff = latest - pd.Timedelta(hours=24)
        start_idx = histories["timestamp"].searchsorted(cutoff, side="left")
        return len(histories) - start_idx

    def adaptive_sampling(self, histories: pd.DataFrame) -> pd.DataFrame:
        unit = (
            (histories["timestamp"].iloc[-1] - histories["timestamp"].iloc[0]) / 240
        ).astype("int64")
        ts = histories["timestamp"].astype("int64").to_numpy()

        min_vals = np.empty(len(histories))
        max_vals = np.empty(len(histories))

        start_idx = 0
        end_idx = 0
        for i in range(len(histories)):
            while ts[i] - ts[start_idx] > unit:
                start_idx += 1
            while end_idx < len(histories) and ts[end_idx] - ts[i] < unit:
                end_idx += 1

            window = histories["price"].iloc[start_idx:end_idx]
            min_vals[i] = window.min()
            max_vals[i] = window.max()

        prices = histories["price"].to_numpy()
        is_extreme = (prices == min_vals) | (prices == max_vals)
        gap_mask = np.diff(ts, prepend=ts[0]) > unit

        selected = np.where(gap_mask | is_extreme)[0]
        return histories.iloc[
            np.unique(np.concatenate([selected, [0, len(histories) - 1]]))
        ]

    def generate_trend_plot(self, histories: pd.DataFrame) -> BytesIO:
        value_rate = (histories["value"] / histories["value"].iloc[0] - 1) * 100
        price_rate = (histories["price"] / histories["price"].iloc[0] - 1) * 100
        ratio = histories["ratio"] * 100

        fig, ax1 = plt.subplots(figsize=(10, 6))

        ax1.set_ylabel("Cash Ratio (%)", color="tab:blue")
        ax1.plot(
            histories["timestamp"],
            ratio,
            label="Ratio",
            color="tab:blue",
            linestyle="-.",
        )
        ax1.tick_params(axis="y", labelcolor="tab:blue")
        ax1.set_ylim(0, 100)

        ax1.fill_between(
            histories["timestamp"],
            ratio,
            100,
            color="lightcoral",
            alpha=0.3,
        )
        ax1.fill_between(
            histories["timestamp"],
            ratio,
            0,
            color="lightblue",
            alpha=0.3,
        )

        ax2 = ax1.twinx()
        ax2.set_xlabel("Timestamp")
        ax2.set_ylabel("Rate of Change (%)", color="tab:green")
        ax2.plot(
            histories["timestamp"],
            value_rate,
            label="Value",
            color="tab:green",
            linestyle="-",
        )
        ax2.plot(
            histories["timestamp"],
            price_rate,
            label="Price",
            color="tab:red",
            linestyle="-",
        )
        ax2.tick_params(axis="y", labelcolor="tab:green")

        handles1, labels1 = ax1.get_legend_handles_labels()
        handles2, labels2 = ax2.get_legend_handles_labels()
        combined_handles = handles1 + handles2
        combined_labels = labels1 + labels2
        fig.legend(
            handles=combined_handles,
            labels=combined_labels,
            loc="upper left",
            bbox_to_anchor=(0.07, 0.94),
            framealpha=0.5,
        )

        plt.title("Balance Trends")
        plt.xlim(histories["timestamp"].iloc[0], histories["timestamp"].iloc[-1])
        fig.tight_layout()

        buffer = BytesIO()
        plt.savefig(buffer, format="png", bbox_inches="tight")
        plt.close()

        buffer.seek(0)
        return buffer
