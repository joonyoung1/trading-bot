import asyncio
from manager import Manager

from dotenv import load_dotenv


if __name__ == "__main__":
    load_dotenv()
    manager = Manager()
    asyncio.run(manager.run())
