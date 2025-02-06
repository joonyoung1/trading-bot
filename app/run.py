import os
import asyncio
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler

from .manager import Manager
from schemas import ConfigKeys


def setting_logger() -> None:
    log_dir = os.getenv(ConfigKeys.LOG_DIR, "log")
    os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            RotatingFileHandler(
                os.path.join(log_dir, "app.log"),
                maxBytes=1024 * 1024 * 5,
                backupCount=3,
            )
        ],
    )

    logging.getLogger("httpx").setLevel(logging.WARNING)


if __name__ == "__main__":
    load_dotenv()
    setting_logger()

    manager = Manager()
    asyncio.run(manager.run())
