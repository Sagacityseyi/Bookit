import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app import models
from app.schemas.user import UserCreate
from app.security import authenticate_user, create_token

logger = logging.getLogger(__name__)

class AuthService:
    @staticmethod
    def login(db: Session, form_data: OAuth2PasswordRequestForm):
        logger.info("Authenticating user...")
        user = authenticate_user(db, email=form_data.username, password=form_data.password)
        if not user:
            logger.warning("Login failed: Invalid credentials")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email or password is incorrect",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = create_token(data={"sub": user.email})
        logger.info(f"Token issued for {user.email}")
        return {"access_token": access_token, "token_type": "bearer"}

    @staticmethod
    def register(db: Session, user_data: UserCreate, password_hash: str):
        user = models.User(
            name=user_data.name,
            email=user_data.email.lower(),
            password_hash=password_hash
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

Auth_Service = AuthService()