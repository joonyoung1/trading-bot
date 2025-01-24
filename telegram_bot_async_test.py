from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import os
from dotenv import load_dotenv

import asyncio


class TradingBot:
    def __init__(self):
        self.running = False

    async def run(self):
        self.running = True
        while self.running:
            await asyncio.sleep(1)
            print("running...")

    async def stop(self):
        self.running = False

    async def get_status(self):
        return "status"


trading_bot = TradingBot()


load_dotenv()
TOKEN = os.getenv("TOKEN")

reply_keyboard = [["📊 Dashboard"]]
markup = ReplyKeyboardMarkup(
    reply_keyboard, one_time_keyboard=False, resize_keyboard=True
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Telegram Bot Activated.", reply_markup=markup)


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Telegram Bot Deactivated.", reply_markup=ReplyKeyboardRemove()
    )


async def handle_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = await trading_bot.get_status()
    await update.message.reply_text(response)


async def main() -> None:
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_command)
    )

    async with application:
        await application.start()
        await application.updater.start_polling()
        await trading_bot.run()

        await application.updater.stop()
        await application.stop()


if __name__ == "__main__":
    asyncio.run(main())
