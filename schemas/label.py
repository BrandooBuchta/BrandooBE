# schemas/form.py

from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from datetime import datetime

class ContactLabel(BaseModel):
    id: UUID
    user_id: UUID
    color: str
    title: str
    created_at: datetime
    updated_at: datetime

class ContactLabelCreate(BaseModel):
    color: str
    title: str

class ContactLabelUpdate(BaseModel):
    color: str
    title: str
