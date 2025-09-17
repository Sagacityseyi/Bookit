import logging

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app import models
from app.models import User
from app.schemas.user import UserCreate, RefreshToken
from app.security import authenticate_user, create_token, SECRET_KEY, ALGORITHM, create_access_token, \
    create_refresh_token

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

    @staticmethod
    def refresh_token(db: Session, request):
        try:
            payload = jwt.decode(request.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])

            # Validate token type
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )

            user_email = payload.get("sub")
            if user_email is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )

        except jwt.ExpiredSignatureError:
            logger.error("Refresh token expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired"
            )
        except jwt.PyJWTError as e:
            logger.error(f"Invalid refresh token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        # Check if user exists
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        # Create new tokens
        new_access_token = create_access_token(data={"sub": user.email})
        new_refresh_token = create_refresh_token(data={"sub": user.email})

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }


Auth_Service = AuthService()