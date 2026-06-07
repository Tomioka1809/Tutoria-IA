from fastapi import APIRouter

from app.api.v1.endpoints import auth, sessions, events, streaks, notifications, chat, tutors

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(streaks.router, prefix="/streaks", tags=["streaks"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(tutors.router, prefix="/tutors", tags=["tutors"])
