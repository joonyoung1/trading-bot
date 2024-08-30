from telegram import Bot
import asyncio


class ChatBot:
    def __init__(self, token: str, chat_id: str) -> None:
        self.chat_id = chat_id
        self.bot: Bot = Bot(token)

    def send_message(self, message: str) -> None:
        asyncio.run(self.bot.send_message(self.chat_id, message))
