from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import AsyncSessionLocal
import crud, schemas
from datetime import date
from typing import List, AsyncGenerator
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pars import main as parser_main
import asyncio

# Настройка логирования в stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Schedule API",
    description="API для получения расписания занятий по группам и преподавателям",
    version="1.0.0"
)

# Инициализация планировщика
scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

@app.get(
    "/schedule/by-date-group/",
    response_model=List[schemas.ScheduleOut],
    summary="Получить расписание по дате и группе",
    description="Возвращает расписание занятий для указанной группы на заданную дату."
)
async def get_schedule_by_date_group(
    date: date,
    name_group: str,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"Запрос расписания: date={date}, name_group={name_group!r}")
    result = await crud.get_schedule_by_date_and_group(session, date, name_group)
    logger.info(f"Найдено {len(result)} записей")
    return result

@app.get(
    "/schedule/by-date-teacher/",
    response_model=List[schemas.ScheduleOut],
    summary="Получить расписание по дате и преподавателю",
    description="Возвращает расписание занятий для указанного преподавателя на заданную дату."
)
async def get_schedule_by_date_teacher(
    date: date,
    name_teacher: str,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"Запрос расписания: date={date}, name_teacher={name_teacher!r}")
    result = await crud.get_schedule_by_date_and_teacher(session, date, name_teacher)
    logger.info(f"Найдено {len(result)} записей")
    return result

@app.get(
    "/schedule/by-range-group/",
    response_model=List[schemas.ScheduleOut],
    summary="Получить расписание по группе за период дат",
    description="Возвращает расписание занятий для указанной группы за указанный период дат."
)
async def get_schedule_by_group_range(
    name_group: str,
    start_date: date,
    end_date: date,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"Запрос расписания: name_group={name_group!r}, start_date={start_date}, end_date={end_date}")
    result = await crud.get_schedule_by_group_and_date_range(session, name_group, start_date, end_date)
    logger.info(f"Найдено {len(result)} записей")
    return result

@app.get(
    "/schedule/by-range-teacher/",
    response_model=List[schemas.ScheduleOut],
    summary="Получить расписание по преподавателю за период дат",
    description="Возвращает расписание занятий для указанного преподавателя за указанный период дат."
)
async def get_schedule_by_teacher_range(
    name_teacher: str,
    start_date: date,
    end_date: date,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"Запрос расписания: name_teacher={name_teacher!r}, start_date={start_date}, end_date={end_date}")
    result = await crud.get_schedule_by_teacher_and_date_range(session, name_teacher, start_date, end_date)
    logger.info(f"Найдено {len(result)} записей")
    return result

@app.delete(
    "/schedule/",
    summary="Удалить старое расписание",
    description="Удаляет записи расписания до указанной даты."
)
async def delete_old_schedule(before: date, session: AsyncSession = Depends(get_session)):
    logger.info(f"Удаление расписания до {before}")
    await crud.delete_old_schedules(session, before)
    logger.info("Записи удалены")
    return {"status": "deleted"}

@app.on_event("startup")
async def startup_event():
    logger.info("Запуск приложения и планировщика")
    # Запускаем парсер при старте для немедленного обновления
    # asyncio.create_task(parser_main()) пока отключен
    # Планируем парсер на 16:00 MSK ежедневно
    scheduler.add_job(
        parser_main,
        trigger=CronTrigger(hour=6, minute=00, timezone="Europe/Moscow"),
        id="daily_parser",
        replace_existing=True
    )
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Остановка приложения и планировщика")
    scheduler.shutdown()

# Эндпоинт для ручного запуска парсера
@app.post("/run-parser/", summary="Ручной запуск парсера", description="Запускает парсер для обновления расписания.")
async def run_parser():
    logger.info("Ручной запуск парсера")
    await parser_main()
    return {"message": "Парсер запущен"}