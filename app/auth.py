import logging
from fastapi import APIRouter,HTTPException,status
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app import logger
from app.database import get_db
from app.security import authenticate_user

auth_router = APIRouter()

logger = logging.getLogger(__name__)

@auth_router.post("/auth/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
        logger.info("Authenticating user...")
        user = authenticate_user(db, email=form_data.username, password=form_data.password)
        if not user:
            logger.warning("Login failed: Invalid credentials")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email or password is incorrect",
                headers={"WWW-Authenticate": "Bearer"},
            )
