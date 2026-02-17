"""
EduCore Backend - Enhanced Gradebook Module
Comprehensive gradebook management with weighted categories and standards
"""
from fastapi import APIRouter

from app.api.v1.gradebook.routes import router as gradebook_router
from app.api.v1.gradebook.scales import router as scales_router
from app.api.v1.gradebook.categories import router as categories_router
from app.api.v1.gradebook.calculations import router as calculations_router

router = APIRouter(prefix="/gradebook", tags=["gradebook"])

router.include_router(gradebook_router)
router.include_router(scales_router, prefix="/scales", tags=["grading_scales"])
router.include_router(categories_router, prefix="/categories", tags=["grade_categories"])
router.include_router(calculations_router, prefix="/calculations", tags=["grade_calculations"])
