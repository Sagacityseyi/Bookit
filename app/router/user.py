import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas.user import UserOut
from app.security import get_current_user

logger = logging.getLogger(__name__)
user_router = APIRouter(prefix="/user", tags=["user"])

@user_router.get("/me", response_model=UserOut)
def get_current_user_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"Fetching profile for user: {current_user.email}")
    db.refresh(current_user)
    logger.info(f"Profile data: {current_user}")
    return current_user