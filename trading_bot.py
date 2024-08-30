from broker import Broker
from logging import Logger
from chat_bot import ChatBot
from multiprocessing import Queue


class TradingBot:
    SENTINEL = object()

    def __init__(
        self, ticker: str, queue: Queue, broker: Broker, chat_bot: ChatBot, logger: Logger
    ) -> None:
        self.ticker: str = ticker
        self.queue: Queue = queue
        self.broker: Broker = broker
        self.chat_bot: ChatBot = chat_bot
        self.logger: Logger = logger

        self.cash: float = 0
        self.quantity: float = 0

        self.update_balance()
        self.broker.cancel_orders(self.ticker)
        self.logger.info("Trading bot initialized.")

    def start(self) -> None:
        self.logger.info("Trading bot started.")
        last_price = -1

        while True:
            data = self.queue.get()
            if data is self.SENTINEL:
                break

            price = data["trade_price"]
            if last_price != price:
                last_price = price
                self.process_trade(price)

    def terminate(self) -> None:
        self.logger.info("Trading bot terminated.")
        self.queue.put(self.SENTINEL)

    def update_balance(self) -> None:
        try:
            self.cash = self.broker.get_balance("KRW")
            self.quantity = self.broker.get_balance(self.ticker)
            self.logger.info(f"Cash: ₩{self.cash}, Assets: {self.quantity} units.")
        except Exception as e:
            self.logger.error(f"Failed to update balance: {e}")
            raise

    def process_trade(self, price: float) -> None:
        asset_value = price * self.quantity
        volume = abs(self.cash - asset_value) / 2
        if volume < 5001:
            return

        ratio = asset_value / asset_value + self.cash
        if ratio < 0.5:
            ret = self.buy(price, volume / price)
        elif ratio > 0.505:
            ret = self.sell(price, volume / price)
        
        if ret:
            self.update_balance()
            self.chat_bot.send_message(
                f"Cash: ₩{self.cash}"
                f"Assets: {self.quantity}"
                f"Price: {price}"
                f"Total: ₩{self.cash + self.quantity * price}"
            )

    def buy(self, price: float, quantity: float) -> bool:
        self.logger.info(f"Buy {quantity} at {price} (₩{price * quantity}).")

        try:
            order = self.broker.buy_limit_order(self.ticker, price, quantity)
            uuid = order["uuid"]
            self.logger.info(f"Order [{uuid}] opened.")
            return self.wait(uuid)
        except Exception as e:
            self.logger.error(f"Failed to place buy order: {e}")
            return False

    def sell(self, price: float, quantity: float) -> bool:
        self.logger.info(f"Sell {quantity} at {price} (₩{price * quantity}).")

        try:
            order = self.broker.sell_limit_order(self.ticker, price, quantity)
            uuid = order["uuid"]
            self.logger.info(f"Order [{uuid}] opened.")
            return self.wait(uuid)
        except Exception as e:
            self.logger.error(f"Failed to place sell order: {e}")
            return False

    def wait(self, uuid: str) -> bool:
        closed = self.broker.wait_order_close(uuid)
        if closed:
            self.logger.info(f"Order [{uuid}] has been closed.")
        else:
            self.logger.warning(
                f"Order [{uuid}] did not close within the expected time. Cancelling all open orders."
            )
            self.broker.cancel_orders(self.ticker)
            self.logger.info(f"All open orders have been canceled.")
        
        return closed
