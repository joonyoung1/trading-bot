import os
import csv
import pandas as pd
import asyncio
from datetime import datetime, timedelta
from file_read_backwards import FileReadBackwards

from schemas import Cols


class Tracker:
    def __init__(self, filepath: str = "./history.csv"):
        self.filepath = filepath
        self.file_lock = asyncio.Lock()

        if not os.path.exists(self.filepath):
            open(self.filepath, "w").close()

    async def record_trade(self, value: float, price: float, ratio: float) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        async with self.file_lock:
            with open(self.filepath, "a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([timestamp, value, price, ratio])

    async def get_recent_histories(self) -> pd.DataFrame:
        time_limit = datetime.now() - timedelta(days=90)
        data = []

        async with self.file_lock:
            with FileReadBackwards(self.filepath) as frb:
                while True:
                    line = frb.readline().strip()
                    if not line:
                        break

                    timestamp, balance, price, ratio = line.split(",")
                    timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                    if timestamp < time_limit:
                        break

                    balance = float(balance)
                    price = float(price)
                    ratio = float(ratio)
                    data.append([timestamp, balance, price, ratio])

        return pd.DataFrame(
            data[::-1], columns=[Cols.TS, Cols.BAL, Cols.P, Cols.R]
        )
