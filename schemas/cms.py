# schemas/cms.py

from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List, Dict, Any
from datetime import datetime

class RootContentLight(BaseModel):
    id: str
    alias: Optional[str]
    is_root: bool
    
class ContentUpdate(BaseModel):
    position: Optional[int] = None
    alias: Optional[str] = None

    content_type: Optional[str] = None
    text: Optional[str] = None
    image: Optional[str] = None
    html: Optional[str] = None
    list_text_content: Optional[List[str]] = None
    item_content: Optional[List[UUID]] = None
    list_item_content: Optional[List[List[UUID]]] = None

    class Config:
        form_attributes = True

class ItemContentProperty(BaseModel):
    content_id: UUID
    id: UUID
    key: Optional[str]

    class Config:
        form_attributes = True  # Umožňuje pracovat se SQLAlchemy modely

class BaseContent(BaseModel):
    id: UUID
    user_id: UUID
    position: int
    content_type: Optional[str] = None
    text: Optional[str] = None
    image: Optional[str] = None
    html: Optional[str] = None
    list_text_content: Optional[List[str]] = None
    item_content: Optional[List[UUID]] = None
    list_item_content: Optional[List[List[UUID]]] = None

    class Config:
        form_attributes = True

class ContentWithProperties(BaseModel):
    id: UUID
    user_id: UUID
    position: int
    content_type: Optional[str]
    text: Optional[str]
    image: Optional[str]
    html: Optional[str]
    list_text_content: Optional[List[str]]
    item_content: Optional[List[ItemContentProperty]]  # Pole objektů properties
    list_item_content: Optional[List[List[ItemContentProperty]]]

    class Config:
        form_attributes = True  # Umožňuje pracovat se SQLAlchemy modely

class ReorderRequest(BaseModel):
    new_order: List[int]
 