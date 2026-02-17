"""
EduCore Backend - Enhanced Assessment Module
Quiz builder, question bank, and auto-grading
"""
from fastapi import APIRouter

from app.api.v1.assessments.questions import router as questions_router
from app.api.v1.assessments.quiz_builder import router as quiz_builder_router
from app.api.v1.assessments.attempts import router as attempts_router
from app.api.v1.assessments.rubrics import router as rubrics_router

router = APIRouter(prefix="/assessments-v2", tags=["assessments"])

router.include_router(questions_router, prefix="/questions", tags=["question_bank"])
router.include_router(quiz_builder_router, prefix="/quizzes", tags=["quiz_builder"])
router.include_router(attempts_router, prefix="/attempts", tags=["quiz_attempts"])
router.include_router(rubrics_router, prefix="/rubrics", tags=["rubrics"])
