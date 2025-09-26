from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
import logging
from app.CRUD.review import Review_Crud
from app.database import get_db
from app.models import User
from app.schemas.review import ReviewOut, ReviewCreate, ReviewUpdate
from app.security import get_current_user

logger = logging.getLogger(__name__)

review_router = APIRouter(prefix="/reviews", tags=["reviews"])


@review_router.post("/", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(
        review_data: ReviewCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    try:
        logger.info(
            f"Received review creation request from user {current_user.id} for booking {review_data.booking_id}")

        new_review = Review_Crud.create_review(db, review_data, current_user.id)
        return new_review

    except ValueError as e:
        logger.warning(f"Validation error creating review: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error creating review: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@review_router.get("/services/{service_id}/reviews", response_model=List[ReviewOut])
def get_service_reviews(
        skip: int = Query(0, ge=0, description="Number of records to skip"),
        limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
        db: Session = Depends(get_db)
):
    try:
        logger.info(f"Fetching all reviews")

        reviews = Review_Crud.get_all_reviews(db, skip, limit)
        return reviews

    except Exception as e:
        logger.error(f"Error fetching all reviews id {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@review_router.get("service/{id}/review")
def get_service_review(
        service_id: UUID,
        db: Session = Depends(get_db)
):
    try:
        service_review = Review_Crud.get_service_review(db, service_id)
        if not service_review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review service not found"
            )
        return service_review

    except Exception as e:
        raise



@review_router.patch("/{review_id}", response_model=ReviewOut)
def update_review(
        review_id: UUID,
        update_data: ReviewUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    try:
        logger.info(f"Received update request for review {review_id} from user {current_user.id}")

        updated_review = Review_Crud.update_review(db, review_id, update_data, current_user)
        if not updated_review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )

        return updated_review

    except PermissionError as e:
        logger.warning(f"Permission error updating review {review_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating review {review_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@review_router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
        review_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    try:
        logger.info(f"Received delete request for review {review_id} from user {current_user.id}")

        success = Review_Crud.delete_review(db, review_id, current_user)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )

        return None

    except PermissionError as e:
        logger.warning(f"Permission error deleting review {review_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting review {review_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )