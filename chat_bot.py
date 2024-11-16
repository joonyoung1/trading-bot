import asyncio

from tracker import Tracker
from telegram import Telegram


class ChatBot:
    def __init__(self, token: str, chat_id: str, tracker: Tracker) -> None:
        self.chat_id: str = chat_id
        self.telegram: Telegram = Telegram(token, chat_id)
        self.tracker: Tracker = tracker

    def notify(self, price: float, cash: float, quantity: float):
        balance = quantity * price + cash
        self.tracker.record_history(price, balance)

        self.telegram.send_message(
            f"Cash: ₩{cash:.2f}\n"
            f"Assets: {quantity:.2f}\n"
            f"Price: {price:.2f}\n"
            f"Total: ₩{balance:.2f}\n"
        )

        file_path = self.tracker.generate_history_graph()
        self.telegram.send_photo(file_path)

    def alert(self, message: str) -> None:
        self.telegram.send_message(message)
