import os
import asyncio
from functools import partial

import pyupbit


class Broker:
    def __init__(self) -> None:
        self.ACCESS = os.getenv("ACCESS")
        self.SECRET = os.getenv("SECRET")
        self.TICKER = os.getenv("TICKER")

        self.upbit = pyupbit.Upbit(self.ACCESS, self.SECRET)
        self.loop = asyncio.get_event_loop()
    
    async def get_current_price(self) -> float:
        task = partial(pyupbit.get_current_price, self.TICKER)
        price = await self.loop.run_in_executor(None, task)
        return float(price)
    
    async def get_balance(self) -> float:
        task = partial(self.upbit.get_balance, self.TICKER)
        balance = await self.loop.run_in_executor(None, task)

        if balance is None:
            raise ValueError("Balance is `None` instead of a float")
        return balance
    
    async def buy_limit_order(self, price: float, quantity: float) -> dict:
        task = partial(self.upbit.buy_limit_order, self.TICKER, price, quantity)
        return await self.loop.run_in_executor(None, task)

    async def sell_limit_order(self, price: float, quantity: float) -> dict:
        task = partial(self.upbit.sell_limit_order, self.TICKER, price, quantity)
        return await self.loop.run_in_executor(None, task)

    async def check_order_closed(self, uuid: str) -> bool:
        order = await self.get_order(uuid)
        return order is not None and (
            order["state"] == "done" or order["state"] == "cancel"
        )

    async def get_order(self, uuid_or_ticker: str) -> dict:
        task = partial(self.upbit.get_order, uuid_or_ticker)
        return await self.loop.run_in_executor(None, task)

    async def cancel_orders(self, ticker: str) -> None:
        response = await self.get_order(ticker)
        if isinstance(response, dict) and "error" in response:
            error = response["error"]
            error_name = error.get("name", "Unknown error")
            error_message = error.get("message", "No error message provided")
            raise ConnectionError(f"Error: {error_name} - {error_message}")

        for order in response:
            uuid = order["uuid"]
            self.upbit.cancel_order(uuid)
