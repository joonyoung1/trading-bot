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
PIVOT = float(os.getenv("PIVOT"))


class Manager:
    def __init__(
        self,
        log_file: str = "logfile.log",
        history_file: str = "history.csv",
        plot_folder: str = "./plots",
    ) -> None:
        self.log_file: str = log_file

        self.logger = self.init_logger()
        self.brocker = Broker(ACCESS, SECRET)
        self.tracker = Tracker(history_file, plot_folder)

        self.chat_bot = ChatBot(TOKEN, CHAT_ID, self.tracker)
        self.trading_bot = TradingBot(
            TICKER,
            self.brocker,
            self.chat_bot,
            self.logger,
            pivot_price=PIVOT,
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
        signal.signal(signal.SIGINT, self.terminate)
        signal.signal(signal.SIGTERM, self.terminate)

        self.trading_bot.start()

    def terminate(self, signum, frame) -> None:
        self.logger.info("Termination signal received. Cleaning up...")
        self.trading_bot.terminate()


if __name__ == "__main__":
    manager = Manager()
    try:
        manager.start()
    except Exception as e:
        manager.terminate(None, None)
