from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, field_validator
from enum import Enum


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class BookingBase(BaseModel):
    service_id: UUID
    start_time: datetime  # Added notes field


class BookingCreate(BookingBase):
    @field_validator('start_time')
    def validate_start_time(cls, v):
        now = datetime.now(timezone.utc)
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)

        if v <= now:
            raise ValueError("Start time must be in the future")

        min_booking_time = now + timedelta(hours=1)
        if v < min_booking_time:
            raise ValueError("Bookings must be made at least 1 hour in advance")

        if v.hour < 8 or v.hour >= 20:
            raise ValueError("Bookings only available between 8 AM and 8 PM")

        if v.weekday() >= 5:
            raise ValueError("Weekend bookings not available")
        return v


class BookingUpdate(BaseModel):
    status: Optional[BookingStatus] = None
    start_time: Optional[datetime] = None




class BookingOut(BookingBase):
    id: UUID
    user_id: UUID
    end_time: datetime
    status: BookingStatus
    created_at: datetime


    model_config = ConfigDict(from_attributes=True)


class BookingFilter(BaseModel):
    status: Optional[BookingStatus] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None