import os
import csv
import pandas as pd
from datetime import datetime, timedelta
from file_read_backwards import FileReadBackwards


class Tracker:
    def __init__(self, filepath: str = "./history.csv"):
        self.filepath = filepath

        if not os.path.exists(self.filepath):
            open(self.filepath, "w").close()

    def record_trade(self, value: float, price: float, ratio: float) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.filepath, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, value, price, ratio])

    def get_recent_histories(self) -> pd.DataFrame:
        time_limit = datetime.now() - timedelta(days=1)
        data = []

        with FileReadBackwards(self.filepath) as frb:
            while True:
                line = frb.readline().strip()
                if not line:
                    break

                timestamp, value, price = line.split(",")
                timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                if timestamp < time_limit:
                    break

                value = float(value)
                price = float(price)
                ratio = float(ratio)
                data.append([timestamp, value, price, ratio])

        return pd.DataFrame(
            data[::-1], columns=["timestamp", "value", "price", "ratio"]
        )
