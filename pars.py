import asyncio
from models import async_main
from parsing import start_parsing
import logging


# Настройка логирования в stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    logger.info("Запуск парсера")
    await async_main()  # Инициализация базы данных
    await start_parsing()  # Запуск парсинга
    logger.info("Парсинг завершен")

if __name__ == "__main__":
    asyncio.run(main())
