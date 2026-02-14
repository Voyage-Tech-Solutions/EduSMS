"""API v1 module exports"""
from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.students import router as students_router
from app.api.v1.schools import router as schools_router
from app.api.v1.admissions import router as admissions_router
from app.api.v1.fees import router as fees_router_new
from app.api.v1.documents import router as documents_router_new
from app.api.v1.reports import router as reports_router_new
from app.api.v1.settings import router as settings_router_new
from app.api.v1.attendance import router as attendance_router
from app.api.v1.system_admin_extended import router as system_admin_router
from app.api.v1.principal import router as principal_router
from app.api.v1.office_admin import router as office_admin_router
from app.api.v1.office_admin_complete import router as office_admin_complete_router
from app.api.v1.teacher import router as teacher_router
from app.api.v1.teacher_complete import router as teacher_complete_router
from app.api.v1.parent import router as parent_router
from app.api.v1.student import router as student_router
from app.api.v1.assessments import router as assessments_router
from app.api.v1.principal_students import router as principal_students_router
from app.api.v1.principal_approvals import router as principal_approvals_router
from app.api.v1.principal_students_approvals import router as principal_students_approvals_router
from app.api.v1.teacher_gradebook import router as teacher_gradebook_router
from app.api.v1.teacher_planning import router as teacher_planning_router
from app.api.v1.parent_dashboard import router as parent_dashboard_router
from app.api.v1.principal_dashboard_complete import router as principal_dashboard_router
from app.api.v1.principal_oversight import router as principal_oversight_router
from app.api.v1.sysadmin import router as sysadmin_router


# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Include all sub-routers
api_router.include_router(auth_router)
api_router.include_router(schools_router)
api_router.include_router(students_router)
api_router.include_router(attendance_router)
api_router.include_router(admissions_router)
api_router.include_router(fees_router_new, prefix="/fees", tags=["fees"])
api_router.include_router(documents_router_new, prefix="/documents", tags=["documents"])
api_router.include_router(reports_router_new, prefix="/reports", tags=["reports"])
api_router.include_router(settings_router_new, prefix="/settings", tags=["settings"])
api_router.include_router(assessments_router, prefix="/assessments", tags=["assessments"])
api_router.include_router(system_admin_router)
api_router.include_router(principal_router, prefix="/principal", tags=["principal"])
api_router.include_router(principal_students_router)
api_router.include_router(principal_approvals_router)
api_router.include_router(principal_students_approvals_router, prefix="/principal", tags=["principal_students_approvals"])
api_router.include_router(principal_oversight_router, prefix="/principal", tags=["principal_oversight"])
api_router.include_router(office_admin_router, prefix="/office-admin", tags=["office_admin"])
api_router.include_router(office_admin_complete_router, prefix="/office-admin", tags=["office_admin_complete"])
api_router.include_router(teacher_router, prefix="/teacher", tags=["teacher"])
api_router.include_router(teacher_complete_router, prefix="/teacher", tags=["teacher_complete"])
api_router.include_router(teacher_gradebook_router)
api_router.include_router(teacher_planning_router)
api_router.include_router(parent_router, prefix="/parent", tags=["parent"])
api_router.include_router(parent_dashboard_router, prefix="/parent", tags=["parent_dashboard"])
api_router.include_router(principal_dashboard_router, prefix="/principal-dashboard", tags=["principal_dashboard"])
api_router.include_router(student_router, prefix="/student", tags=["student"])
api_router.include_router(sysadmin_router)
