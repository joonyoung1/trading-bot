import asyncio
import os
import logging
from enum import Enum

from broker import Broker
from utils import get_lower_price, get_upper_price
from config import config

logger = logging.getLogger(__name__)


class NotInitializedError(Exception): ...


class TradingBot:
    class State(Enum):
        INITIALIZED = 0
        RUNNING = 1
        STOPPING = 2
        TERMINATED = 3

    def __init__(self) -> None:
        self.state = self.State.TERMINATED
        self.TICKER = os.getenv("TICKER")
        self.pivot_price = config.get("PIVOT", float(os.getenv("PIVOT")))

        self.broker = Broker()

    async def initialize(self) -> None:
        self.broker.initialize()
        await self.broker.cancel_orders(self.TICKER)
        await self.update_balance()
        await self.calibrate_ratio()
        self.set_optimal_last_price()

        self.state = self.State.INITIALIZED

    async def update_balance(self) -> None:
        self.cash = await self.broker.get_balance("KRW")
        self.quantity = await self.broker.get_balance(self.TICKER)

        logger.info(f"cash: {self.cash}, quantity: {self.quantity}")

    async def calibrate_ratio(self) -> None:
        self.last_price = await self.broker.get_current_price(self.TICKER)
        volume = self.calc_volume(self.last_price)

        logger.info(f"calibration volume: {volume}")

        if abs(volume) >= 5001:
            if volume > 0:
                order = await self.broker.buy_market_order(self.TICKER, volume)
            else:
                order = await self.broker.sell_market_order(
                    self.TICKER, -volume / self.last_price
                )

            await self.wait_order_closed(order["uuid"])
            await self.update_balance()

    def set_optimal_last_price(self) -> None:
        min_volume = abs(self.calc_volume(self.last_price))
        optimal_price = self.last_price

        for func in (get_lower_price, get_upper_price):
            price = self.last_price
            while True:
                price = func(price)
                volume = abs(self.calc_volume(price))

                if volume < min_volume:
                    min_volume = volume
                    optimal_price = price
                else:
                    break
        self.last_price = optimal_price

    async def start(self) -> None:
        if self.state != self.State.INITIALIZED:
            raise NotInitializedError

        self.state = self.State.RUNNING
        await self.run()

    async def stop(self) -> None:
        self.state = self.State.STOPPING

        while self.state != self.State.TERMINATED:
            await asyncio.sleep(0.5)

    async def run(self) -> None:
        while self.state == self.State.RUNNING:
            buy_uuid, sell_uuid, lower_price, upper_price = await self.place_orders()
            any_closed, bought = await self.wait_any_closed(buy_uuid, sell_uuid)
            await self.broker.cancel_orders(self.TICKER)

            if any_closed:
                self.last_price = lower_price if bought else upper_price
                self.update_pivot_price()
                await self.update_balance()

        self.state = self.State.TERMINATED

    async def place_orders(self) -> tuple[str, str, float, float]:
        if self.last_price is not None:
            price = self.last_price
        else:
            price = await self.broker.get_current_price(self.TICKER)

        lower_price = price
        while True:
            volume = self.calc_volume(lower_price)
            if volume >= 5001 and self.is_trade_profitable(lower_price):
                quantity = volume / lower_price
                buy_order = await self.broker.buy_limit_order(
                    self.TICKER, lower_price, quantity
                )
                break

            lower_price = get_lower_price(lower_price)

        upper_price = price
        while True:
            volume = -self.calc_volume(upper_price)
            if volume >= 5001 and self.is_trade_profitable(upper_price):
                quantity = volume / upper_price
                sell_order = await self.broker.sell_limit_order(
                    self.TICKER, upper_price, volume / upper_price
                )
                break

            upper_price = get_upper_price(upper_price)

        return buy_order["uuid"], sell_order["uuid"], lower_price, upper_price

    async def wait_any_closed(
        self, buy_uuid: str, sell_uuid: str
    ) -> tuple[bool, bool | None]:
        while self.state == self.State.RUNNING:
            if await self.broker.check_order_closed(buy_uuid):
                return True, True

            if await self.broker.check_order_closed(sell_uuid):
                return True, False

            await asyncio.sleep(3)

        return False, None

    async def wait_order_closed(self, uuid: str) -> None:
        while not await self.broker.check_order_closed(uuid):
            asyncio.sleep(0.5)

    def is_trade_profitable(self, price: float) -> bool:
        return abs(self.last_price - price) / self.last_price >= 0.005

    def update_pivot_price(self) -> None:
        if self.last_price >= self.pivot_price * 3:
            self.pivot_price = self.last_price / 3
            config.set("PIVOT", self.pivot_price)

        elif self.pivot_price >= self.last_price * 3:
            self.pivot_price = self.last_price * 3
            config.set("PIVOT", self.pivot_price)

    def calc_volume(self, price: float) -> float:
        if price >= self.pivot_price:
            delta = price / self.pivot_price - 1
            ratio = -0.5 * 2**-delta + 1
        else:
            delta = self.pivot_price / price - 1
            ratio = 0.5 * 2**-delta

        value = self.quantity * price + self.cash
        return self.cash - value * ratio

    def get_status(self) -> bool:
        return self.state == self.State.RUNNING
