from io import BytesIO
from typing import TYPE_CHECKING
from dataclasses import dataclass

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use("Agg")

if TYPE_CHECKING:
    from broker import Broker
    from tracker import Tracker


@dataclass
class Status:
    balance: float
    balance_change_rate: float
    cash: float
    cash_change_rate: float
    value: float
    value_change_rate: float
    quantity: float
    quantity_change_rate: float
    price: float
    price_change_rate: float


@dataclass
class Dashboard:
    trend: BytesIO
    status: Status
    n_trades: int


class DataProcessor:
    def __init__(self, broker: "Broker", tracker: "Tracker") -> None:
        self.broker = broker
        self.tracker = tracker

    async def process(self) -> Dashboard:
        histories = await self.tracker.get_recent_histories()
        trend_plot = await self.generate_trend_plot(histories)
        status = await self.get_current_status(histories)
        n_trades = self.count_recent_trades(histories)
        return Dashboard(trend=trend_plot, status=status, n_trades=n_trades)

    async def generate_trend_plot(self, histories: pd.DataFrame) -> BytesIO:
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

    def count_recent_trades(self, histories: pd.DataFrame) -> int:
        latest = histories["timestamp"].iloc[-1]
        cutoff = latest - pd.Timedelta(hours=24)
        start_idx = histories["timestamp"].searchsorted(cutoff, side="left")
        return len(histories) - start_idx

    async def get_current_status(self, histories: pd.DataFrame) -> Status:
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
        print(oldest)
        _balance = oldest["value"]
        _cash = _balance * oldest["ratio"]
        _value = _balance - _cash
        _price = oldest["price"]
        _quantity = _value / _price

        print(f"_balance: {_balance}")
        print(f"_cash: {_cash}")
        print(f"_value: {_value}")
        print(f"_price: {_price}")
        print(f"_quantity: {_quantity}")

        return Status(
            balance=balance,
            balance_change_rate=(balance / _balance - 1) * 100,
            cash=cash,
            cash_change_rate=(cash / _cash - 1) * 100,
            value=value,
            value_change_rate=(value / _value - 1) * 100,
            quantity=quantity,
            quantity_change_rate=(quantity / _quantity - 1) * 100,
            price=price,
            price_change_rate=(price / _price - 1) * 100,
        )


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    from broker import Broker
    from tracker import Tracker
    
    async def main():
        broker = Broker()
        loop = asyncio.get_running_loop()
        broker.set_loop(loop)
        tracker = Tracker()
        data_processor = DataProcessor(broker, tracker)

        result = await data_processor.process()
        from pprint import pprint
        pprint(result.status)
    import asyncio 
    asyncio.run(main())