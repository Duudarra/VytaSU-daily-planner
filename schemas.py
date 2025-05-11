from pydantic import BaseModel
from datetime import date
from typing import Optional

class ScheduleOut(BaseModel):
    id: int
    date: date
    time_lesson: str
    cabinet_number: str
    name_group: str
    name_teacher: str
    name_discipline: str

    class Config:
        orm_mode = True

class UserCreate(BaseModel):
    email: str
    password: str
    name: str

class UserOut(BaseModel):
    id: int
    email: str
    name: str
    is_active: bool

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str