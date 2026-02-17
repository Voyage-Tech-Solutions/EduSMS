"""
EduCore Backend - System Module
Audit logging, health monitoring, and system administration
"""
from fastapi import APIRouter

from app.api.v1.system.audit import router as audit_router
from app.api.v1.system.health import router as health_router
from app.api.v1.system.search import router as search_router
from app.api.v1.system.backup import router as backup_router

router = APIRouter()

router.include_router(audit_router, prefix="/audit", tags=["audit"])
router.include_router(health_router, prefix="/health", tags=["health"])
router.include_router(search_router, prefix="/search", tags=["search"])
router.include_router(backup_router, prefix="/backup", tags=["backup"])
