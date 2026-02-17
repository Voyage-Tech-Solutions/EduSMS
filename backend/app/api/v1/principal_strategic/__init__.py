"""
EduCore Backend - Principal Strategic Tools Module
School goals, staff evaluations, professional development, and analytics
"""
from fastapi import APIRouter

from app.api.v1.principal_strategic.goals import router as goals_router
from app.api.v1.principal_strategic.evaluations import router as evaluations_router
from app.api.v1.principal_strategic.professional_development import router as pd_router
from app.api.v1.principal_strategic.analytics import router as analytics_router

router = APIRouter()

router.include_router(goals_router, prefix="/goals", tags=["school_goals"])
router.include_router(evaluations_router, prefix="/evaluations", tags=["staff_evaluations"])
router.include_router(pd_router, prefix="/professional-development", tags=["professional_development"])
router.include_router(analytics_router, prefix="/analytics", tags=["school_analytics"])
