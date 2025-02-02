from io import BytesIO
from typing import TYPE_CHECKING
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

    async def generate_distribution_plot(self) -> BytesIO:
        values = []
        labels = []
        balances = await self.broker.get_balances()
        for balance in balances:
            currency = balance["currency"]
            quantity = float(balance["balance"]) + float(balance["locked"])
            labels.append(currency)

            if currency != "KRW":
                price = await self.broker.get_current_price(f"KRW-{currency}")
                values.append(quantity * price)
            else:
                values.append(quantity)

        total = sum(values)
        buffer = BytesIO()
        plt.figure(figsize=(6, 6))
        plt.pie(
            [value / total for value in values],
            labels=labels,
            startangle=90,
            counterclock=False,
            autopct="%1.1f%%",
            wedgeprops={"width": 0.7},
        )
        plt.title("Portfolio Distribution")
        plt.axis("equal")
        plt.savefig(buffer, format="png")
        plt.close()

        buffer.seek(0)
        return buffer

    async def generate_trend_plot(self) -> BytesIO:
        df = await self.tracker.get_recent_histories()
        df["value"] = (df["value"] / df["value"].iloc[0] - 1) * 100
        df["price"] = (df["price"] / df["price"].iloc[0] - 1) * 100
        df["ratio"] *= 100

        fig, ax1 = plt.subplots(figsize=(10, 6))

        ax1.set_ylabel("Cash Ratio (%)", color="tab:blue")
        ax1.plot(
            df["timestamp"],
            df["ratio"],
            label="Ratio",
            color="tab:blue",
            linestyle="-.",
        )
        ax1.tick_params(axis="y", labelcolor="tab:blue")
        ax1.set_ylim(0, 100)

        ax1.fill_between(
            df["timestamp"],
            df["ratio"],
            100,
            color="lightcoral",
            alpha=0.3,
        )
        ax1.fill_between(
            df["timestamp"],
            df["ratio"],
            0,
            color="lightblue",
            alpha=0.3,
        )

        ax2 = ax1.twinx()
        ax2.set_xlabel("Timestamp")
        ax2.set_ylabel("Rate of Change (%)", color="tab:green")
        ax2.plot(
            df["timestamp"],
            df["value"],
            label="Value",
            color="tab:green",
            linestyle="-",
        )
        ax2.plot(
            df["timestamp"],
            df["price"],
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
        )

        plt.title("Balance Trends")
        plt.xlim(df["timestamp"].iloc[0], df["timestamp"].iloc[-1])
        fig.tight_layout()

        buffer = BytesIO()
        plt.savefig(buffer, format="png")
        plt.close()

        buffer.seek(0)
        return buffer
