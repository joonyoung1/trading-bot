import os
import asyncio
import logging
from logging.handlers import RotatingFileHandler

from app import Manager, init_db
from config import Env


def setting_logger() -> None:
    log_dir = Env.LOG_DIR
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
