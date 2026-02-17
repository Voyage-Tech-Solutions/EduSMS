"""
EduCore Backend - Online Admissions Portal
Public application forms, document uploads, and application tracking
"""
from fastapi import APIRouter

from app.api.v1.admissions_portal.applications import router as applications_router
from app.api.v1.admissions_portal.forms import router as forms_router
from app.api.v1.admissions_portal.documents import router as documents_router
from app.api.v1.admissions_portal.interviews import router as interviews_router
from app.api.v1.admissions_portal.public import router as public_router

router = APIRouter()

router.include_router(applications_router, prefix="/applications", tags=["admission_applications"])
router.include_router(forms_router, prefix="/forms", tags=["application_forms"])
router.include_router(documents_router, prefix="/documents", tags=["admission_documents"])
router.include_router(interviews_router, prefix="/interviews", tags=["admission_interviews"])
router.include_router(public_router, prefix="/public", tags=["public_admissions"])
