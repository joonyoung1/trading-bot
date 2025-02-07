import os
from io import BytesIO
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import numpy as np
from scipy.integrate import quad
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

from config import config
from utils import calc_ratio
from schemas import ConfigKeys, Cols, Status, Dashboard

matplotlib.use("Agg")

if TYPE_CHECKING:
    from app.broker import Broker
    from app.tracker import Tracker


class DataProcessor:
    def __init__(self, broker: "Broker", tracker: "Tracker") -> None:
        self.broker = broker
        self.tracker = tracker
        self.TICKER = os.getenv(ConfigKeys.TICKER)

    async def construct_status(self, histories: pd.DataFrame) -> Status:
        history_3m = histories.iloc[0]

        time_24h = datetime.now() - timedelta(hours=24)
        idx_24h = histories[Cols.TS].searchsorted(time_24h)
        history_24h = histories.iloc[idx_24h]

        cash = await self.broker.get_balance("KRW")
        quantity = await self.broker.get_balance(self.TICKER)
        current_price = await self.broker.get_current_price(self.TICKER)
        current_balance = cash + quantity * current_price

        estimated_balance_3m = self.estimate_balance_at_price(
            current_balance, current_price, history_3m[Cols.P]
        )
        profit_3m, profit_rate_3m = self.calc_delta_rate(
            estimated_balance_3m, history_3m[Cols.BAL]
        )
        estimated_balance_24h = self.estimate_balance_at_price(
            current_balance, current_price, history_24h[Cols.P]
        )
        profit_24h, profit_rate_24h = self.calc_delta_rate(
            estimated_balance_24h, history_24h[Cols.BAL]
        )

        balance_delta_3m, balance_rate_3m = self.calc_delta_rate(
            current_balance, history_3m[Cols.BAL]
        )
        balance_delta_24h, balance_rate_24h = self.calc_delta_rate(
            current_balance, history_24h[Cols.BAL]
        )

        price_delta_3m, price_rate_3m = self.calc_delta_rate(
            current_price, history_3m[Cols.P]
        )
        price_delta_24h, price_rate_24h = self.calc_delta_rate(
            current_price, history_24h[Cols.P]
        )

        return Status(
            profit_3m=profit_3m,
            profit_rate_3m=profit_rate_3m,
            profit_24h=profit_24h,
            profit_rate_24h=profit_rate_24h,
            balance=current_balance,
            balance_delta_3m=balance_delta_3m,
            balance_rate_3m=balance_rate_3m,
            balance_delta_24h=balance_delta_24h,
            balance_rate_24h=balance_rate_24h,
            price=current_price,
            price_delta_3m=price_delta_3m,
            price_rate_3m=price_rate_3m,
            price_delta_24h=price_delta_24h,
            price_rate_24h=price_rate_24h,
        )

    @staticmethod
    def calc_delta_rate(pivot: float, comp: float) -> tuple[float, float]:
        delta = pivot - comp
        rate = delta / comp * 100
        return delta, rate

    @staticmethod
    def estimate_balance_at_price(
        balance: float, cur_price: float, target_price: float
    ) -> float:
        pivot_price = config.get(ConfigKeys.PIVOT)

        def integrand(price: float):
            ratio = calc_ratio(price, pivot_price)
            return (1 - ratio) / price

        integral, _ = quad(integrand, cur_price, target_price)
        return balance * np.exp(integral)

    async def process(self) -> Dashboard:
        histories = await self.tracker.get_recent_histories()
        status = await self.construct_status(histories)

        histories = self.adaptive_sampling(histories)
        trend_plot = self.generate_trend_plot(histories)

        return Dashboard(trend=trend_plot, status=status)

    def adaptive_sampling(self, histories: pd.DataFrame) -> pd.DataFrame:
        time_diff = histories[Cols.TS].iloc[-1] - histories[Cols.TS].iloc[0]
        unit = time_diff.total_seconds() * 1e9 / 240
        ts = histories[Cols.TS].astype("int64").to_numpy()

        min_vals = np.empty(len(histories))
        max_vals = np.empty(len(histories))

        start_idx = 0
        end_idx = 0
        for i in range(len(histories)):
            while ts[i] - ts[start_idx] > unit:
                start_idx += 1
            while end_idx < len(histories) and ts[end_idx] - ts[i] < unit:
                end_idx += 1

            window = histories[Cols.P].iloc[start_idx:end_idx]
            min_vals[i] = window.min()
            max_vals[i] = window.max()

        prices = histories[Cols.P].to_numpy()
        is_extreme = (prices == min_vals) | (prices == max_vals)
        gap_mask = np.diff(ts, prepend=ts[0]) > unit

        selected = np.where(gap_mask | is_extreme)[0]
        return histories.iloc[
            np.unique(np.concatenate([selected, [0, len(histories) - 1]]))
        ]

    def generate_trend_plot(self, histories: pd.DataFrame) -> BytesIO:
        value_rate = (histories[Cols.BAL] / histories[Cols.BAL].iloc[0] - 1) * 100
        price_rate = (histories[Cols.P] / histories[Cols.P].iloc[0] - 1) * 100
        ratio = histories[Cols.R] * 100

        fig, ax1 = plt.subplots(figsize=(10, 6))

        ax1.set_ylabel("Cash Ratio (%)", color="tab:blue")
        ax1.plot(
            histories[Cols.TS],
            ratio,
            label=Cols.R,
            color="tab:blue",
            linestyle="-.",
        )
        ax1.tick_params(axis="y", labelcolor="tab:blue")
        ax1.set_ylim(0, 100)

        ax1.fill_between(
            histories[Cols.TS],
            ratio,
            100,
            color="lightcoral",
            alpha=0.3,
        )
        ax1.fill_between(
            histories[Cols.TS],
            ratio,
            0,
            color="lightblue",
            alpha=0.3,
        )

        ax2 = ax1.twinx()
        ax2.set_xlabel(Cols.TS)
        ax2.set_ylabel("Rate of Change (%)", color="tab:green")
        ax2.plot(
            histories[Cols.TS],
            value_rate,
            label=Cols.BAL,
            color="tab:green",
            linestyle="-",
        )
        ax2.plot(
            histories[Cols.TS],
            price_rate,
            label=Cols.P,
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
        plt.xlim(histories[Cols.TS].iloc[0], histories[Cols.TS].iloc[-1])
        fig.tight_layout()

        buffer = BytesIO()
        plt.savefig(buffer, format="png", bbox_inches="tight")
        plt.close()

        buffer.seek(0)
        return buffer
