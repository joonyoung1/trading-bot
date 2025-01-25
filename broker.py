import os
import asyncio
from functools import partial

import pyupbit

from utils import retry


class Broker:
    def __init__(self) -> None:
        self.ACCESS = os.getenv("ACCESS")
        self.SECRET = os.getenv("SECRET")

        self.upbit = pyupbit.Upbit(self.ACCESS, self.SECRET)
        self.loop = asyncio.get_running_loop()
    
    @retry()
    async def get_current_price(self, ticker) -> float:
        task = partial(pyupbit.get_current_price, ticker)
        price = await self.loop.run_in_executor(None, task)
        return float(price)
    
    @retry()
    async def get_balance(self, ticker: str) -> float:
        task = partial(self.upbit.get_balance, ticker)
        balance = await self.loop.run_in_executor(None, task)

        if balance is None:
            raise ValueError("Balance is `None` instead of a float")
        return balance
    
    @retry()
    async def buy_limit_order(self, ticker: str, price: float, quantity: float) -> dict:
        task = partial(self.upbit.buy_limit_order, ticker, price, quantity)
        return await self.loop.run_in_executor(None, task)

    @retry()
    async def sell_limit_order(self, ticker: str, price: float, quantity: float) -> dict:
        task = partial(self.upbit.sell_limit_order, ticker, price, quantity)
        return await self.loop.run_in_executor(None, task)

    @retry()
    async def check_order_closed(self, uuid: str) -> bool:
        order = await self.get_order(uuid)
        return order is not None and (
            order["state"] == "done" or order["state"] == "cancel"
        )

    @retry()
    async def get_order(self, uuid_or_ticker: str) -> dict:
        task = partial(self.upbit.get_order, uuid_or_ticker)
        return await self.loop.run_in_executor(None, task)

    @retry()
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
