# schemas/form.py

from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List, Dict, Any


class FormPropertyCRUDModel(BaseModel):
    property_type: str
    label: str
    key: str
    description: str

class FormPropertyCRUDModelOptional(BaseModel):
    property_type: Optional[str] = None
    label: Optional[str] = None
    key: Optional[str] = None
    description: Optional[str] = None

class CreateFormPropertiesRequest(BaseModel):
    user_id: str
    form_id: str
    properties: List[FormPropertyCRUDModel] = []

class CreateFormPropertiesResponse(BaseModel):
    properties: List[FormPropertyCRUDModel] = []

class CreateFormRequest(BaseModel):
    name: str
    description: Optional[str] = None

class UpdateFormRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class CreateForm(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str] = None
    form_propeties: List[str] = []

class CreateFormResponseRequest(BaseModel):
    values: Dict[str, Any]
