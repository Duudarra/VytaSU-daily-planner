from pydantic import BaseModel
from datetime import date, time, datetime

class ScheduleBase(BaseModel):
    date: date  # Дата, например, '2025-05-13'
    name_group: str  # Группа, например, '101' или 'ИЭ-2025'
    time_lesson: str  # Изменено с time
    name_discipline: str  # Изменено с subject
    name_teacher: str  # Изменено с teacher
    cabinet_number: str  # Изменено с cabinet

class ScheduleCreate(ScheduleBase):
    pass

class ScheduleOut(ScheduleBase):
    id: int

    class Config:
        orm_mode = True
