import os
import sys
from dotenv import load_dotenv

load_dotenv()

import logging
from logging.handlers import RotatingFileHandler
from multiprocessing import Queue, Process
from pyupbit import WebSocketClient
import signal

from broker import Broker
from trading_bot import TradingBot
from chat_bot import ChatBot
from tracker import Tracker


ACCESS = os.getenv("ACCESS")
SECRET = os.getenv("SECRET")
TICKER = os.getenv("TICKER")

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


class Manager:
    def __init__(
        self,
        log_file: str = "logfile.log",
        history_file: str = "history.csv",
        plot_folder: str = "./plots",
    ) -> None:
        self.log_file: str = log_file

        self.queue = Queue()
        self.price_fetcher: Process = Process(
            target=WebSocketClient, args=("ticker", [TICKER], self.queue), daemon=True
        )

        self.logger = self.init_logger()
        self.brocker = Broker(ACCESS, SECRET)
        self.tracker = Tracker(history_file, plot_folder)
        initial_price = self.tracker.get_initial_price()

        self.chat_bot = ChatBot(TOKEN, CHAT_ID, self.tracker)
        self.trading_bot = TradingBot(
            TICKER,
            self.queue,
            self.brocker,
            self.chat_bot,
            self.logger,
            initial_price=initial_price,
        )

    def init_logger(self) -> logging.Logger:
        logger = logging.getLogger("logger")
        logger.setLevel(logging.DEBUG)

        handler = RotatingFileHandler(
            self.log_file, maxBytes=1024 * 1024 * 5, backupCount=3
        )
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def start(self) -> None:
        self.logger.info("Starting PriceFetcher...")
        self.price_fetcher.start()
        self.logger.info("PriceFetcher started.")

        signal.signal(signal.SIGINT, self.terminate)
        signal.signal(signal.SIGTERM, self.terminate)

        self.trading_bot.start()

    def terminate(self, signum, frame) -> None:
        self.logger.info("Termination signal received. Cleaning up...")

        self.logger.info("Terminating PriceFetcher...")
        self.price_fetcher.terminate()
        self.price_fetcher.join()
        self.logger.info("PriceFetcher terminated.")

        self.trading_bot.terminate()

        self.price_fetcher.join()


if __name__ == "__main__":
    manager = Manager()

    try:
        manager.start()
    except Exception as e:
        manager.terminate(None, None)
