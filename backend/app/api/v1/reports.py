from fastapi import APIRouter, Depends
from typing import Optional
from datetime import date
from app.core.auth import get_current_user, get_user_school_id
from app.db.supabase_client import get_supabase_admin

router = APIRouter()

@router.get("/summary")
async def get_report_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    result = supabase.rpc("get_report_summary", {
        "p_school_id": school_id,
        "p_start_date": start_date.isoformat() if start_date else None,
        "p_end_date": end_date.isoformat() if end_date else None
    }).execute()
    return result.data[0] if result.data else {}

@router.get("/student-directory")
async def get_student_directory(
    grade_id: Optional[str] = None,
    class_id: Optional[str] = None,
    status: str = "active",
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    query = supabase.table("students").select("*").eq("school_id", school_id).eq("status", status)
    
    if grade_id:
        query = query.eq("grade_id", grade_id)
    if class_id:
        query = query.eq("class_id", class_id)
    
    result = query.order("first_name").execute()
    return result.data

@router.get("/attendance-summary")
async def get_attendance_summary(
    grade_id: Optional[str] = None,
    class_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    query = supabase.table("attendance_records").select("*, attendance_sessions!inner(*)").eq("attendance_sessions.school_id", school_id)
    
    if start_date:
        query = query.gte("attendance_sessions.date", start_date.isoformat())
    if end_date:
        query = query.lte("attendance_sessions.date", end_date.isoformat())
    
    result = query.execute()
    return result.data
