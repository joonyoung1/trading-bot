import pyupbit
from pyupbit import Upbit
import time


class Broker:
    def __init__(self, access: str, secret: str) -> None:
        self.upbit: Upbit = Upbit(access, secret)
    
    def get_current_price(self, ticker: str) -> float:
        return pyupbit.get_current_price(ticker)

    def get_balance(self, ticker: str) -> float:
        return self.upbit.get_balance(ticker)

    def buy_limit_order(self, ticker: str, price: float, quantity: float) -> dict:
        return self.upbit.buy_limit_order(ticker, price, quantity)

    def sell_limit_order(self, ticker: str, price: float, quantity: float) -> dict:
        return self.upbit.sell_limit_order(ticker, price, quantity)

    def wait_order_close(
        self, uuid: str, timeout: float = 300, interval: float = 5
    ) -> bool:
        end_time = time.time() + timeout

        while time.time() < end_time:
            order = self.upbit.get_order(uuid)
            if order["state"] == "done":
                return True
            time.sleep(interval)
        
        return False

    def cancel_orders(self, ticker: str) -> None:
        orders = self.upbit.get_order(ticker)
        for order in orders:
            uuid = order["uuid"]
            self.upbit.cancel_order(uuid)