from pydantic import BaseModel
from datetime import date

class ScheduleBase(BaseModel):
    date: date
    name_group: str
    time_lesson: str
    name_discipline: str
    name_teacher: str
    cabinet_number: str

class ScheduleCreate(ScheduleBase):
    pass

class ScheduleOut(ScheduleBase):
    id: int

    class Config:
        from_attributes = True
