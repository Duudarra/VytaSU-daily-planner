from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import AsyncSessionLocal
import crud, schemas
from typing import List
from datetime import date
from typing import AsyncGenerator

app = FastAPI(
    title="Schedule API",
    description="API для получения расписания занятий по группам и преподавателям",
    version="1.0.0"
)

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
    return await crud.get_schedule_by_date_and_group(session, date, name_group)

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
    return await crud.get_schedule_by_date_and_teacher(session, date, name_teacher)

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
    return await crud.get_schedule_by_group_and_date_range(session, name_group, start_date, end_date)

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
    return await crud.get_schedule_by_teacher_and_date_range(session, name_teacher, start_date, end_date)

@app.delete(
    "/schedule/",
    summary="Удалить старое расписание",
    description="Удаляет записи расписания до указанной даты."
)
async def delete_old_schedule(before: date, session: AsyncSession = Depends(get_session)):
    await crud.delete_old_schedules(session, before)
    return {"status": "deleted"}
