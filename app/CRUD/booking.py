from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from typing import List, Optional, Tuple
from app.models.booking import Booking, BookingStatus
from app.models.service import Service
from app.models.user import User, Role


class Booking_Crud:

    @staticmethod
    def create_booking(db: Session, booking_data, user_id: UUID) -> Booking:
        # Check for overlapping bookings
        overlapping = db.query(Booking).filter(
            Booking.service_id == booking_data.service_id,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
            Booking.start_time < booking_data.start_time,
            Booking.end_time > booking_data.start_time
        ).first()

        if overlapping:
            raise ValueError("Time slot is already booked")

        # Get service to calculate end_time and total_price
        service = db.query(Service).filter(Service.id == booking_data.service_id).first()
        if not service:
            raise ValueError("Service not found")

        # Calculate end_time and total_price
        from datetime import timedelta
        end_time = booking_data.start_time + timedelta(minutes=service.duration_minutes)
        total_price = service.price

        booking = Booking(
            user_id=user_id,
            service_id=booking_data.service_id,
            start_time=booking_data.start_time,
            end_time=end_time,
            total_price=total_price,
            notes=booking_data.notes,
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
    ) -> Tuple[List[Booking], int]:

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

        # Check if user has permission to view this booking
        if booking and (user.role == Role.ADMIN or booking.user_id == user.id):
            return booking
        return None

    @staticmethod
    def update_booking(db: Session, booking_id: UUID, update_data, user: User) -> Optional[Booking]:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            return None

        # Permission check
        if user.role != Role.ADMIN and booking.user_id != user.id:
            raise PermissionError("Not authorized to update this booking")

        # Status transition rules
        if update_data.status:
            if user.role != Role.ADMIN:
                # Users can only cancel their own bookings
                if update_data.status != BookingStatus.CANCELLED:
                    raise ValueError("Users can only cancel bookings")

                # Can only cancel before start time
                if booking.start_time <= datetime.now():
                    raise ValueError("Cannot cancel booking after it has started")

            booking.status = update_data.status

        # Rescheduling rules
        if update_data.start_time:
            if user.role != Role.ADMIN and booking.status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
                raise ValueError("Can only reschedule pending or confirmed bookings")

            # Check for new time conflicts
            overlapping = db.query(Booking).filter(
                Booking.service_id == booking.service_id,
                Booking.id != booking_id,
                Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
                Booking.start_time < update_data.start_time,
                Booking.end_time > update_data.start_time
            ).first()

            if overlapping:
                raise ValueError("New time slot is already booked")

            # Recalculate end_time and update
            service = db.query(Service).filter(Service.id == booking.service_id).first()
            from datetime import timedelta
            booking.start_time = update_data.start_time
            booking.end_time = update_data.start_time + timedelta(minutes=service.duration_minutes)

        if update_data.notes:
            booking.notes = update_data.notes

        booking.updated_at = datetime.now()
        db.commit()
        db.refresh(booking)
        return booking

    @staticmethod
    def delete_booking(db: Session, booking_id: UUID, user: User) -> bool:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            return False

        # Permission and timing rules
        if user.role == Role.ADMIN:
            # Admin can delete anytime
            pass
        elif booking.user_id == user.id:
            # User can only delete before start time
            if booking.start_time <= datetime.now():
                raise ValueError("Cannot delete booking after it has started")
        else:
            raise PermissionError("Not authorized to delete this booking")

        db.delete(booking)
        db.commit()
        return True