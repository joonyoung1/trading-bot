import asyncio
import os
import logging

from broker import Broker
from utils import get_lower_price, get_upper_price

logger = logging.getLogger(__name__)


class NotInitializedError(Exception): ...


class TradingBot:
    def __init__(self) -> None:
        self.initialized = False
        self.running = False
        self.TICKER = os.getenv("TICKER")
        self.pivot_price = os.getenv("PIVOT")

        self.broker = Broker()

    async def initialize(self) -> None:
        await self.broker.cancel_orders(self.TICKER)
        await self.update_balance()
        await self.calibrate_ratio()

        self.initialized = True

    async def update_balance(self) -> None:
        self.cash = await self.broker.get_balance("KRW")
        self.quantity = await self.broker.get_balance(self.TICKER)

    async def calibrate_ratio(self):
        self.last_price = await self.broker.get_balance(self.TICKER)
        ratio = self.calc_ratio(self.last_price)
        value = self.quantity * self.last_price + self.cash
        volume = self.cash - value * ratio

        if volume >= 5001:
            order = await self.broker.buy_market_order(self.TICKER, volume)
        elif volume <= -5001:
            order = await self.broker.sell_market_order(
                self.TICKER, -volume / self.last_price
            )

        await self.wait_order_closed(order["uuid"])
        await self.update_balance()

    async def start(self) -> None:
        if not self.initialized:
            raise NotInitializedError

        self.running = True
        await self.run()

    async def stop(self) -> None:
        self.running = False
        self.initialized = False

    async def run(self) -> None:
        while self.running:
            buy_uuid, sell_uuid, lower_price, upper_price = await self.place_orders()
            any_closed, bought = await self.wait_any_closed(buy_uuid, sell_uuid)
            await self.broker.cancel_orders(self.TICKER)

            if any_closed:
                self.last_price = lower_price if bought else upper_price
                await self.update_balance()

    async def place_orders(self) -> tuple[str, str, float, float]:
        if self.last_price is not None:
            price = self.last_price
        else:
            price = await self.broker.get_current_price(self.TICKER)

        lower_price = price
        while True:
            ratio = self.calc_ratio(lower_price)
            value = self.quantity * lower_price + self.cash
            volume = self.cash - value * ratio

            if volume >= 5001 and self.is_trade_profitable(lower_price):
                quantity = volume / lower_price
                buy_order = await self.broker.buy_limit_order(
                    self.TICKER, lower_price, quantity
                )
                break

            lower_price = get_lower_price(lower_price)

        upper_price = price
        while True:
            ratio = self.calc_ratio(upper_price)
            value = self.quantity * upper_price + self.cash
            volume = value * ratio - self.cash

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
        while self.running:
            if await self.broker.check_order_closed(buy_uuid):
                return True, True

            if await self.broker.check_order_closed(sell_uuid):
                return True, False

            asyncio.sleep(3)

        return False, None

    async def wait_order_closed(self, uuid: str) -> None:
        while not await self.broker.check_order_closed(uuid):
            asyncio.sleep(0.5)

    def is_trade_profitable(self, price: float) -> bool:
        return abs(self.last_price - price) / self.last_price >= 0.005

    def calc_ratio(self, price):
        if price >= self.pivot_price:
            delta = price / self.pivot_price - 1
            ratio = -0.5 * 2**-delta + 1
        else:
            delta = self.pivot_price / price - 1
            ratio = 0.5 * 2**-delta
        return ratio

    def get_status(self) -> bool:
        return self.running
