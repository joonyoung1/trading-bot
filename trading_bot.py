import asyncio
import os

from broker import Broker


class NotInitializedError(Exception): ...


class TradingBot:
    def __init__(self) -> None:
        self.initialized = False
        self.running = False
        self.TICKER = os.getenv("TICKER")

        self.broker = Broker()

    async def initialize(self) -> None:
        await self.broker.cancel_orders(self.TICKER)
        await self.update_balance()

        self.initialized = True

    async def update_balance(self) -> None:
        self.cash = await self.broker.get_balance("KRW")
        self.quantity = await self.broker.get_balance(self.TICKER)

    async def start(self) -> None:
        if not self.initialized:
            raise NotInitializedError

        self.running = True
        while self.running:
            await asyncio.sleep(1)
            print("running...")

    async def stop(self) -> None:
        self.running = False
        self.initialized = False

    def get_status(self) -> bool:
        return self.running
