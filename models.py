from sqlalchemy import String, Integer, Date
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, AsyncSession, create_async_engine
import asyncio
import logging
import os
import datetime 

# Настройка логирования в stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Получение DATABASE_URL из переменной окружения
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:1234@localhost:5432/schedule_db")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Настройка пула соединений
engine = create_async_engine(
    url=DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,
)

async_session = async_sessionmaker(engine, class_=AsyncSession)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)  # Изменено на Date
    time_lesson: Mapped[str] = mapped_column(String(50), nullable=False)
    cabinet_number: Mapped[str] = mapped_column(String(50), nullable=False)
    name_group: Mapped[str] = mapped_column(String(100), nullable=False)
    name_teacher: Mapped[str] = mapped_column(String(100), nullable=False)
    name_discipline: Mapped[str] = mapped_column(String(100), nullable=False)

async def async_main():
    max_retries = 5
    retry_delay = 10  # секунды
    for attempt in range(max_retries):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Успешно создана таблица schedules")
            return
        except Exception as e:
            logger.error(f"Ошибка подключения к базе данных (попытка {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                raise Exception(f"Не удалось подключиться к базе данных после {max_retries} попыток: {str(e)}")