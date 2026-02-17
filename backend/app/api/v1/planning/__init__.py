"""
EduCore Backend - Lesson Planning Module
Enhanced lesson planning with curriculum mapping, templates, and resources
"""
from fastapi import APIRouter

from app.api.v1.planning.curriculum import router as curriculum_router
from app.api.v1.planning.templates import router as templates_router
from app.api.v1.planning.resources import router as resources_router
from app.api.v1.planning.lessons import router as lessons_router

router = APIRouter()

router.include_router(curriculum_router, prefix="/curriculum", tags=["curriculum"])
router.include_router(templates_router, prefix="/templates", tags=["lesson_templates"])
router.include_router(resources_router, prefix="/resources", tags=["teaching_resources"])
router.include_router(lessons_router, prefix="/lessons", tags=["lesson_plans"])
