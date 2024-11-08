import os
import csv
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt


class Tracker:
    def __init__(
        self, history_file: str = "history.csv", plot_folder: str = "./plots"
    ) -> None:
        self.history_file: str = history_file
        self.plot_folder: str = plot_folder

        if not os.path.exists(self.history_file):
            with open(self.history_file, "a", newline="") as file:
                writer = csv.writer(file)
                if file.tell() == 0:
                    writer.writerow(["timestamp", "price", "balance"])

        if not os.path.exists(self.plot_folder):
            os.makedirs(self.plot_folder)

    def get_last_data(self) -> tuple[float, float]:
        with open(self.history_file, "r") as file:
            reader = csv.reader(file)
            header = next(reader)
            price_idx = header.index("price")
            timestamp_idx = header.index("timestamp")

            line = next(reader, None)
            if line is None:
                return None
            
            first_line = line
            for line in reader:
                pass

            last_trade_price = (
                None
                if first_line[timestamp_idx] == line[timestamp_idx]
                else float(line[price_idx])
            )
            return last_trade_price

    def record_history(self, price, balance):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.history_file, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, price, balance])

    def generate_history_graph(self) -> str:
        df = pd.read_csv(self.history_file)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        initial_balance = df["balance"].iloc[0]
        initial_price = df["price"].iloc[0]

        df["cumulative_return"] = (
            (df["balance"] - initial_balance) / initial_balance * 100
        )
        df["cumulative_price"] = (df["price"] - initial_price) / initial_price * 100
        df.set_index("timestamp", inplace=True)

        df["cumulative_price"].plot(label="Cumulative Price", color="red", linestyle="-")
        df["cumulative_return"].plot(label="Cumulative Return", color="orange", linestyle="--")

        plt.xlabel("Date")
        plt.ylabel("Percentage (%)")
        plt.title("Cumulative Return and Cumulative Price")
        plt.legend()
        plt.grid(True)

        plot_name = f"{datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}_history.png"
        plot_path = os.path.join(self.plot_folder, plot_name)
        plt.savefig(plot_path, bbox_inches="tight")
        plt.close()

        return plot_path
