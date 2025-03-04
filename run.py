import os
import asyncio
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler

load_dotenv()

from app import Manager, init_db
from constants import ConfigKeys


def setting_logger() -> None:
    log_dir = os.getenv(ConfigKeys.LOG_DIR, "logs")
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


async def main() -> None:
    setting_logger()
    manager = Manager()

    await init_db()
    await manager.run()


if __name__ == "__main__":
    asyncio.run(main())
