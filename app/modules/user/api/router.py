from fastapi import APIRouter
from .v1.router import v1 as user_router

v1 = APIRouter()

v1.include_router(user_router)