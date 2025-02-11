import asyncio
import os
import logging
from enum import Enum, auto
from typing import TYPE_CHECKING

from .utils import get_lower_price, get_upper_price, calc_ratio
from .config import config
from constants import ConfigKeys

if TYPE_CHECKING:
    from app.broker import Broker
    from app.tracker import Tracker

logger = logging.getLogger(__name__)


class NotInitializedError(Exception): ...


class TradingBot:
    class State(Enum):
        INITIALIZED = auto()
        RUNNING = auto()
        STOPPING = auto()
        TERMINATED = auto()

    def __init__(self, broker: "Broker", tracker: "Tracker") -> None:
        self.broker = broker
        self.tracker = tracker

        self.state = self.State.TERMINATED
        self.TICKER = os.getenv(ConfigKeys.TICKER)

    async def initialize(self) -> None:
        await self.broker.cancel_orders(self.TICKER)
        await self.update_balance()
        await self.calibrate_ratio()
        self.update_pivot_price()
        self.set_optimal_last_price()

        self.state = self.State.INITIALIZED

    async def update_balance(self) -> None:
        balance_map = await self.broker.get_balances()

        cash = balance_map.get("KRW")
        self.cash = 0 if not cash else cash.balance + cash.locked

        coin = balance_map.get(self.TICKER)
        self.quantity = 0 if not coin else coin.balance + coin.locked

        logger.info(f"cash: {self.cash}, quantity: {self.quantity}")

    async def calibrate_ratio(self) -> None:
        self.last_price = await self.broker.get_current_price(self.TICKER)
        volume = self.calc_volume(self.last_price)

        logger.info(f"calibration volume: {volume}")

        if abs(volume) >= 5000:
            if volume > 0:
                order = await self.broker.buy_market_order(self.TICKER, volume)
            else:
                order = await self.broker.sell_market_order(
                    self.TICKER, -volume / self.last_price
                )

            await self.wait_order_closed(order.uuid)
            await self.update_balance()
            await self.record_trade()

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
        if self.state == self.State.RUNNING:
            self.state = self.State.STOPPING

            while self.state != self.State.TERMINATED:
                await asyncio.sleep(0.5)
        else:
            self.state = self.State.TERMINATED
        await self.broker.cancel_orders(self.TICKER)

    async def run(self) -> None:
        while self.state == self.State.RUNNING:
            buy_uuid, sell_uuid, lower_price, upper_price = await self.place_orders()
            any_closed, bought = await self.wait_any_closed(buy_uuid, sell_uuid)

            if any_closed:
                self.last_price = lower_price if bought else upper_price
                self.update_pivot_price()
                await self.update_balance()
                await self.record_trade()

                if bought:
                    await self.broker.cancel_order(sell_uuid)
                else:
                    await self.broker.cancel_order(buy_uuid)

        self.state = self.State.TERMINATED

    async def place_orders(self) -> tuple[str, str, float, float]:
        lower_price = self.last_price
        while True:
            volume = self.calc_volume(lower_price)
            if self.is_trade_profitable(lower_price) and volume >= 5000:
                quantity = volume / lower_price
                buy_order = await self.broker.buy_limit_order(
                    self.TICKER, lower_price, quantity
                )
                break

            lower_price = get_lower_price(lower_price)

        upper_price = self.last_price
        while True:
            volume = -self.calc_volume(upper_price)
            if self.is_trade_profitable(upper_price) and volume >= 5000:
                quantity = volume / upper_price
                sell_order = await self.broker.sell_limit_order(
                    self.TICKER, upper_price, quantity
                )
                break

            upper_price = get_upper_price(upper_price)

        return buy_order.uuid, sell_order.uuid, lower_price, upper_price

    async def wait_any_closed(
        self, buy_uuid: str, sell_uuid: str
    ) -> tuple[bool, bool | None]:
        while self.state == self.State.RUNNING:
            order_map = await self.broker.get_orders([buy_uuid, sell_uuid])

            if (
                order_map[buy_uuid].state == "done"
                or order_map[buy_uuid].state == "cancel"
            ):
                return True, True

            if (
                order_map[sell_uuid].state == "done"
                or order_map[sell_uuid].state == "cancel"
            ):
                return True, False

            await asyncio.sleep(1)

        return False, None

    async def wait_order_closed(self, uuid: str) -> None:
        while True:
            order = await self.broker.get_order(uuid)
            if order.state == "done" or order.state == "cancel":
                break
            await asyncio.sleep(0.5)

    def is_trade_profitable(self, price: float) -> bool:
        return abs(self.last_price - price) / self.last_price >= 0.005

    def update_pivot_price(self) -> None:
        pivot_price = config.get(ConfigKeys.PIVOT)
        if self.last_price >= pivot_price * 2:
            config.set(ConfigKeys.PIVOT, self.last_price / 2)

        elif pivot_price >= self.last_price * 2:
            config.set(ConfigKeys.PIVOT, self.last_price * 2)

    def calc_volume(self, price: float) -> float:
        ratio = calc_ratio(price, config.get(ConfigKeys.PIVOT))
        value = self.quantity * price + self.cash
        return self.cash - value * ratio

    def is_running(self) -> bool:
        return self.state == self.State.RUNNING

    def is_terminated(self) -> bool:
        return self.state == self.State.TERMINATED

    async def record_trade(self) -> None:
        value = self.cash + self.quantity * self.last_price
        ratio = self.cash / value
        await self.tracker.record_trade(value, self.last_price, ratio)
