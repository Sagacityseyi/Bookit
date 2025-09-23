from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timezone
from typing import List, Optional
import logging

from app import models
from app.models import Review, User
from app.schemas.booking import BookingStatus
from app.schemas.user import Role

logger = logging.getLogger(__name__)


class Review_Crud:

    @staticmethod
    def create_review(db: Session, review_data, user_id: UUID) -> Review:
        try:
            logger.info(f"Attempting to create review for booking {review_data.booking_id} by user {user_id}")

            # Check if booking exists and belongs to user
            booking = db.query(models.Booking).filter(
                models.Booking.id == review_data.booking_id,
                models.Booking.user_id == user_id
            ).first()

            if not booking:
                logger.warning(f"Booking {review_data.booking_id} not found or doesn't belong to user {user_id}")
                raise ValueError("Booking not found or access denied")

            # Check if booking is completed
            if booking.status != BookingStatus.COMPLETED:
                logger.warning(f"Booking {review_data.booking_id} is not completed (status: {booking.status})")
                raise ValueError("Can only review completed bookings")

            # Check if review already exists for this booking
            existing_review = db.query(models.Review).filter(models.Review.booking_id == review_data.booking_id).first()
            if existing_review:
                logger.warning(f"Review already exists for booking {review_data.booking_id}")
                raise ValueError("Only one review allowed per booking")

            # Create the review
            review = Review(
                booking_id=review_data.booking_id,
                rating=review_data.rating,
                comment=review_data.comment
            )

            db.add(review)
            db.commit()
            db.refresh(review)

            logger.info(f"Review {review.id} created successfully for booking {review_data.booking_id}")
            return review

        except Exception as e:
            db.rollback()
            logger.error(f"Error creating review: {str(e)}")
            raise

    @staticmethod
    def get_reviews_by_service(db: Session, service_id: UUID, skip: int = 0, limit: int = 100) -> List[Review]:
        try:
            logger.info(f"Fetching reviews for service {service_id}")

            reviews = db.query(models.Review).filter(
                models.Review.service_id == service_id
            ).order_by(Review.created_at.desc()).offset(skip).limit(limit).all()

            logger.info(f"Found {len(reviews)} reviews for service {service_id}")

            return reviews

        except Exception as e:
            logger.error(f"Error fetching reviews for service {service_id}: {str(e)}")
            raise

    @staticmethod
    def get_review(db: Session, review_id: UUID) -> Optional[Review]:
        try:
            logger.info(f"Fetching review {review_id}")
            return db.query(Review).filter(Review.id == review_id).first()
        except Exception as e:
            logger.error(f"Error fetching review {review_id}: {str(e)}")
            raise

    @staticmethod
    def update_review(db: Session, review_id: UUID, update_data, user: User) -> Optional[Review]:
        try:
            logger.info(f"Attempting to update review {review_id} by user {user.id}")

            review = db.query(Review).filter(Review.id == review_id).first()
            if not review:
                logger.warning(f"Review {review_id} not found")
                return None

            # Check if user owns the review or is admin
            if user.role != Role.ADMIN and review.user_id != user.id:
                logger.warning(f"User {user.id} not authorized to update review {review_id}")
                raise PermissionError("Not authorized to update this review")

            # Update fields if provided
            if update_data.rating is not None:
                review.rating = update_data.rating
            if update_data.comment is not None:
                review.comment = update_data.comment

            review.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(review)

            logger.info(f"Review {review_id} updated successfully")
            return review

        except Exception as e:
            db.rollback()
            logger.error(f"Error updating review {review_id}: {str(e)}")
            raise

    @staticmethod
    def delete_review(db: Session, review_id: UUID, user: User) -> bool:
        try:
            logger.info(f"Attempting to delete review {review_id} by user {user.id}")

            review = db.query(Review).filter(Review.id == review_id).first()
            if not review:
                logger.warning(f"Review {review_id} not found")
                return False

            # Check if user owns the review or is admin
            if user.role != Role.ADMIN and review.user_id != user.id:
                logger.warning(f"User {user.id} not authorized to delete review {review_id}")
                raise PermissionError("Not authorized to delete this review")

            db.delete(review)
            db.commit()

            logger.info(f"Review {review_id} deleted successfully")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting review {review_id}: {str(e)}")
            raise

    @staticmethod
    def get_service_rating_stats(db: Session, service_id: UUID) -> dict:
        try:
            logger.info(f"Calculating rating stats for service {service_id}")

            from sqlalchemy import func

            stats = db.query(
                func.count(Review.id).label('total_reviews'),
                func.avg(Review.rating).label('average_rating'),
                func.min(Review.rating).label('min_rating'),
                func.max(Review.rating).label('max_rating')
            ).filter(Review.service_id == service_id).first()

            result = {
                'total_reviews': stats.total_reviews or 0,
                'average_rating': float(stats.average_rating or 0),
                'min_rating': stats.min_rating or 0,
                'max_rating': stats.max_rating or 0
            }

            logger.info(f"Rating stats for service {service_id}: {result}")
            return result

        except Exception as e:
            logger.error(f"Error calculating rating stats for service {service_id}: {str(e)}")
            raise