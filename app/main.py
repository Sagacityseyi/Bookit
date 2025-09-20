from fastapi import FastAPI
from app.auth import auth_router
from . import models
from .database import engine
from .router.booking import booking_router
from .router.service import service_router
from .router.user import user_router

models.Base.metadata.create_all(bind=engine)


app = FastAPI()


app.include_router(auth_router)
app.include_router(user_router)
app.include_router(service_router)
app.include_router(booking_router)

@app.get("/")
def home():
    return {"message" : "Welcome home"}