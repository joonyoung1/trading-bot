import os
import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from utils import retry

if TYPE_CHECKING:
    from trading_bot import TradingBot
    from data_processor import DataProcessor


class TelegramBot:
    @dataclass(frozen=True)
    class Button:
        TOGGLE = "🔄 Toggle TradingBot"
        DASHBOARD = "📊 Dashboard"

    def __init__(
        self, trading_bot: "TradingBot", data_processor: "DataProcessor"
    ) -> None:
        self.trading_bot = trading_bot
        self.data_processor = data_processor

        self.TOKEN = os.getenv("TOKEN")
        self.application = Application.builder().token(self.TOKEN).build()
        self.execution_lock = asyncio.Lock()

        reply_keyboard = [[self.Button.TOGGLE, self.Button.DASHBOARD]]
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
        text = update.message.text

        if text == self.Button.TOGGLE:
            await self.toggle_handler(update, context)

        elif text == self.Button.DASHBOARD:
            await self.dashboard_handler(update, context)

    @retry()
    async def toggle_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        async with self.execution_lock:
            if self.trading_bot.is_running():
                await update.message.reply_text(
                    f"Terminating Trading Bot ...",
                    reply_markup=self.markup,
                )
                await self.trading_bot.stop()
                await update.message.reply_text(
                    f"Trading Bot Terminated",
                    reply_markup=self.markup,
                )

            elif self.trading_bot.is_terminated():
                await update.message.reply_text(
                    f"Starting Trading Bot ...",
                    reply_markup=self.markup,
                )
                await self.trading_bot.initialize()
                asyncio.create_task(self.trading_bot.start())
                await update.message.reply_text(
                    f"Trading Bot Started",
                    reply_markup=self.markup,
                )

    @retry()
    async def dashboard_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        trend_plot, n_recent_trades = await self.data_processor.process()
        await update.message.reply_photo(trend_plot, reply_markup=self.markup)
        await update.message.reply_text(
            f"{n_recent_trades} trades executed in the last 24 hours",
            reply_markup=self.markup,
        )

    async def start(self) -> None:
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()

    async def stop(self) -> None:
        await self.trading_bot.stop()

        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()
