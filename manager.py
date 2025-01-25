import asyncio
import os

from telegram_bot import TelegramBot
from trading_bot import TradingBot


TOKEN = os.getenv("TOKEN")


class Manager:
    def __init__(self):
        self.trading_bot = TradingBot()
        self.telegram_bot = TelegramBot(TOKEN, self.trading_bot.get_status)

    async def run(self):
        await self.telegram_bot.start()
        asyncio.create_task(self.trading_bot.start())

        await asyncio.Event().wait()

        await self.telegram_bot.stop()
