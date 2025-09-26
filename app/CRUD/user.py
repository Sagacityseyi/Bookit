from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
import logging
from app.models import User

logger = logging.getLogger(__name__)


class User_Crud:

    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
        try:
            return db.query(User).filter(User.id == user_id).first()
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {str(e)}")
            raise

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        try:
            return db.query(User).filter(User.email == email).first()
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {str(e)}")
            raise

    @staticmethod
    def update_user(db: Session, user_id: UUID, update_data: dict) -> Optional[User]:
        try:
            logger.info(f"Updating user {user_id} with data: {update_data}")

            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.warning(f"User {user_id} not found for update")
                return None

            # Check if email is being updated and if it's already taken
            if 'email' in update_data and update_data['email'] != user.email:
                existing_user = User_Crud.get_user_by_email(db, update_data['email'])
                if existing_user:
                    logger.warning(f"Email {update_data['email']} already taken")
                    raise ValueError("Email already registered")

            for field, value in update_data.items():
                if value is not None and hasattr(user, field):
                    setattr(user, field, value)

            db.commit()
            db.refresh(user)

            logger.info(f"User {user_id} updated successfully")
            return user

        except ValueError as e:
            db.rollback()
            logger.warning(f"Validation error updating user {user_id}: {str(e)}")
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating user {user_id}: {str(e)}")
            raise

