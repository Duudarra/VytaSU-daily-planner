from sqlalchemy import Column, Integer, String, Date, Time, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    time_lesson = Column(Time, nullable=False)
    name_discipline = Column(String, nullable=False)
    name_teacher = Column(String, nullable=False)
    name_group = Column(String, nullable=False)
    cabinet_number = Column(String, nullable=False)
