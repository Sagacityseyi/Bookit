from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from typing import List, Optional

from app.db.database import get_db
from app.models.user import User, Role
from app.CRUD.booking import Booking_Crud
from app.schemas.booking import BookingCreate, BookingUpdate, BookingOut, BookingStatus, BookingFilter
from app.services.auth import get_current_user

booking_router = APIRouter(prefix="/bookings", tags=["bookings"])


@booking_router.post("/", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(
        booking_data: BookingCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    try:
        new_booking = Booking_Crud.create_booking(db, booking_data, current_user.id)
        return new_booking
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@booking_router.get("/", response_model=dict)
def get_bookings(
        status: Optional[BookingStatus] = Query(None, description="Filter by status"),
        from_date: Optional[datetime] = Query(None, description="Filter from date"),
        to_date: Optional[datetime] = Query(None, description="Filter to date"),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    try:
        bookings, total = Booking_Crud.get_bookings(
            db, current_user, status, from_date, to_date, skip, limit
        )

        # Convert to Pydantic models
        from app.schemas.booking import BookingOut
        booking_models = [BookingOut.model_validate(booking) for booking in bookings]

        return {
            "data": booking_models,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@booking_router.get("/{booking_id}", response_model=BookingOut)
def get_booking(
        booking_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    booking = Booking_Crud.get_booking(db, booking_id, current_user)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    return BookingOut.model_validate(booking)


@booking_router.patch("/{booking_id}", response_model=BookingOut)
def update_booking(
        booking_id: UUID,
        update_data: BookingUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    try:
        updated_booking = Booking_Crud.update_booking(db, booking_id, update_data, current_user)
        if not updated_booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

        return updated_booking
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@booking_router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(
        booking_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    try:
        success = Booking_Crud.delete_booking(db, booking_id, current_user)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))