import os
import time
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

load_dotenv()

import pyupbit
from pyupbit import WebSocketManager


ACCESS = os.getenv("ACCESS")
SECRET = os.getenv("SECRET")
TICKER = os.getenv("TICKER")


class TradingBot:
    def __init__(self):
        self.upbit = pyupbit.Upbit(ACCESS, SECRET)
        self.update_balance()
        self.cancel_orders()
        self.init_logger()

    def init_logger(self):
        self.logger = logging.getLogger("logger")
        self.logger.setLevel(logging.DEBUG)

        handler = RotatingFileHandler(
            "logfile.log", maxBytes=1024 * 1024 * 5, backupCount=3
        )
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def run(self):
        wm = WebSocketManager("ticker", [TICKER])
        while True:
            data = wm.get()
            price = data["trade_price"]
            ret = self.action(price)

            if ret:
                self.update_balance()

    def action(self, price):
        asset_value = price * self.quantity
        total_value = self.cash + asset_value

        volume = abs(self.cash - asset_value) / 2
        if volume < 5001:
            return False

        ratio = asset_value / total_value
        if ratio < 0.5:
            ret = self.buy(price, volume / price)
        elif ratio > 0.505:
            ret = self.sell(price, volume / price)

        return ret

    def buy(self, price, quantity):
        order = self.upbit.buy_limit_order(TICKER, price, quantity)
        uuid = order["uuid"]

        self.logger.info(f"Buy {quantity} at {price} (₩{price * quantity}).")
        self.logger.info(f"Order [{uuid}] opened.")

        return self.wait(uuid)

    def sell(self, price, quantity):
        order = self.upbit.sell_limit_order(TICKER, price, quantity)
        uuid = order["uuid"]

        self.logger.info(f"Sell {quantity} at {price} (₩{price * quantity}).")
        self.logger.info(f"Order [{uuid}] opened.")

        return self.wait(order)

    def wait(self, uuid):
        for _ in range(30):
            order = self.upbit.get_order(uuid)
            if order["state"] == "done":
                self.logger.info(f"Order [{uuid}] has been successfully closed.")
                return True
            time.sleep(10)

        self.cancel_orders()
        return False

    def update_balance(self):
        self.cash = self.upbit.get_balance("KRW")
        self.quantity = self.upbit.get_balance(TICKER)
        self.logger.info(f"Cash: ₩{self.cash}, Assets: {self.quantity} units.")

    def cancel_orders(self):
        self.logger.info("Closing all open orders...")
        
        orders = self.upbit.get_order(TICKER)
        for order in orders:
            uuid = order["uuid"]
            self.upbit.cancel_order(uuid)
        
        self.logger.info("All open orders have been successfully closed.")

if __name__ == "__main__":
    trading_bot = TradingBot()
    trading_bot.run()
