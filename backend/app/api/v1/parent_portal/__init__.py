"""
EduCore Backend - Enhanced Parent Portal Module
Conference booking, payments, notifications, and document management
"""
from fastapi import APIRouter

from app.api.v1.parent_portal.conferences import router as conferences_router
from app.api.v1.parent_portal.payments import router as payments_router
from app.api.v1.parent_portal.notifications import router as notifications_router
from app.api.v1.parent_portal.documents import router as documents_router
from app.api.v1.parent_portal.calendar import router as calendar_router

router = APIRouter()

router.include_router(conferences_router, prefix="/conferences", tags=["parent_conferences"])
router.include_router(payments_router, prefix="/payments", tags=["parent_payments"])
router.include_router(notifications_router, prefix="/notifications", tags=["parent_notifications"])
router.include_router(documents_router, prefix="/documents", tags=["parent_documents"])
router.include_router(calendar_router, prefix="/calendar", tags=["parent_calendar"])
