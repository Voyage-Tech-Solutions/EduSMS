"""
EduCore Backend - Analytics Module
Comprehensive analytics and reporting dashboard
"""
from fastapi import APIRouter

from app.api.v1.analytics.dashboard import router as dashboard_router
from app.api.v1.analytics.reports import router as reports_router
from app.api.v1.analytics.insights import router as insights_router
from app.api.v1.analytics.exports import router as exports_router

router = APIRouter()

router.include_router(dashboard_router, prefix="/dashboard", tags=["analytics_dashboard"])
router.include_router(reports_router, prefix="/reports", tags=["analytics_reports"])
router.include_router(insights_router, prefix="/insights", tags=["analytics_insights"])
router.include_router(exports_router, prefix="/exports", tags=["analytics_exports"])
