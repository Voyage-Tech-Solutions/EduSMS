from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.db.supabase import get_supabase_client

router = APIRouter()

# Students endpoints
@router.get("/students/summary")
async def get_students_summary(supabase = Depends(get_supabase_client)):
    students = supabase.table("students").select("id, status").execute()
    total = len(students.data)
    at_risk = len([s for s in students.data if s.get("status") == "at_risk"])
    inactive = len([s for s in students.data if s.get("status") == "inactive"])
    
    return {
        "total": total,
        "at_risk": at_risk,
        "chronic_absent": 0,
        "inactive": inactive
    }

@router.get("/students")
async def get_students(
    search: str = Query(""),
    grade: str = Query(""),
    status: str = Query("active"),
    risk: str = Query(""),
    supabase = Depends(get_supabase_client)
):
    query = supabase.table("students").select("*, grades(name)")
    
    if status and status != "all":
        query = query.eq("status", status)
    
    result = query.execute()
    
    return [{
        "id": s["id"],
        "admission_number": s.get("admission_number", "N/A"),
        "first_name": s.get("first_name", ""),
        "last_name": s.get("last_name", ""),
        "grade_name": s["grades"]["name"] if s.get("grades") else "N/A",
        "status": s.get("status", "active"),
        "attendance_rate": 0,
        "academic_avg": 0,
        "outstanding": 0
    } for s in result.data]

# Approvals endpoints
@router.get("/approvals/summary")
async def get_approvals_summary(supabase = Depends(get_supabase_client)):
    approvals = supabase.table("approval_requests").select("status, priority").execute()
    
    return {
        "total_pending": len([a for a in approvals.data if a.get("status") == "pending"]),
        "high_priority": len([a for a in approvals.data if a.get("priority") == "high"]),
        "approved_today": 0,
        "rejected_today": 0
    }

@router.get("/approvals")
async def get_approvals(
    status: str = Query("pending"),
    supabase = Depends(get_supabase_client)
):
    query = supabase.table("approval_requests").select("*")
    
    if status and status != "all":
        query = query.eq("status", status)
    
    result = query.execute()
    return result.data if result.data else []
