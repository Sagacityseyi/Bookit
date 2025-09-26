from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, field_validator, ConfigDict
from enum import Enum


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class BookingBase(BaseModel):
    service_id: UUID
    start_time: datetime
    end_time: datetime


class BookingCreate(BookingBase):
   pass



class BookingUpdate(BaseModel):
    status: Optional[BookingStatus] = None
    start_time: Optional[datetime] = None


class BookingOut(BookingBase):
    id: UUID
    user_id: UUID
    end_time: datetime
    status: BookingStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)  # v2 syntax


class BookingFilter(BaseModel):
    status: Optional[BookingStatus] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None