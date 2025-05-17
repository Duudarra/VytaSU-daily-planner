from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from models import Schedule, User
from schemas import UserCreate, ScheduleOut
from security import get_password_hash
from sqlalchemy import cast, Date
from datetime import date, timedelta
from typing import List, Optional
import logging
import models, schemas

# Настройка логирования для вывода в stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def get_schedule_by_date_and_group(session: AsyncSession, date: date, name_group: str) -> List[ScheduleOut]:
    logger.info(f"Запрос расписания для группы {name_group!r} на {date}")
    result = await session.execute(
        select(Schedule).filter(Schedule.date == date, Schedule.name_group == name_group)
    )
    schedules = result.scalars().all()
    logger.info(f"Найдено {len(schedules)} записей")
    return [ScheduleOut.from_orm(schedule) for schedule in schedules]


async def get_schedule_by_date_and_teacher(session: AsyncSession, date: date, name_teacher: str) -> List[ScheduleOut]:
    logger.info(f"Запрос расписания для преподавателя {name_teacher!r} на {date}")
    result = await session.execute(
        select(Schedule).filter(Schedule.date == date, Schedule.name_teacher == name_teacher)
    )
    schedules = result.scalars().all()
    logger.info(f"Найдено {len(schedules)} записей")
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
    logger.info(f"Найдено {len(schedules)} записей")
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
    logger.info(f"Найдено {len(schedules)} записей")
    return [ScheduleOut.from_orm(schedule) for schedule in schedules]

async def get_schedule_by_date_and_department(session: AsyncSession, date: date, department: str) -> List[ScheduleOut]:
    logger.info(f"Запрос расписания для кафедры {department!r} на {date}")
    result = await session.execute(
        select(Schedule).filter(Schedule.date == date, Schedule.department == department)
    )
    schedules = result.scalars().all()
    logger.info(f"Найдено {len(schedules)} записей")
    return [ScheduleOut.from_orm(schedule) for schedule in schedules]

async def get_schedule_by_department(session: AsyncSession, department: str, start_date: date, end_date: date) -> List[ScheduleOut]:
    logger.info(f"Запрос расписания для кафедры {department!r} с {start_date} по {end_date}")
    result = await session.execute(
        select(Schedule).filter(
            Schedule.department == department,
            Schedule.date.between(start_date, end_date)
        ).order_by(Schedule.date, Schedule.time_lesson)
    )
    schedules = result.scalars().all()
    logger.info(f"Найдено {len(schedules)} записей")
    return [ScheduleOut.from_orm(schedule) for schedule in schedules]

async def get_schedule_by_date_department_teacher(session: AsyncSession, date: date, department: str, name_teacher: str) -> List[ScheduleOut]:
    logger.info(f"Запрос расписания для кафедры {department!r} и преподавателя {name_teacher!r} на {date}")
    result = await session.execute(
        select(Schedule).filter(
            Schedule.date == date,
            Schedule.department == department,
            Schedule.name_teacher == name_teacher
        )
    )
    schedules = result.scalars().all()
    logger.info(f"Найдено {len(schedules)} записей")
    return [ScheduleOut.from_orm(schedule) for schedule in schedules]

async def get_schedule_by_department_teacher_range(session: AsyncSession, department: str, name_teacher: str, start_date: date, end_date: date) -> List[ScheduleOut]:
    logger.info(f"Запрос расписания для кафедры {department!r} и преподавателя {name_teacher!r} с {start_date} по {end_date}")
    result = await session.execute(
        select(Schedule).filter(
            Schedule.department == department,
            Schedule.name_teacher == name_teacher,
            Schedule.date.between(start_date, end_date)
        ).order_by(Schedule.date, Schedule.time_lesson)
    )
    schedules = result.scalars().all()
    logger.info(f"Найдено {len(schedules)} записей")
    return [ScheduleOut.from_orm(schedule) for schedule in schedules]

async def get_free_cabinets(session: AsyncSession, date: date, time_lesson: str) -> List[str]:
    logger.info(f"Запрос свободных кабинетов на {date} в {time_lesson}")
    # Получаем все кабинеты
    all_cabinets_result = await session.execute(
        select(Schedule.cabinet_number).distinct()
    )
    all_cabinets = [row[0] for row in all_cabinets_result.fetchall()]
    
    # Получаем занятые кабинеты
    occupied_result = await session.execute(
        select(Schedule.cabinet_number).filter(
            Schedule.date == date,
            Schedule.time_lesson == time_lesson,
            Schedule.name_group != "Unknown"
        )
    )
    occupied_cabinets = [row[0] for row in occupied_result.fetchall()]
    
    # Свободные кабинеты
    free_cabinets = sorted(list(set(all_cabinets) - set(occupied_cabinets)))
    logger.info(f"Найдено {len(free_cabinets)} свободных кабинетов")
    return free_cabinets

async def get_free_cabinets_range(session: AsyncSession, start_date: date, end_date: date, time_lesson: str) -> List[dict]:
    logger.info(f"Запрос свободных кабинетов с {start_date} по {end_date} в {time_lesson}")
    results = []
    current_date = start_date
    while current_date <= end_date:
        free_cabinets = await get_free_cabinets(session, current_date, time_lesson)
        results.append({
            "date": current_date,
            "time_lesson": time_lesson,
            "free_cabinets": free_cabinets
        })
        current_date += timedelta(days=1)
    logger.info(f"Найдено свободных кабинетов для {len(results)} дат")
    return results

async def get_schedule_by_date_and_cabinet(session: AsyncSession, date: date, cabinet_number: str) -> List[ScheduleOut]:
    logger.info(f"Запрос расписания для кабинета {cabinet_number!r} на {date}")
    result = await session.execute(
        select(Schedule).filter(Schedule.date == date, Schedule.cabinet_number == cabinet_number)
    )
    schedules = result.scalars().all()
    logger.info(f"Найдено {len(schedules)} записей")
    return [ScheduleOut.from_orm(schedule) for schedule in schedules]

async def get_schedule_by_cabinet_range(session: AsyncSession, cabinet_number: str, start_date: date, end_date: date) -> List[ScheduleOut]:
    logger.info(f"Запрос расписания для кабинета {cabinet_number!r} с {start_date} по {end_date}")
    result = await session.execute(
        select(Schedule).filter(
            Schedule.cabinet_number == cabinet_number,
            Schedule.date.between(start_date, end_date)
        ).order_by(Schedule.date, Schedule.time_lesson)
    )
    schedules = result.scalars().all()
    logger.info(f"Найдено {len(schedules)} записей")
    return [ScheduleOut.from_orm(schedule) for schedule in schedules]

async def delete_old_schedules(session: AsyncSession, cutoff_date: date):
    logger.info(f"Удаление расписания до {cutoff_date}")
    await session.execute(delete(Schedule).where(Schedule.date < cutoff_date))
    await session.commit()
    logger.info("Старые записи удалены")

async def create_user(session: AsyncSession, user: UserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password, name=user.name)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user

async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    query = select(User).where(User.email == email)
    result = await session.execute(query)
    return result.scalars().first()

async def create_task(session: AsyncSession, task: schemas.TaskCreate, user_id: int) -> models.Task:
    db_task = models.Task(
        title=task.title,
        date=task.date,
        time=task.time,
        category=task.category,
        priority=task.priority,
        user_id=user_id
    )
    session.add(db_task)
    await session.commit()
    await session.refresh(db_task)
    return db_task

async def get_unique_departments(session: AsyncSession) -> List[str]:
    result = await session.execute(
        select(Schedule.department).distinct().where(Schedule.department != None)
    )
    departments = [row[0] for row in result.fetchall()]
    return departments

async def get_tasks_by_user(session: AsyncSession, user_id: int) -> list[models.Task]:
    result = await session.execute(select(models.Task).filter(models.Task.user_id == user_id))
    return result.scalars().all()

async def delete_task(session: AsyncSession, task_id: int, user_id: int) -> None:
    result = await session.execute(
        select(models.Task).filter(models.Task.id == task_id, models.Task.user_id == user_id)
    )
    task = result.scalars().first()
    if task is None:
        return None
    await session.delete(task)
    await session.commit()
    return task