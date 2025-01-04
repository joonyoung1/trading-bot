from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

reply_keyboard = [
    ["Start Engine", "Stop Engine"],
    ["Check Status", "Reset"]
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Telegram Bot Activated.",
        reply_markup=markup
    )


async def handle_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """사용자의 명령 처리."""
    user_input = update.message.text
    if user_input == "Start Engine":
        response = "🚀 Engine started successfully!"
    elif user_input == "Stop Engine":
        response = "🛑 Engine stopped successfully!"
    elif user_input == "Check Status":
        response = "📊 All systems are operational!"
    elif user_input == "Reset":
        response = "🔄 System reset completed!"
    else:
        response = "❓ Unknown command. Please use the buttons."

    await update.message.reply_text(response)


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Telegram Bot Deactivated.",
        reply_markup=ReplyKeyboardRemove()
    )


def main() -> None:
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_command))

    application.run_polling()


if __name__ == "__main__":
    main()
