from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional


class ReviewBase(BaseModel):
    comment: str = Field(..., min_length=1, max_length=1000, description="Review comment")
    rating: int = Field(..., ge=1, le=5, description="Rating must be between 1 and 5")


class ReviewCreate(ReviewBase):
    booking_id: UUID = Field(..., description="ID of the booking being reviewed")

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v: int) -> int:
        if v < 1 or v > 5:
            raise ValueError("Rating must be between 1 and 5")
        return v


class ReviewUpdate(BaseModel):
    comment: Optional[str] = Field(None, min_length=1, max_length=1000, description="Review comment")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating must be between 1 and 5")


class ReviewOut(ReviewBase):
    id: UUID
    booking_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)