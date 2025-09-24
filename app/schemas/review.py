from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReviewBase(BaseModel):
    comment: str = Field(..., min_length=1, max_length=1000, description="Review comment")
    rating: int = Field(..., ge=1, le=5, description="Rating must be between 1 and 5")


class ReviewCreate(ReviewBase):
    booking_id: UUID = Field(..., description="ID of the booking being reviewed")

    @field_validator('rating')
    def validate_rating(cls, v):
        if v < 1 or v > 5:
            raise ValueError("Rating must be between 1 and 5")
        return v


class ReviewUpdate(BaseModel):
    comment: str | None = Field(None, min_length=1, max_length=1000, description="Review comment")
    rating: int | None = Field(None, ge=1, le=5, description="Rating must be between 1 and 5")


class Review(ReviewBase):
    id: UUID
    booking_id: UUID
    created_at: datetime


    model_config = ConfigDict(from_attributes=True)


class ReviewOut(BaseModel):
    id: UUID
    booking_id: UUID
    comment: str
    rating: int
    created_at: datetime

