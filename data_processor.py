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

    def count_recent_trades(self) -> int:
        df = self.tracker.get_recent_histories()
        return len(df)
