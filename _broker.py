import pyupbit
from pyupbit import Upbit


class Broker:
    def __init__(self, access: str, secret: str) -> None:
        self.upbit: Upbit = Upbit(access, secret)

    def get_current_price(self, ticker: str) -> float:
        return float(pyupbit.get_current_price(ticker))

    def get_balance(self, ticker: str) -> float:
        balance = self.upbit.get_balance(ticker)
        if balance is None:
            raise ValueError("Balance is `None` instead of a float")
        return balance

    def buy_limit_order(self, ticker: str, price: float, quantity: float) -> dict:
        return self.upbit.buy_limit_order(ticker, price, quantity)

    def sell_limit_order(self, ticker: str, price: float, quantity: float) -> dict:
        return self.upbit.sell_limit_order(ticker, price, quantity)

    def check_order_closed(self, uuid: str) -> bool:
        order = self.upbit.get_order(uuid)
        return order is not None and (
            order["state"] == "done" or order["state"] == "cancel"
        )

    def get_order(self, uuid: str) -> dict:
        return self.upbit.get_order(uuid)

    def cancel_orders(self, ticker: str) -> None:
        response = self.upbit.get_order(ticker)
        if isinstance(response, dict) and "error" in response:
            error = response["error"]
            error_name = error.get("name", "Unknown error")
            error_message = error.get("message", "No error message provided")
            raise ConnectionError(f"Error: {error_name} - {error_message}")

        for order in response:
            uuid = order["uuid"]
            self.upbit.cancel_order(uuid)
