from fastapi import FastAPI
from app.auth import auth_router
from . import models
from .database import engine


models.Base.metadata.create_all(bind=engine)


app = FastAPI()


app.include_router(auth_router)