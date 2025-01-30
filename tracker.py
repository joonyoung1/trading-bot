import csv
import pandas as pd
from datetime import datetime, timedelta
from file_read_backwards import FileReadBackwards


class Tracker:
    def __init__(self, filepath: str = "./history.csv"):
        self.filepath = filepath

    def record_trade(self, value: float, price: float) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.filepath, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, price, value])

    def get_recent_histories(self) -> pd.DataFrame:
        time_limit = datetime.now() - timedelta(days=1)
        data = []

        with FileReadBackwards(self.filepath) as frb:
            while True:
                line = frb.readline().strip()
                if not line:
                    break

                timestamp, price, value = line.split(",")
                timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                if timestamp < time_limit:
                    break

                price = float(price)
                value = float(value)
                data.append([timestamp, price, value])

        return pd.DataFrame(data[::-1], columns=["timestamp", "price", "value"])
