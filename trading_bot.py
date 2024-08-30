from broker import Broker
from logging import Logger
from multiprocessing import Queue


class TradingBot:
    SENTINEL = object()

    def __init__(
        self, ticker: str, queue: Queue, broker: Broker, logger: Logger
    ) -> None:
        self.ticker: str = ticker
        self.queue: Queue = queue
        self.broker: Broker = broker
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
        self.cash = self.broker.get_balance("KRW")
        self.quantity = self.broker.get_balance(self.ticker)
        self.logger.info(f"Cash: ₩{self.cash}, Assets: {self.quantity} units.")

    def process_trade(self, price: float) -> None:
        print("price", price)
        asset_value = price * self.quantity
        volume = abs(self.cash - asset_value) / 2
        print("volume", volume)
        if volume < 5001:
            return

        ratio = asset_value / asset_value + self.cash
        if ratio < 0.5:
            self.buy(price, volume / price)
        elif ratio > 0.505:
            self.sell(price, volume / price)

    def buy(self, price: float, quantity: float) -> None:
        self.logger.info(f"Buy {quantity} at {price} (₩{price * quantity}).")

        order = self.broker.buy_limit_order(self.ticker, price, quantity)
        uuid = order["uuid"]
        self.logger.info(f"Order [{uuid}] opened.")

        self.wait(uuid)

    def sell(self, price: float, quantity: float) -> None:
        self.logger.info(f"Sell {quantity} at {price} (₩{price * quantity}).")

        order = self.broker.sell_limit_order(self.ticker, price, quantity)
        uuid = order["uuid"]
        self.logger.info(f"Order [{uuid}] opened.")

        self.wait(uuid)
    
    def wait(self, uuid: str) -> None:
        closed = self.broker.wait_order_close(uuid)
        if closed:
            self.logger.info(f"Order [{uuid}] has been closed.")
        else:
            self.logger.info(f"Canceling all open orders...")
            self.broker.cancel_orders(self.ticker)
            self.logger.info(f"All open orders have been canceled.")
