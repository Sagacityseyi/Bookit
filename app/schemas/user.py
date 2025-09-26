from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict


class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"

class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(UserBase):
    id: UUID
    role: Role = Role.USER
    created_at: datetime

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

    model_config = ConfigDict(from_attributes=True)


class UserOut(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    created_at: datetime


    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str

class TokenData(BaseModel):
    email: str | None = None


class RefreshToken(BaseModel):
    refresh_token: str