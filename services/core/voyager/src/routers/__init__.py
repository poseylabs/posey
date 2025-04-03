from fastapi import APIRouter
from .voyager import router as voyager_router

api_router = APIRouter()
api_router.include_router(voyager_router)
