from fastapi import FastAPI

from app import models
from app.auth import auth_router
from app.database import engine


models.Base.metadata.create_all(bind=engine)


app = FastAPI()


app.include_router(auth_router)