import asyncio
import os

from telegram_bot import TelegramBot
from trading_bot import TradingBot


class Manager:
    def __init__(self):
        self.trading_bot = TradingBot()
        self.telegram_bot = TelegramBot(self.trading_bot.get_status)

    async def run(self):
        try:
            await self.telegram_bot.start()
            await self.trading_bot.initialize()
            print("initialized")
            await self.trading_bot.start()

            await asyncio.Event().wait()

        except KeyboardInterrupt:
            print("Interrupted")

        finally:
            await self.trading_bot.stop()
            await self.telegram_bot.stop()
