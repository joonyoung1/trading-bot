import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from .base import Base
from constants import ConfigKeys

database_path = os.path.join(os.getenv(ConfigKeys.DATA_DIR), "app.db")
DATABASE_URL = f"sqlite+aiosqlite:///{database_path}"

engine = create_async_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal: sessionmaker[AsyncSession] = sessionmaker(
    bind=engine, class_=AsyncSession
)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
