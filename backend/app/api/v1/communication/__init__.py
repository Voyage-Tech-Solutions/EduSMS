"""
EduCore Backend - Communication Hub Module
Messaging, announcements, and notifications
"""
from fastapi import APIRouter

from app.api.v1.communication.messages import router as messages_router
from app.api.v1.communication.announcements import router as announcements_router
from app.api.v1.communication.notifications import router as notifications_router
from app.api.v1.communication.templates import router as templates_router

router = APIRouter()

router.include_router(messages_router, prefix="/messages", tags=["messages"])
router.include_router(announcements_router, prefix="/announcements", tags=["announcements"])
router.include_router(notifications_router, prefix="/notifications", tags=["notifications_service"])
router.include_router(templates_router, prefix="/templates", tags=["message_templates"])
