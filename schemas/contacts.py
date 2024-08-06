from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List

class FormCreate(BaseModel):
    name: str
    description: str
    form_properties: List[str] = []

class FormUpdate(BaseModel):
    name: str
    description: str
    form_properties: List[str] = []

class Form(BaseModel):
    id: UUID
    user_id: UUID
    form_properties: List[str] = [] 
    name: str
    description: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ContactCreate(BaseModel):
    name: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    job: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    preffered_contact_method: Optional[str] = None
    preffered_contact_time: Optional[str] = None
    secondary_email: Optional[str] = None
    secondary_phone: Optional[str] = None
    referral_source: Optional[str] = None
    notes: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    initial_message: Optional[str] = None
    description: Optional[str] = None
    agreed_to_privacy_policy: Optional[bool] = False
    agreed_to_news_letter: Optional[bool] = False
    labels: List[str] = []
    has_read_initial_message: Optional[bool] = False

class ContactUpdate(BaseModel):
    name: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    job: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    preffered_contact_method: Optional[str] = None
    preffered_contact_time: Optional[str] = None
    secondary_email: Optional[str] = None
    secondary_phone: Optional[str] = None
    referral_source: Optional[str] = None
    notes: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    initial_message: Optional[str] = None
    description: Optional[str] = None
    agreed_to_privacy_policy: Optional[bool]
    agreed_to_news_letter: Optional[bool]
    has_read_initial_message: Optional[bool]
    labels: List[str] = []

class Contact(BaseModel):
    id: UUID
    user_id: UUID
    form_id: UUID
    name: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    job: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    preffered_contact_method: Optional[str] = None
    preffered_contact_time: Optional[str] = None
    secondary_email: Optional[str] = None
    secondary_phone: Optional[str] = None
    referral_source: Optional[str] = None
    notes: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    initial_message: Optional[str] = None
    description: Optional[str] = None
    agreed_to_privacy_policy: bool
    agreed_to_news_letter: bool
    has_read_initial_message: bool
    created_at: datetime
    updated_at: datetime
    labels: List[str] = []

    class Config:
        from_attributes = True

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

class UpdateContactLabels(BaseModel):
    labels: List[str]

class UpdateDescription(BaseModel):
    description: str
