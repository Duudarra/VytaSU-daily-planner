from models import async_session
from models import Schedule
from sqlalchemy import select, update, delete
import datetime


def connection(func):
    async def wrapper(*args, **kwargs):
        async with async_session() as session:
            return await func(session, *args, **kwargs)

    return wrapper


@connection
async def delete_outdated_schedules(session):
    two_weeks_ago = datetime.datetime.now().date() - datetime.timedelta(weeks=2)

    result = await session.execute(select(Schedule))

    old_schedules = result.scalars().all()

    for schedule in old_schedules:
        schedule_date = datetime.datetime.strptime(schedule.date, "%d.%m.%y").date()
        if schedule_date <= two_weeks_ago:
            await session.delete(schedule)

    await session.commit()


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
):
    query = select(Schedule).where(
        Schedule.date == date,
        Schedule.time_lesson == time_lesson,
        Schedule.cabinet_number == cabinet_number,
    )
    data = (await session.execute(query)).scalars().all()

    if empty:
        # если записи есть, то удаляем их
        if data:
            delete_query = delete(Schedule).where(
                Schedule.date == date,
                Schedule.time_lesson == time_lesson,
                Schedule.cabinet_number == cabinet_number,
            )
            await session.execute(delete_query)
            await session.commit()

    # если пара есть сейчас, то нужно заменить( если есть) или добавить( если нет)
    else:
        # если нет старых записей, то добавляем все группы на паре
        if not data:
            for i in range(len(name_of_group)):
                new_record = Schedule(
                    date=date,
                    time_lesson=time_lesson,
                    cabinet_number=cabinet_number,
                    name_group=name_of_group[i],
                    name_teacher=name_teacher[i],
                    name_discipline=name_of_discipline[i],
                )
                session.add(new_record)
            await session.commit()

        # если есть записи
        else:
            # если добавляется много записей, то удаляем все старые и добавляем все новые
            if many:
                delete_query = delete(Schedule).where(
                    Schedule.date == date,
                    Schedule.time_lesson == time_lesson,
                    Schedule.cabinet_number == cabinet_number,
                )
                await session.execute(delete_query)
                await session.commit()

                for i in range(len(name_of_group)):
                    new_record = Schedule(
                        date=date,
                        time_lesson=time_lesson,
                        cabinet_number=cabinet_number,
                        name_group=name_of_group[i],
                        name_teacher=name_teacher[i],
                        name_discipline=name_of_discipline[i],
                    )
                    session.add(new_record)
                await session.commit()

            # если добавляется одна запись
            else:
                # если запись всего одна в бд, то просто заменяем
                if len(data) == 1:
                    update_query = (
                        update(Schedule)
                        .where(
                            Schedule.date == date,
                            Schedule.time_lesson == time_lesson,
                            Schedule.cabinet_number == cabinet_number,
                        )
                        .values(
                            name_group=name_of_group[0],
                            name_teacher=name_teacher[0],
                            name_discipline=name_of_discipline[0],
                        )
                    )
                    await session.execute(update_query)
                    await session.commit()

                # если записей много в бд, но добавляется одна
                else:
                    # удаляем все
                    delete_query = delete(Schedule).where(
                        Schedule.date == date,
                        Schedule.time_lesson == time_lesson,
                        Schedule.cabinet_number == cabinet_number,
                    )
                    await session.execute(delete_query)
                    await session.commit()

                    # добавляем одну запись
                    new_record = Schedule(
                        date=date,
                        time_lesson=time_lesson,
                        cabinet_number=cabinet_number,
                        name_group=name_of_group[0],
                        name_teacher=name_teacher[0],
                        name_discipline=name_of_discipline[0],
                    )
                    session.add(new_record)
                    await session.commit()