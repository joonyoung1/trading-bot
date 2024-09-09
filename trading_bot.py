from functools import wraps
from math import sqrt
import time

from broker import Broker
from logging import Logger
from chat_bot import ChatBot
from multiprocessing import Queue


class TradingBot:
    SENTINEL = "STOP"

    def __init__(
        self,
        ticker: str,
        queue: Queue,
        broker: Broker,
        chat_bot: ChatBot,
        logger: Logger,
        initial_price: float | None = None,
        last_trade_price: float | None = None,
    ) -> None:
        self.ticker: str = ticker
        self.queue: Queue = queue
        self.broker: Broker = broker
        self.chat_bot: ChatBot = chat_bot
        self.logger: Logger = logger

        self.cash: float = 0
        self.quantity: float = 0
        self.running: bool = False

        self.initial_price: float = (
            initial_price
            if initial_price is not None
            else self.broker.get_current_price()
        )
        self.last_trade_price: float | None = last_trade_price

    @staticmethod
    def handle_errors(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            try:
                return method(self, *args, **kwargs)
            except Exception as e:
                self.logger.error(f"An error occurred: {e}", exc_info=True)
                raise

        return wrapper

    @handle_errors
    def start(self) -> None:
        self.logger.info("Starting TradingBot...")

        self.running = True
        self.update_balance()
        self.broker.cancel_orders(self.ticker)
        self.logger.info("TradingBot initialized.")

        self.chat_bot.notify(
            self.broker.get_current_price(self.ticker), self.cash, self.quantity
        )
        self.logger.info("TradingBot started.")

        self.run()

    @handle_errors
    def run(self) -> None:
        while True:
            data = self.queue.get()
            if data == self.SENTINEL:
                break

            price = data["trade_price"]
            if (
                self.last_trade_price is not None
                and abs(self.last_trade_price / price - 1) > 0.002
            ):
                self.process_trade(price)
        self.logger.info("TradingBot terminated.")

    @handle_errors
    def terminate(self) -> None:
        self.logger.info("Terminating TradingBot...")
        self.queue.put(self.SENTINEL)

    @handle_errors
    def update_balance(self) -> None:
        try:
            self.cash = self.broker.get_balance("KRW")
            self.quantity = self.broker.get_balance(self.ticker)
            self.logger.info(
                f"Cash: ₩{self.cash:.2f}, Assets: {self.quantity:.2f} units."
            )
        except Exception as e:
            self.logger.error(f"Failed to update balance: {e}")
            raise

    @handle_errors
    def process_trade(self, price: float) -> None:
        delta = price / self.initial_price - 1
        if delta == 0:
            ratio = 0.5
        elif delta < 0:
            ratio = 0.5 - 0.5 * sqrt(abs(delta))
        else:
            ratio = 0.5 + 0.5 * sqrt(delta)

        value = price * self.quantity
        total_value = self.cash + value

        volume = self.cash - total_value * ratio
        if abs(volume) < max(5001, total_value * 0.01):
            return

        if volume > 0:
            ret = self.buy(price, volume / price)
        elif volume < 0:
            ret = self.sell(price, -volume / price)

        self.update_balance()
        if ret:
            self.last_trade_price = price
            self.chat_bot.notify(price, self.cash, self.quantity, volume)

    @handle_errors
    def buy(self, price: float, quantity: float) -> bool:
        self.logger.info(f"Buy {quantity:.2f} at {price} (₩{price * quantity:.2f}).")

        try:
            order = self.broker.buy_limit_order(self.ticker, price, quantity)
            uuid = order["uuid"]
            self.logger.info(f"Order [{uuid}] opened.")
            return self.wait(uuid)
        except Exception as e:
            self.logger.error(f"Failed to place buy order: {e}")
            return False

    @handle_errors
    def sell(self, price: float, quantity: float) -> bool:
        self.logger.info(f"Sell {quantity:.2f} at {price} (₩{price * quantity:.2f}).")

        try:
            order = self.broker.sell_limit_order(self.ticker, price, quantity)
            uuid = order["uuid"]
            self.logger.info(f"Order [{uuid}] opened.")
            return self.wait(uuid)
        except Exception as e:
            self.logger.error(f"Failed to place sell order: {e}")
            return False

    @handle_errors
    def wait(self, uuid: str, timeout: float = 180, interval: float = 10) -> bool:
        end_time = time.time() + timeout

        closed = False
        while time.time() < end_time and self.running:
            if self.broker.check_order_closed(uuid):
                closed = True
                break
            time.sleep(interval)

        if closed:
            self.logger.info(f"Order [{uuid}] has been closed.")
        else:
            self.logger.warning(
                f"Order [{uuid}] did not close within the expected time. Cancelling all open orders."
            )
            self.broker.cancel_orders(self.ticker)
            self.logger.info(f"All open orders have been canceled.")

        self.empty_queue()
        return closed

    @handle_errors
    def empty_queue(self) -> None:
        while not self.queue.empty():
            data = self.queue.get_nowait()
            if data == self.SENTINEL:
                self.queue.put(self.SENTINEL)
                break
