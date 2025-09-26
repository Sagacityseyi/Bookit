from datetime import datetime, timezone, timedelta
import logging
from fastapi import HTTPException, status
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from app import models
from app.models import Booking, User
from app.schemas.booking import BookingStatus
from app.schemas.user import Role

logger = logging.getLogger(__name__)

class Booking_Crud:

    @staticmethod
    def ensure_timezone_aware(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    @staticmethod
    def create_booking(db: Session, booking_data, user_id: UUID) -> Booking:
        now = datetime.now(timezone.utc)
        logger.info(f"Creating booking for user {user_id} at {now.isoformat()}")

        start_time = Booking_Crud.ensure_timezone_aware(booking_data.start_time)

        if start_time <= now:
            raise ValueError("Start time must be in the future")

        overlapping = db.query(Booking).filter(
            Booking.service_id == booking_data.service_id,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
            (Booking.start_time <= start_time) & (Booking.end_time > start_time)
        ).first()

        if overlapping:
            raise HTTPException(
                status_code = status.HTTP_409_CONFLICT,
                detail="Time slot is already booked")
        
        logger.info("No overlapping bookings found")

        service = db.query(models.Service).filter(models.Service.id == booking_data.service_id).first()
        if not service:
            raise ValueError("Service not found")


        booking = Booking(
            user_id=user_id,
            service_id=booking_data.service_id,
            start_time=start_time,
            end_time=booking_data.end_time,
            status=BookingStatus.PENDING
        )
        logger.info(f"Booking created: {booking}")

        db.add(booking)
        db.commit()
        db.refresh(booking)
        return booking

    @staticmethod
    def get_bookings(
            db: Session,
            user: User,
            status: Optional[BookingStatus] = None,
            from_date: Optional[datetime] = None,
            to_date: Optional[datetime] = None,
            skip: int = 0,
            limit: int = 100
    ):
        logger.info(f"Fetching bookings for user {user.id} ")

        query = db.query(Booking)

        # Regular users can only see their own bookings
        if user.role != Role.ADMIN:
            query = query.filter(Booking.user_id == user.id)

        if status:
            query = query.filter(Booking.status == status)

        if from_date:
            query = query.filter(Booking.start_time >= from_date)

        if to_date:
            query = query.filter(Booking.start_time <= to_date)
            
            logger.info(f"Filtering bookings up to {to_date.isoformat()}")

        total = query.count()
        bookings = query.order_by(Booking.start_time.desc()).offset(skip).limit(limit).all()

        return bookings, total

    @staticmethod
    def get_booking(db: Session, booking_id: UUID, user: User) -> Optional[Booking]:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()

        if booking and (user.role == Role.ADMIN or booking.user_id == user.id):
            return booking
        return None

    @staticmethod
    def update_booking(db: Session, booking_id: UUID, update_data, user: User) -> Optional[Booking]:
        logger.info(f"Updating booking {booking_id} for user {user.id}")
        booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
        if not booking:
            return None

        if user.role != Role.ADMIN and booking.user_id != user.id:
            raise PermissionError("Not authorized to update this booking")

        now = datetime.now(timezone.utc)
        booking_start = Booking_Crud.ensure_timezone_aware(booking.start_time)
        is_rescheduling = update_data.start_time is not None

        if update_data.status is not None:
            if user.role != Role.ADMIN:
                allowed_statuses = [BookingStatus.CANCELLED]
                if is_rescheduling:
                    allowed_statuses.append(BookingStatus.PENDING)

                if update_data.status not in allowed_statuses:
                    raise ValueError("Users can only cancel bookings or set to pending when rescheduling")

                if booking_start <= now and update_data.status != BookingStatus.CANCELLED:
                    raise ValueError("Cannot change status after booking has started")

            booking.status = update_data.status


        if update_data.start_time is not None:
            new_start_time = Booking_Crud.ensure_timezone_aware(update_data.start_time)

            if user.role != Role.ADMIN:
                if booking.status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
                    raise ValueError("Can only reschedule pending or confirmed bookings")
                if booking_start <= now:
                    raise ValueError("Cannot reschedule booking after it has started")

            if new_start_time <= now:
                raise ValueError("New start time must be in the future")

            if new_start_time.hour < 8 or new_start_time.hour >= 20:
                raise ValueError("Bookings only available between 8 AM and 8 PM")
            if new_start_time.weekday() >= 5:
                raise ValueError("Weekend bookings not available")

            overlapping = db.query(Booking).filter(
                Booking.service_id == booking.service_id,
                Booking.id != booking_id,
                Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
                (Booking.start_time <= new_start_time) & (Booking.end_time > new_start_time)
            ).first()

            if overlapping:
                raise ValueError("New time slot is already booked")

            service = db.query(models.Service).filter(models.Service.id == booking.service_id).first()
            booking.start_time = new_start_time
            booking.end_time = new_start_time + timedelta(minutes=service.duration_minutes)

        booking.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(booking)
        return booking


    @staticmethod
    def complete_booking(db: Session, booking_id: UUID, admin_user: User) -> Optional[Booking]:
        logger.info(f"Admin {admin_user.id} completing booking {booking_id}")
        if admin_user.role != Role.ADMIN:
            raise PermissionError("Only admins can complete bookings")

        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            logger.warning(f"Booking {booking_id} not found")
            return None

    
        booking.status = BookingStatus.COMPLETED
        booking.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(booking)
        logger.info(f"Booking {booking_id} marked as completed")
        return booking

    @staticmethod
    def delete_booking(db: Session, booking_id: UUID, user: User) -> bool:
        try:
            logger.info(f"Deleting booking {booking_id} for user {user.id}")

            booking = db.query(Booking).filter(Booking.id == booking_id).first()
            if not booking:
                logger.warning(f"Booking {booking_id} not found")
                return False

            now = datetime.now(timezone.utc)
            logger.info(f"Current time: {now}, Booking start time: {booking.start_time}")

            booking_start = Booking_Crud.ensure_timezone_aware(booking.start_time)
            logger.info(f"Timezone-aware booking start: {booking_start}")

            if user.role == Role.ADMIN:
                logger.info("Admin deletion - no time restrictions")
            elif booking.user_id == user.id:
                # User can only delete before start time
                if booking_start <= now:
                    logger.warning(f"Cannot delete - booking started at {booking_start}, current time {now}")
                    raise ValueError("Cannot delete booking after it has started")
                logger.info("User deletion allowed - booking hasn't started yet")
            else:
                logger.warning(f"User {user.id} not authorized to delete booking {booking_id}")
                raise PermissionError("Not authorized to delete this booking")

            db.delete(booking)
            db.commit()
            logger.info(f"Booking {booking_id} deleted successfully")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting booking: {str(e)}")
            raise