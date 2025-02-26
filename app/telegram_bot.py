import os
import asyncio
from enum import StrEnum
from typing import TYPE_CHECKING
import textwrap

from jinja2 import Template
from telegram import ReplyKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from .utils import retry
from config import Env

if TYPE_CHECKING:
    from app.trading_bot import TradingBot
    from app.data_processor import DataProcessor


class TelegramBot:
    class Button(StrEnum):
        TOGGLE = "🔄 Toggle TradingBot"
        DASHBOARD = "📊 Dashboard"

    template = Template(
        textwrap.dedent(
            """\
            <code>&lt;Estimated Profit&gt;
              7D:  {{ format_value(profit_7d, True, 12, 0) }} {{ format_rate(profit_rate_7d, 12) }}
              3M:  {{ format_value(profit_3m, True, 12, 0) }} {{ format_rate(profit_rate_3m, 12) }}

            &lt;Balance&gt;
              Now: {{ format_value(balance, False, 12, 0) }}
              7D:  {{ format_value(balance_delta_7d, True, 12, 0) }} {{ format_rate(balance_rate_7d, 12) }}
              3M:  {{ format_value(balance_delta_3m, True, 12, 0) }} {{ format_rate(balance_rate_3m, 12) }}

            &lt;Price&gt;
              Now: {{ format_value(price, False, 12, 0) }}
              7D:  {{ format_value(price_delta_7d, True, 12, 0) }} {{ format_rate(price_rate_7d, 12) }}
              3M:  {{ format_value(price_delta_3m, True, 12, 0) }} {{ format_rate(price_rate_3m, 12) }}
            
            &lt;Fear & Greed Index&gt;
              score: {{ format_value(fgi_score, False, 13, 2) }}
              state: {{ format_text(fgi_text, 13) }}

            {{ n_trades }} trades in the last 7 days</code>
            """
        )
    )

    def __init__(
        self, trading_bot: "TradingBot", data_processor: "DataProcessor"
    ) -> None:
        self.trading_bot = trading_bot
        self.data_processor = data_processor

        self.TOKEN = Env.TOKEN
        self.application = Application.builder().token(self.TOKEN).build()
        self.execution_lock = asyncio.Lock()
        self.template_data = {
            "format_value": self.format_value,
            "format_rate": self.format_rate,
            "format_text": self.format_text,
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
    def format_value(
        value: float, with_sign: bool, rjust: int, decimals: int | None = None
    ) -> str:
        postfix = "+" if with_sign and value >= 0 else ""

        if decimals is None:
            formatted = f"{value:,}".rstrip("0").rstrip(".")
        else:
            formatted = f"{value:,.{decimals}f}"
        return f"{postfix}{formatted}".rjust(rjust)

    @staticmethod
    def format_rate(rate: float, rjust: int) -> str:
        if rate >= 0:
            return f"(🔺+{rate:.2f}%)".rjust(rjust)
        else:
            return f"(🔻{rate:.2f}%)".rjust(rjust)

    @staticmethod
    def format_text(text: str, rjust: int) -> str:
        return f"{text}".rjust(rjust)

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
            parse_mode=ParseMode.HTML,
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
