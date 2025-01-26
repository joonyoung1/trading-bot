import asyncio
import os
from typing import Callable

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from utils import retry


class TelegramBot:
    def __init__(self, get_trading_bot_data: Callable[[], bool]) -> None:
        self.TOKEN = os.getenv("TOKEN")

        self.application = Application.builder().token(self.TOKEN).build()
        self.get_trading_bot_data = get_trading_bot_data

        reply_keyboard = [["📊 Dashboard"]]
        self.markup = ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=False, resize_keyboard=True
        )

        self.application.add_handler(CommandHandler("start", self.start_handler))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler)
        )

    @retry()
    async def start_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        await update.message.reply_text(
            "Telegram Bot Activated.",
            reply_markup=self.markup,
        )

    @retry()
    async def message_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        is_trading_bot_running = self.get_trading_bot_data()
        await update.message.reply_text(
            f"Trading Bot Running Status : {is_trading_bot_running}",
            reply_markup=self.markup,
        )

    async def start(self) -> None:
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()

    async def stop(self) -> None:
        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()
