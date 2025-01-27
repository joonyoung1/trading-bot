import asyncio
import signal

from telegram_bot import TelegramBot
from trading_bot import TradingBot
from data_processor import DataProcessor
from tracker import Tracker
from broker import Broker


class Manager:
    def __init__(self) -> None:
        self.broker = Broker()
        self.tracker = Tracker()
        self.trading_bot = TradingBot(self.broker, self.tracker)
        self.data_processor = DataProcessor(self.broker, self.tracker)
        self.telegram_bot = TelegramBot(self.trading_bot, self.data_processor)

    async def run(self) -> None:
        stop_event = asyncio.Event()

        def signal_handler() -> None:
            stop_event.set()

        loop = asyncio.get_running_loop()
        for sig in [signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT]:
            loop.add_signal_handler(sig, signal_handler)

        try:
            self.broker.set_loop(loop)
            await self.telegram_bot.start()
            await self.trading_bot.initialize()
            asyncio.create_task(self.trading_bot.start())

            await stop_event.wait()

        finally:
            await self.trading_bot.stop()
            await self.telegram_bot.stop()
