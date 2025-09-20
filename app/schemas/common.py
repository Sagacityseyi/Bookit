# app/schemas/common.py
from pydantic import BaseModel
from typing import Generic, TypeVar, List
from datetime import datetime

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    total: int
    skip: int
    limit: int
    has_more: bool

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }