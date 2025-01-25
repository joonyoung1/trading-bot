import asyncio
import logging.handlers
from manager import Manager
from dotenv import load_dotenv
import logging


def setting_logger() -> None:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.handlers.RotatingFileHandler(
                "app.log", maxBytes=1024 * 1024 * 5, backupCount=3
            )
        ],
    )


if __name__ == "__main__":
    load_dotenv()
    setting_logger()

    manager = Manager()
    asyncio.run(manager.run())
