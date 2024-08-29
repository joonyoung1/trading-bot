import os
import time
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
            self.upbit.buy_limit_order(TICKER, price, volume / price)
            ret = self.wait()
        elif ratio > 0.505:
            self.upbit.sell_limit_order(TICKER, price, volume / price)
            ret = self.wait()
            
        return ret
    
    def wait(self):
        for _ in range(30):
            orders = self.upbit.get_order(TICKER)
            if not orders:
                return True
            time.sleep(10)
        
        self.cancel_orders()
        return False

    def update_balance(self):
        self.cash = self.upbit.get_balance("KRW")
        self.quantity = self.upbit.get_balance(TICKER)
    
    def cancel_orders(self):
        orders = self.upbit.get_order(TICKER)
        for order in orders:
            uuid = order["uuid"]
            self.upbit.cancel_order(uuid)


if __name__ == "__main__":
    trading_bot = TradingBot()
    trading_bot.run()