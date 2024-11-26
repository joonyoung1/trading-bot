from functools import wraps
import time

from broker import Broker
from logging import Logger
from chat_bot import ChatBot
from utils import get_upper_price, get_lower_price


class TradingBot:
    def __init__(
        self,
        ticker: str,
        broker: Broker,
        chat_bot: ChatBot,
        logger: Logger,
        pivot_price: float | None = None,
    ) -> None:
        self.ticker: str = ticker
        self.broker: Broker = broker
        self.chat_bot: ChatBot = chat_bot
        self.logger: Logger = logger

        self.cash: float = 0
        self.quantity: float = 0
        self.running: bool = False

        self.pivot_price: float = (
            pivot_price
            if pivot_price is not None
            else self.broker.get_current_price(self.ticker)
        )
        self.running: bool = False
        self.last_price: float = self.broker.get_current_price(self.ticker)

    @staticmethod
    def handle_errors(method):
        @wraps(method)
        def wrapper(self: "TradingBot", *args, **kwargs):
            try:
                return method(self, *args, **kwargs)
            except Exception as e:
                self.logger.error(f"An error occurred: {e}", exc_info=True)
                self.chat_bot.alert(f"An error occurred: {e}")
                raise

        return wrapper

    @handle_errors
    def start(self) -> None:
        self.logger.info("Starting TradingBot...")

        self.broker.cancel_orders(self.ticker)
        self.update_balance()
        self.logger.info("TradingBot initialized.")

        self.chat_bot.notify(
            self.broker.get_current_price(self.ticker), self.cash, self.quantity
        )
        self.logger.info("TradingBot started.")
        self.running = True
        self.run()

    @handle_errors
    def run(self) -> None:
        while self.running:
            buy_uuid, sell_uuid, lower_price, upper_price = self.place_orders()
            buy_closed = self.wait_any_closed(buy_uuid, sell_uuid)
            self.last_price = lower_price if buy_closed else upper_price

            self.broker.cancel_orders(self.ticker)
            self.wait_all_closed(buy_uuid, sell_uuid)
            self.update_balance()
            self.chat_bot.notify(
                self.broker.get_current_price(self.ticker),
                self.cash,
                self.quantity,
            )

        self.logger.info("TradingBot terminated.")

    @handle_errors
    def place_orders(self):
        price = self.broker.get_current_price(self.ticker)

        lower_price = price
        while True:
            ratio = self.calc_ratio(lower_price)
            value = self.quantity * lower_price + self.cash
            volume = self.cash - value * ratio

            if (
                volume > 5001
                and abs(self.last_price - lower_price) / self.last_price >= 0.005
            ):
                self.logger.info(
                    f"Buy {volume / lower_price:.2f} at {lower_price} (₩{volume:.2f})."
                )
                buy_order = self.broker.buy_limit_order(
                    self.ticker, lower_price, volume / price
                )
                self.logger.info(f"Order [{buy_order['uuid']}] opened.")
                break

            lower_price = get_lower_price(lower_price)

        upper_price = price
        while True:
            ratio = self.calc_ratio(upper_price)
            value = self.quantity * upper_price + self.cash
            volume = value * ratio - self.cash

            if (
                volume > 5001
                and abs(self.last_price - upper_price) / self.last_price >= 0.005
            ):
                self.logger.info(
                    f"Sell {volume / upper_price:.2f} at {upper_price} (₩{volume:.2f})."
                )
                sell_order = self.broker.sell_limit_order(
                    self.ticker, upper_price, volume / price
                )
                self.logger.info(f"Order [{sell_order['uuid']}] opened.")
                break

            upper_price = get_upper_price(upper_price)

        return buy_order["uuid"], sell_order["uuid"], lower_price, upper_price

    @handle_errors
    def wait_any_closed(self, buy_uuid, sell_uuid):
        while self.running:
            buy_closed = self.broker.check_order_closed(buy_uuid)
            if buy_closed:
                return True

            sell_closed = self.broker.check_order_closed(sell_uuid)
            if sell_closed:
                return False

            time.sleep(3)

    @handle_errors
    def wait_all_closed(self, buy_uuid, sell_uuid):
        while not (
            self.broker.check_order_closed(buy_uuid)
            and self.broker.check_order_closed(sell_uuid)
        ):
            time.sleep(0.5)

    @handle_errors
    def calc_ratio(self, price):
        delta = price / self.pivot_price - 1
        if delta == 0:
            ratio = 0.5
        elif delta < 0:
            ratio = 0.5 * delta**2 + delta + 0.5
        else:
            ratio = -0.5 * 2**-delta + 1
        return ratio

    @handle_errors
    def terminate(self) -> None:
        self.logger.info("Terminating TradingBot...")
        self.running = False

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
