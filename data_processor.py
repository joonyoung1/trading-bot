from io import BytesIO
from typing import TYPE_CHECKING
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use("Agg")

if TYPE_CHECKING:
    from broker import Broker
    from tracker import Tracker


class DataProcessor:
    def __init__(self, broker: "Broker", tracker: "Tracker") -> None:
        self.broker = broker
        self.tracker = tracker

    async def process(self) -> tuple[BytesIO, int]:
        histories = await self.tracker.get_recent_histories()
        trend_plot = await self.generate_trend_plot(histories)
        n_recent_trades = self.count_recent_trades(histories)
        return trend_plot, n_recent_trades

    async def generate_trend_plot(self, histories: pd.DataFrame) -> BytesIO:
        histories["value"] = (histories["value"] / histories["value"].iloc[0] - 1) * 100
        histories["price"] = (histories["price"] / histories["price"].iloc[0] - 1) * 100
        histories["ratio"] *= 100

        fig, ax1 = plt.subplots(figsize=(10, 6))

        ax1.set_ylabel("Cash Ratio (%)", color="tab:blue")
        ax1.plot(
            histories["timestamp"],
            histories["ratio"],
            label="Ratio",
            color="tab:blue",
            linestyle="-.",
        )
        ax1.tick_params(axis="y", labelcolor="tab:blue")
        ax1.set_ylim(0, 100)

        ax1.fill_between(
            histories["timestamp"],
            histories["ratio"],
            100,
            color="lightcoral",
            alpha=0.3,
        )
        ax1.fill_between(
            histories["timestamp"],
            histories["ratio"],
            0,
            color="lightblue",
            alpha=0.3,
        )

        ax2 = ax1.twinx()
        ax2.set_xlabel("Timestamp")
        ax2.set_ylabel("Rate of Change (%)", color="tab:green")
        ax2.plot(
            histories["timestamp"],
            histories["value"],
            label="Value",
            color="tab:green",
            linestyle="-",
        )
        ax2.plot(
            histories["timestamp"],
            histories["price"],
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
