import asyncio
from manager import Manager
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    manager = Manager()
    asyncio.run(manager.run())
