from datetime import datetime
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict, Field


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


class UserUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=50)
    email: EmailStr | None = None


class User(UserBase):
    id: UUID
    role: Role = Role.USER
    created_at: datetime
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class UserOut(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    role: Role
    created_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
