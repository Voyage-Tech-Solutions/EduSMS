"""
EduCore Backend - Student Progress Monitoring Module
Learning profiles, interventions, portfolios, and progress reports
"""
from fastapi import APIRouter

from app.api.v1.progress.profiles import router as profiles_router
from app.api.v1.progress.interventions import router as interventions_router
from app.api.v1.progress.portfolios import router as portfolios_router
from app.api.v1.progress.reports import router as reports_router

router = APIRouter()

router.include_router(profiles_router, prefix="/profiles", tags=["learning_profiles"])
router.include_router(interventions_router, prefix="/interventions", tags=["interventions"])
router.include_router(portfolios_router, prefix="/portfolios", tags=["portfolios"])
router.include_router(reports_router, prefix="/reports", tags=["progress_reports"])
