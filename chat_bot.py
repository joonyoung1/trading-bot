from telegram import Bot
import threading
import asyncio

from tracker import Tracker


class ChatBot:
    def __init__(self, token: str, chat_id: str, tracker: Tracker) -> None:
        self.chat_id: str = chat_id
        self.bot: Bot = Bot(token)
        self.tracker: Tracker = tracker

        self.loop = asyncio.new_event_loop()
        self.asyncio_thread = threading.Thread(target=self.start_loop, daemon=True)

    def start(self) -> None:
        self.asyncio_thread.start()

    def start_loop(self) -> None:
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
    
    def terminate(self) -> None:
        if self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        self.asyncio_thread.join()

    def notify(
        self, price: float, cash: float, quantity: float, volume: float | None = None
    ):
        balance = quantity * price + cash
        self.tracker.record_history(price, balance)

        if volume is not None:
            trade_type = "Sold" if volume < 0 else "Bought"
            trade_amount = abs(volume) / price
            message = f"{trade_type} {trade_amount:.2f} at {price:.2f}"
            self.loop.call_soon_threadsafe(
                asyncio.create_task, self.send_message(message)
            )

        message = (
            f"Cash: ₩{cash:.2f}\n"
            f"Assets: {quantity:.2f}\n"
            f"Price: {price:.2f}\n"
            f"Total: ₩{balance:.2f}\n"
        )
        self.loop.call_soon_threadsafe(
            asyncio.create_task, self.send_message(message)
        )

        file = self.tracker.generate_history_graph()
        self.loop.call_soon_threadsafe(
            asyncio.create_task, self.send_file(file)
        )

    async def send_message(self, message: str) -> None:
        await self.bot.send_message(self.chat_id, message)

    async def send_file(self, file: str) -> None:
        await self.bot.send_document(self.chat_id, file)
