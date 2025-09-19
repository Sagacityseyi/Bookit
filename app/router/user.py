from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas.user import UserOut
from app.security import get_current_user

user_router = APIRouter(prefix="/user", tags=["user"])

@user_router.get("/me", response_model=UserOut)
def get_current_user_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db.refresh(current_user)
    return current_user