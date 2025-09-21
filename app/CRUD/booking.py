from datetime import datetime, timezone, timedelta
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from app import models
from app.models import Booking, User
from app.schemas.booking import BookingStatus
from app.schemas.user import Role


class Booking_Crud:

    @staticmethod
    def ensure_timezone_aware(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    @staticmethod
    def create_booking(db: Session, booking_data, user_id: UUID) -> Booking:
        now = datetime.now(timezone.utc)

        start_time = Booking_Crud.ensure_timezone_aware(booking_data.start_time)

        if start_time <= now:
            raise ValueError("Start time must be in the future")

        overlapping = db.query(Booking).filter(
            Booking.service_id == booking_data.service_id,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
            (Booking.start_time <= start_time) & (Booking.end_time > start_time)
        ).first()

        if overlapping:
            raise ValueError("Time slot is already booked")

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
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
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
    def delete_booking(db: Session, booking_id: UUID, user: User) -> bool:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            return False


        if user.role == Role.ADMIN:
            pass
        elif booking.user_id == user.id:
            if booking.start_time <= datetime.now():
                raise ValueError("Cannot delete booking after it has started")
        else:
            raise PermissionError("Not authorized to delete this booking")

        db.delete(booking)
        db.commit()
        return True