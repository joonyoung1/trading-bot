import os
import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING
import textwrap

from jinja2 import Template
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

    template = Template(
        textwrap.dedent(
            """\
            Estimated Profit: {{ format_currency(profit) }} ({{ format_rate(profit_rate) }})

            Balance: {{ format_currency(balance) }} ({{ format_rate(balance_rate) }})
            Cash: {{ format_currency(cash) }} ({{ format_rate(cash_rate) }})
            Value: {{ format_currency(value) }} ({{ format_rate(value_rate) }})
            Quantity: {{ quantity }} ({{ format_rate(quantity_rate) }})
            Price: {{ format_currency(price) }} ({{ format_rate(price_rate) }})
            
            {{ n_trades }} trades executed (24h)
            """
        )
    )

    def __init__(
        self, trading_bot: "TradingBot", data_processor: "DataProcessor"
    ) -> None:
        self.trading_bot = trading_bot
        self.data_processor = data_processor

        self.TOKEN = os.getenv("TOKEN")
        self.application = Application.builder().token(self.TOKEN).build()
        self.execution_lock = asyncio.Lock()
        self.template_data = {
            "format_currency": self.format_currency,
            "format_rate": self.format_rate,
        }

        reply_keyboard = [[self.Button.TOGGLE, self.Button.DASHBOARD]]
        self.markup = ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=False, resize_keyboard=True
        )

        self.application.add_handler(CommandHandler("start", self.start_handler))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler)
        )

    @staticmethod
    def format_currency(value: float):
        return f"₩{value:,.0f}"

    @staticmethod
    def format_rate(rate: float):
        if rate > 0:
            return f"📈 +{rate:.2f}%"
        elif rate < 0:
            return f"📉 {rate:.2f}%"
        else:
            return f"⚖️ {rate:.2f}%"

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
        dashboard = await self.data_processor.process()
        await update.message.reply_photo(dashboard.trend, reply_markup=self.markup)

        self.template_data.update(**vars(dashboard.status))
        await update.message.reply_text(
            self.template.render(self.template_data),
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
