"""
EduCore Backend - Scheduling & Timetable Module
Room management, bell schedules, timetables, and substitutions
"""
from fastapi import APIRouter

from app.api.v1.scheduling.rooms import router as rooms_router
from app.api.v1.scheduling.bell_schedules import router as bell_schedules_router
from app.api.v1.scheduling.timetables import router as timetables_router
from app.api.v1.scheduling.substitutions import router as substitutions_router

router = APIRouter()

router.include_router(rooms_router, prefix="/rooms", tags=["rooms"])
router.include_router(bell_schedules_router, prefix="/bell-schedules", tags=["bell_schedules"])
router.include_router(timetables_router, prefix="/timetables", tags=["timetables"])
router.include_router(substitutions_router, prefix="/substitutions", tags=["substitutions"])
