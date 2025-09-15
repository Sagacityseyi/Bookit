from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from enum import Enum


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class BookingBase(BaseModel):
    user_id: UUID
    service_id: UUID
    start_time: datetime
    end_time: datetime


class BookingCreate(BookingBase):
    pass


class BookingUpdate(BaseModel):
    status: BookingStatus | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None


class Booking(BookingBase):
    id: UUID
    status: BookingStatus

    model_config = ConfigDict(from_attributes=True)


class BookingOut(BaseModel):
    id: UUID
    user_id: UUID
    service_id: UUID
    status: BookingStatus
    start_time: datetime
    end_time: datetime

    model_config = ConfigDict(from_attributes=True)