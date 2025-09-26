from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
import logging
from app.CRUD.user import User_Crud
from app.database import get_db
from app.models import User
from app.schemas.user import UserOut, UserUpdate
from app.security import get_current_user

logger = logging.getLogger(__name__)
user_router = APIRouter(prefix="/me", tags=["users"])


@user_router.get("/", response_model=UserOut)
def get_current_user_profile(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    try:
        logger.info(f"Fetching profile for user {current_user.id}")
        return current_user

    except Exception as e:
        logger.error(f"Error fetching user profile {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching profile"
        )


@user_router.patch("/", response_model=UserOut)
def update_current_user_(
        update_data: UserUpdate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):

    try:
        logger.info(f"Updating profile for user {current_user.id}")
        update_dict = update_data.model_dump(exclude_unset=True)

        if not update_dict:
            logger.info("No fields to update")
            return current_user

        updated_user = User_Crud.update_user(db, current_user.id, update_dict)

        if not updated_user:
            logger.error(f"User {current_user.id} not found during update")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        logger.info(f"Profile updated successfully for user {current_user.id}")
        return updated_user

    except ValueError as e:
        logger.warning(f"Validation error updating user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating profile for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating profile"
        )

