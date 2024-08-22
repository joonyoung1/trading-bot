import os
import asyncio
import telegram
from dotenv import load_dotenv

load_dotenv()


TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


async def send_message():
    bot = telegram.Bot(TOKEN)
    await bot.send_message(CHAT_ID, "response")


asyncio.run(send_message())
