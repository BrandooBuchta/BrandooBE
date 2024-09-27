from pydantic import BaseModel, validator
from uuid import UUID
from datetime import datetime, time
from typing import Optional, List

class StatisticCreate(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    type: str

class StatisticUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    type: Optional[str] = None

class StatisticValueCreate(BaseModel):
    time: Optional[str] = None  # Use str to accept time input as a string
    number: Optional[int] = None
    boolean: Optional[bool] = None
    text: Optional[str] = None

    @validator('time', pre=True, always=True)
    def validate_time(cls, v):
        if v is not None:
            try:
                datetime.strptime(v, '%H:%M:%S')
            except ValueError:
                raise ValueError('Time must be in the format HH:MM:SS')
        return v

class StatisticValue(BaseModel):
    id: UUID
    statistic_id: UUID
    created_at: datetime
    time: Optional[str]
    number: Optional[int]
    boolean: Optional[bool]
    text: Optional[str]

    @validator('time', pre=True, always=True)
    def serialize_time(cls, v):
        if isinstance(v, time):
            return v.strftime('%H:%M:%S')
        return v

    class Config:
        from_attributes = True

class Statistic(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    type: str
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    values: List['StatisticValue'] = []

    class Config:
        arbitrary_types_allowed = True

