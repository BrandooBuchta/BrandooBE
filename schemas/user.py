# schemas/user.py

from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    type: str
    web_url: str
    code: str

class UserUpdate(BaseModel):
    contact_email: str = None
    contact_phone: str = None
    registration_no: str = None
    email: EmailStr = None
    name: str = None
    type: str = None
    web_url: str = None

class User(BaseModel):
    id: UUID
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    registration_no: Optional[str] = None
    name: str
    email: EmailStr
    is_verified: bool
    type: str
    web_url: str
    created_at: datetime
    updated_at: datetime
    public_key: str
    encrypted_private_key: str

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: UUID
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    registration_no: Optional[str] = None
    name: str
    email: EmailStr
    is_verified: bool
    type: str
    web_url: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TokenData(BaseModel):
    auth_token: str
    user_id: UUID
    expires_at: datetime
    created_at: datetime
    updated_at: datetime

class Security(BaseModel):
    private_key: str
    token: TokenData

class SignInResponse(BaseModel):
    security: Security
    user: UserResponse

class CodeVerification(BaseModel):
    code: str

class PasswordReset(BaseModel):
    code: str
    password: str
    email: EmailStr

class UserSignIn(BaseModel):
    email: EmailStr
    password: str

