from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ServiceBase(BaseModel):
    title: str
    description: str
    price: int
    duration_minutes: int

class ServiceCreate(ServiceBase):
    pass


class Service(ServiceBase):
    id: UUID
    is_active: bool = True
    created_at: datetime

class ServiceOut(BaseModel):
    id: UUID
    title: str
    description: str
    price: int
    duration_minutes: int
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class ServiceUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    price: Optional[float] = Field(None, gt=0)
    duration_minutes: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None

    model_config = {
        "from_attributes": True
    }