import logging
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.security import get_user_by_email, get_password_hash
from app.schemas.user import UserCreate, UserOut, RefreshToken
from .CRUD.auth import Auth_Service
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


security = HTTPBearer()

auth_router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger(__name__)


@auth_router.post("/login", status_code=status.HTTP_201_CREATED)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return Auth_Service.login(db, form_data)


@auth_router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserOut)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    logger.info("checking if user exists....")

    # Check if user already exists
    existing_user = get_user_by_email(db, email=user_data.email)
    if existing_user:
        logger.warning(f"User with email {user_data.email} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    logger.info('Hashing password...')
    password_hash = get_password_hash(user_data.password)

    logger.info('Creating new user...')
    new_user = Auth_Service.register(db, user_data, password_hash)
    logger.info('User successfully created.')

    return new_user

@auth_router.post("/refresh", status_code=status.HTTP_201_CREATED, response_model=dict)
def refresh(request: RefreshToken, db: Session = Depends(get_db)):
    return Auth_Service.refresh_token(db, request.refresh_token)



@auth_router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    authorization: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = authorization.credentials
    return Auth_Service.logout(db, token)