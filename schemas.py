from pydantic import BaseModel, ConfigDict
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

    model_config = ConfigDict(from_attributes=True)

class UserCreate(BaseModel):
    email: str
    password: str
    name: str

class UserOut(BaseModel):
    id: int
    email: str
    name: str
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TaskBase(BaseModel):
    title: str
    date: str
    time: str
    category: str
    priority: str
    user_id: int

class TaskCreate(TaskBase):
    pass

class TaskOut(TaskBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
