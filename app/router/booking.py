import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from app.CRUD.booking import Booking_Crud
from app.database import get_db
from app.models import User
from app.schemas.booking import BookingOut, BookingCreate, BookingStatus, BookingUpdate
from app.schemas.user import Role
from app.security import get_current_user

booking_router = APIRouter(prefix="/bookings", tags=["bookings"])

logger = logging.getLogger(__name__)

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
        logging.error(f"Error creating booking: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@booking_router.get("/", response_model=dict)
def get_bookings(
        status: Optional[BookingStatus] = Query(None, description="Filter by status"),
        from_date: Optional[datetime] = Query(None, description="Filter from date"),
        to_date: Optional[datetime] = Query(None, description="Filter to date"),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    try:
        bookings, total = Booking_Crud.get_bookings(
            db, current_user, status, from_date, to_date, skip, limit
        )

        booking_models = [BookingOut.model_validate(booking) for booking in bookings]

        return {
            "data": booking_models,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error fetching bookings: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))



@booking_router.get("/{booking_id}", response_model=BookingOut)
def get_booking(
        booking_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    logger.info(f"Fetching booking with ID: {booking_id}")
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
    logger.info(f"Updating booking with ID: {booking_id}")
    try:
        updated_booking = Booking_Crud.update_booking(db, booking_id, update_data, current_user)
        if not updated_booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

        return updated_booking
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating booking: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@booking_router.post("/{id}/complete", response_model=BookingOut)
def complete_booking(
        booking_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        completed_booking = Booking_Crud.complete_booking(db, booking_id, current_user)
        if not completed_booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        return completed_booking
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@booking_router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(
    booking_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        success = Booking_Crud.delete_booking(db, booking_id, current_user)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        return None

    except (ValueError, PermissionError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting booking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )