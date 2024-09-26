# schemas/form.py

from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from datetime import datetime

class FormResponseEventManageSchema(BaseModel):
    response_id: UUID
    user_id: UUID
    title: str  # Bude zašifrováno
    notes: Optional[str] = None  # Bude zašifrováno
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    all_day: bool
    links: Optional[str] = None
    address: Optional[str] = None
    files: Optional[List[str]] = []

    class Config:
        from_attributes = True

class FormResponseEventSchema(BaseModel):
    id: Optional[UUID] = None
    response_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    title: Optional[str] = None
    notes: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    all_day: Optional[bool] = None
    links: Optional[str] = None
    address: Optional[str] = None
    files: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

