# schemas/form.py

from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from datetime import datetime

class CreateForm(BaseModel):
    name: str
    description: str

class FormPropertyManageModel(BaseModel):
    id: Optional[UUID] = None
    property_type: Optional[str] = None
    options: Optional[List[str]] = None  # Updated to be a list of strings
    position: Optional[int] = None
    label: Optional[str] = None
    key: Optional[str] = None
    required: Optional[bool] = True

class UpdateForm(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    properties: List[FormPropertyManageModel]

class FormPropertyModel(BaseModel):
    id: UUID
    user_id: UUID
    form_id: UUID
    property_type: str
    options: Optional[List[str]] = None  # Updated to be a list of strings
    position: int
    label: str
    key: str
    required: bool

class FormPropertyModelPublic(BaseModel):
    id: UUID
    property_type: str
    options: Optional[List[str]] = None
    position: int
    label: str
    key: str
    required: bool

class FormModel(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: str
    form_properties_ids: List[UUID] = []
    properties: List[FormPropertyModel] = []

class FormModelPublic(BaseModel):
    id: UUID
    name: str
    description: str
    properties: List[FormPropertyModel] = []

class FormWithoutProperties(BaseModel):
    id: UUID
    name: str



class FormResponseMessageCreate(BaseModel):
    response_id: UUID
    user_id: UUID
    message: str

class FormResponseMessageUpdate(BaseModel):
    message: Optional[str] = None

class FormResponseMessagePublic(BaseModel):
    id: UUID
    response_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    message: str
    editable_until: datetime
    
class UpdateContactLabels(BaseModel):
    labels: List[str]

class TermsAndConditions(BaseModel):
    registration_no: str
    contact_email: str
    contact_phone: str
    form_properties: List[str] = []

class PublicOptions(BaseModel):
    property_name: str
    form_name: str
    options: List[str]