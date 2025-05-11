from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from models import Schedule
from schemas import ScheduleCreate
from sqlalchemy import cast, Date
from datetime import date
from typing import List
import logging

logging.basicConfig(filename="app.log", level=logging.INFO)

async def get_schedule_by_date_and_group(session: AsyncSession, date: date, name_group: str) -> List[Schedule]:
    logging.info(f"Запрос расписания для группы {name_group} на {date}")
    result = await session.execute(
        select(Schedule).filter(Schedule.date == date, Schedule.name_group == name_group)
    )
    schedules = result.scalars().all()
    logging.info(f"Найдено {len(schedules)} записей")
    return schedules

async def get_schedule_by_date_and_teacher(session: AsyncSession, date: date, name_teacher: str) -> List[Schedule]:
    logging.info(f"Запрос расписания для преподавателя {name_teacher} на {date}")
    result = await session.execute(
        select(Schedule).filter(Schedule.date == date, Schedule.name_teacher == name_teacher)
    )
    schedules = result.scalars().all()
    logging.info(f"Найдено {len(schedules)} записей")
    return schedules

async def get_schedule_by_group_and_date_range(session: AsyncSession, name_group: str, start_date: date, end_date: date) -> List[Schedule]:
    logging.info(f"Запрос расписания для группы {name_group} с {start_date} по {end_date}")
    result = await session.execute(
        select(Schedule).filter(
            Schedule.name_group == name_group,
            Schedule.date.between(start_date, end_date)
        ).order_by(Schedule.date, Schedule.time_lesson)
    )
    schedules = result.scalars().all()
    logging.info(f"Найдено {len(schedules)} записей")
    return schedules

async def get_schedule_by_teacher_and_date_range(session: AsyncSession, name_teacher: str, start_date: date, end_date: date) -> List[Schedule]:
    logging.info(f"Запрос расписания для преподавателя {name_teacher} с {start_date} по {end_date}")
    result = await session.execute(
        select(Schedule).filter(
            Schedule.name_teacher == name_teacher,
            Schedule.date.between(start_date, end_date)
        ).order_by(Schedule.date, Schedule.time_lesson)
    )
    schedules = result.scalars().all()
    logging.info(f"Найдено {len(schedules)} записей")
    return schedules

async def delete_old_schedules(session: AsyncSession, cutoff_date: date):
    logging.info(f"Удаление расписания до {cutoff_date}")
    await session.execute(delete(Schedule).where(Schedule.date < cutoff_date))
    await session.commit()
    logging.info("Старые записи удалены")
