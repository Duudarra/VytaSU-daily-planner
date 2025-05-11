from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from models import Schedule
from schemas import ScheduleOut
from sqlalchemy import cast, Date
from datetime import date
from typing import List
import logging

# Настройка логирования для вывода в stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def get_schedule_by_date_and_group(session: AsyncSession, date: date, name_group: str) -> List[ScheduleOut]:
    logger.info(f"Запрос расписания для группы {name_group!r} на {date}")
    result = await session.execute(
        select(Schedule).filter(Schedule.date == date, Schedule.name_group == name_group)
    )
    schedules = result.scalars().all()
    logger.info(f"Найдено {len(schedules)} записей: {schedules}")
    return [ScheduleOut.from_orm(schedule) for schedule in schedules]

async def get_schedule_by_date_and_teacher(session: AsyncSession, date: date, name_teacher: str) -> List[ScheduleOut]:
    logger.info(f"Запрос расписания для преподавателя {name_teacher!r} на {date}")
    result = await session.execute(
        select(Schedule).filter(Schedule.date == date, Schedule.name_teacher == name_teacher)
    )
    schedules = result.scalars().all()
    logger.info(f"Найдено {len(schedules)} записей: {schedules}")
    return [ScheduleOut.from_orm(schedule) for schedule in schedules]

async def get_schedule_by_group_and_date_range(session: AsyncSession, name_group: str, start_date: date, end_date: date) -> List[ScheduleOut]:
    logger.info(f"Запрос расписания для группы {name_group!r} с {start_date} по {end_date}")
    result = await session.execute(
        select(Schedule).filter(
            Schedule.name_group == name_group,
            Schedule.date.between(start_date, end_date)
        ).order_by(Schedule.date, Schedule.time_lesson)
    )
    schedules = result.scalars().all()
    logger.info(f"Найдено {len(schedules)} записей: {schedules}")
    return [ScheduleOut.from_orm(schedule) for schedule in schedules]

async def get_schedule_by_teacher_and_date_range(session: AsyncSession, name_teacher: str, start_date: date, end_date: date) -> List[ScheduleOut]:
    logger.info(f"Запрос расписания для преподавателя {name_teacher!r} с {start_date} по {end_date}")
    result = await session.execute(
        select(Schedule).filter(
            Schedule.name_teacher == name_teacher,
            Schedule.date.between(start_date, end_date)
        ).order_by(Schedule.date, Schedule.time_lesson)
    )
    schedules = result.scalars().all()
    logger.info(f"Найдено {len(schedules)} записей: {schedules}")
    return [ScheduleOut.from_orm(schedule) for schedule in schedules]

async def delete_old_schedules(session: AsyncSession, cutoff_date: date):
    logger.info(f"Удаление расписания до {cutoff_date}")
    await session.execute(delete(Schedule).where(Schedule.date < cutoff_date))
    await session.commit()
    logger.info("Старые записи удалены")
