from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import AsyncSessionLocal
from fastapi.security import OAuth2PasswordBearer
import crud, schemas
from models import User
from datetime import date, timedelta
from typing import List, AsyncGenerator
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pars import main as parser_main
import asyncio
from security import verify_password, create_access_token, decode_access_token

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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)) -> schemas.UserOut:
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await crud.get_user_by_email(session, email)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return schemas.UserOut.from_orm(user)

# Эндпоинты для задач
@app.post(
    "/tasks/",
    response_model=schemas.TaskOut,
    summary="Создать задачу",
    description="Создает новую задачу для текущего пользователя."
)
async def create_task(
    task: schemas.TaskCreate,
    current_user: schemas.UserOut = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"Создание задачи для пользователя: user_id={current_user.id}")
    # Передаем user_id из current_user, а не из тела запроса
    db_task = await crud.create_task(session, task, current_user.id)
    return db_task

@app.get(
    "/tasks/",
    response_model=List[schemas.TaskOut],
    summary="Получить задачи пользователя",
    description="Возвращает список задач текущего пользователя."
)
async def get_tasks(
    current_user: schemas.UserOut = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"Запрос задач для пользователя: user_id={current_user.id}")
    tasks = await crud.get_tasks_by_user(session, current_user.id)
    return tasks

@app.delete(
    "/tasks/{task_id}/",
    status_code=204,
    summary="Удалить задачу",
    description="Удаляет задачу по её ID, если она принадлежит текущему пользователю."
)
async def delete_task(
    task_id: int,
    current_user: schemas.UserOut = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"Удаление задачи: task_id={task_id}, user_id={current_user.id}")
    task = await crud.delete_task(session, task_id, current_user.id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found or not authorized")
    return

# Существующие эндпоинты
@app.post(
    "/register/",
    response_model=schemas.UserOut,
    summary="Регистрация нового пользователя",
    description="Создает нового пользователя с указанным email, паролем и именем."
)
async def register_user(user: schemas.UserCreate, session: AsyncSession = Depends(get_session)):
    logger.info(f"Регистрация пользователя: email={user.email}")
    existing_user = await crud.get_user_by_email(session, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = await crud.create_user(session, user)
    logger.info(f"Пользователь зарегистрирован: id={db_user.id}")
    return db_user

@app.post(
    "/login/",
    response_model=schemas.Token,
    summary="Вход пользователя",
    description="Аутентифицирует пользователя и возвращает JWT-токен."
)
async def login_user(email: str, password: str, session: AsyncSession = Depends(get_session)):
    logger.info(f"Попытка входа: email={email}")
    user = await crud.get_user_by_email(session, email)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    logger.info(f"Успешный вход: email={email}")
    return {"access_token": access_token, "token_type": "bearer"}

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
    # Закомментирован запуск парсера при старте
    # asyncio.create_task(parser_main()) пока отключен
    # Планируем парсер на 6:00 MSK ежедневно
    scheduler.add_job(
        parser_main,
        trigger=CronTrigger(hour=6, minute=0, timezone="Europe/Moscow"),
        id="daily_parser",
        replace_existing=True
    )
    scheduler.start()

@app.get(
    "/me/",
    response_model=schemas.UserOut,
    summary="Получить данные текущего пользователя",
    description="Возвращает данные текущего пользователя на основе JWT-токена."
)
async def get_current_user_data(
    current_user: schemas.UserOut = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"Запрос данных пользователя: user_id={current_user.id}")
    return current_user

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