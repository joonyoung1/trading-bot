import asyncio


class TradingBot:
    def __init__(self) -> None:
        self.running = False

    async def start(self) -> None:
        self.running = True
        while self.running:
            await asyncio.sleep(1)
            print("running...")

    async def stop(self) -> None:
        self.running = False

    async def get_status(self) -> bool:
        return self.running
