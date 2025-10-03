from fastapi import APIRouter
from app.controller import video
from app.controller import ping


root_api_router = APIRouter()
root_api_router.include_router(video.router)
root_api_router.include_router(ping.router)
