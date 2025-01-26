import asyncio
import signal

from telegram_bot import TelegramBot
from trading_bot import TradingBot


class Manager:
    def __init__(self) -> None:
        self.trading_bot = TradingBot()
        self.telegram_bot = TelegramBot(self.trading_bot.get_status)

    async def run(self) -> None:
        stop_event = asyncio.Event()

        def signal_handler() -> None:
            stop_event.set()

        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, signal_handler)
        loop.add_signal_handler(signal.SIGTERM, signal_handler)
        loop.add_signal_handler(signal.SIGHUP, signal_handler)
        loop.add_signal_handler(signal.SIGQUIT, signal_handler)

        try:
            await self.telegram_bot.start()
            await self.trading_bot.initialize()
            asyncio.create_task(self.trading_bot.start())

            await stop_event.wait()

        finally:
            await self.trading_bot.stop()
            await self.telegram_bot.stop()
