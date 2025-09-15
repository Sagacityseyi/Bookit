from datetime import datetime
from uuid import UUID
from pydantic import  BaseModel


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


    model_config = {
        "from_attributes": True
    }