from fastapi import APIRouter



auth_router = APIRouter()


@auth_router.post("/register")
def register()