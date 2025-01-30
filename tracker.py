import os
import csv
from datetime import datetime


class Tracker:
    def __init__(self, filepath: str = "./history.csv"):
        self.filepath = filepath

        if not os.path.exists(self.filepath):
            with open(self.filepath, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["timestamp", "price", "value"])

    def record_trade(self, value: float, price: float) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.filepath, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, price, value])
