from models import async_session
from models import Schedule
from sqlalchemy import select, update, delete
import datetime
import logging

# Настройка логирования в stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def connection(func):
    async def wrapper(*args, **kwargs):
        async with async_session() as session:
            return await func(session, *args, **kwargs)
    return wrapper

@connection
async def delete_outdated_schedules(session):
    two_weeks_ago = datetime.datetime.now().date() - datetime.timedelta(weeks=2)
    
    result = await session.execute(
        delete(Schedule).where(Schedule.date < two_weeks_ago)
    )
    await session.commit()
    logger.info(f"Удалено {result.rowcount} устаревших записей")

@connection
async def update_schedule(
    session,
    date,
    time_lesson,
    cabinet_number,
    name_of_group,
    name_teacher,
    name_of_discipline,
    *,
    empty=False,
    many=False,
    department=None
):
    if isinstance(date, str):
        try:
            if len(date) == 8 and '.' in date:
                date = datetime.datetime.strptime(date, "%d.%m.%y").date()
            else:
                date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError as e:
            logger.error(f"Ошибка формата даты: {date}, {e}")
            raise ValueError(f"Неверный формат даты: {date}")

    logger.info(f"Обновление расписания: date={date}, time_lesson={time_lesson}, cabinet_number={cabinet_number}, empty={empty}, many={many}, department={department}")
    
    query = select(Schedule).where(
        Schedule.date == date,
        Schedule.time_lesson == time_lesson,
        Schedule.cabinet_number == cabinet_number,
    )
    data = (await session.execute(query)).scalars().all()

    if empty:
        if data:
            delete_query = delete(Schedule).where(
                Schedule.date == date,
                Schedule.time_lesson == time_lesson,
                Schedule.cabinet_number == cabinet_number,
            )
            result = await session.execute(delete_query)
            await session.commit()
            logger.info(f"Удалено {result.rowcount} записей (empty=True)")
    else:
        if not data:
            for i in range(len(name_of_group)):
                new_record = Schedule(
                    date=date,
                    time_lesson=time_lesson,
                    cabinet_number=cabinet_number,
                    name_group=name_of_group[i] or "Unknown",
                    name_teacher=name_teacher[i] or "Unknown",
                    name_discipline=name_of_discipline[i] or "Unknown",
                    department=department
                )
                session.add(new_record)
            await session.commit()
            logger.info(f"Добавлено {len(name_of_group)} новых записей")
        else:
            if many:
                delete_query = delete(Schedule).where(
                    Schedule.date == date,
                    Schedule.time_lesson == time_lesson,
                    Schedule.cabinet_number == cabinet_number,
                )
                result = await session.execute(delete_query)
                await session.commit()
                logger.info(f"Удалено {result.rowcount} старых записей (many=True)")

                for i in range(len(name_of_group)):
                    new_record = Schedule(
                        date=date,
                        time_lesson=time_lesson,
                        cabinet_number=cabinet_number,
                        name_group=name_of_group[i] or "Unknown",
                        name_teacher=name_teacher[i] or "Unknown",
                        name_discipline=name_of_discipline[i] or "Unknown",
                        department=department
                    )
                    session.add(new_record)
                await session.commit()
                logger.info(f"Добавлено {len(name_of_group)} новых записей (many=True)")
            else:
                if len(data) == 1:
                    update_query = (
                        update(Schedule)
                        .where(
                            Schedule.date == date,
                            Schedule.time_lesson == time_lesson,
                            Schedule.cabinet_number == cabinet_number,
                        )
                        .values(
                            name_group=name_of_group[0] or "Unknown",
                            name_teacher=name_teacher[0] or "Unknown",
                            name_discipline=name_of_discipline[0] or "Unknown",
                            department=department
                        )
                    )
                    await session.execute(update_query)
                    await session.commit()
                    logger.info("Обновлена одна запись")
                else:
                    delete_query = delete(Schedule).where(
                        Schedule.date == date,
                        Schedule.time_lesson == time_lesson,
                        Schedule.cabinet_number == cabinet_number,
                    )
                    result = await session.execute(delete_query)
                    await session.commit()
                    logger.info(f"Удалено {result.rowcount} старых записей")

                    new_record = Schedule(
                        date=date,
                        time_lesson=time_lesson,
                        cabinet_number=cabinet_number,
                        name_group=name_of_group[0] or "Unknown",
                        name_teacher=name_teacher[0] or "Unknown",
                        name_discipline=name_of_discipline[0] or "Unknown",
                        department=department
                    )
                    session.add(new_record)
                    await session.commit()
                    logger.info("Добавлена одна новая запись")