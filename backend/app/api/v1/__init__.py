"""API v1 module exports"""
from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.students import router as students_router
from app.api.v1.fees import router as fees_router
from app.api.v1.attendance import router as attendance_router
from app.api.v1.schools import router as schools_router
from app.api.v1.admissions import router as admissions_router
from app.api.v1.documents import router as documents_router
from app.api.v1.reports import router as reports_router
from app.api.v1.settings import router as settings_router
from app.api.v1.system_admin_extended import router as system_admin_router
from app.api.v1.principal import router as principal_router
from app.api.v1.office_admin import router as office_admin_router
from app.api.v1.teacher import router as teacher_router
from app.api.v1.parent import router as parent_router
from app.api.v1.student import router as student_router


# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Include all sub-routers
api_router.include_router(auth_router)
api_router.include_router(schools_router)
api_router.include_router(students_router)
api_router.include_router(fees_router)
api_router.include_router(attendance_router)
api_router.include_router(admissions_router)
api_router.include_router(documents_router)
api_router.include_router(reports_router)
api_router.include_router(settings_router)
api_router.include_router(system_admin_router)
api_router.include_router(principal_router, prefix="/principal", tags=["principal"])
api_router.include_router(office_admin_router, prefix="/office-admin", tags=["office_admin"])
api_router.include_router(teacher_router, prefix="/teacher", tags=["teacher"])
api_router.include_router(parent_router, prefix="/parent", tags=["parent"])
api_router.include_router(student_router, prefix="/student", tags=["student"])
