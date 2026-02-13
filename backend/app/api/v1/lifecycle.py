"""
EduCore Backend - Student Lifecycle API
Track student journey from admission to graduation
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional, Dict, Any, List
from datetime import datetime, date

from app.core.security import get_current_user, require_office_admin
from app.db.supabase import supabase_admin

router = APIRouter(prefix="/lifecycle", tags=["Lifecycle"])


@router.get("/students/{student_id}")
async def get_student_lifecycle(
    student_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get complete lifecycle history for a student"""
    school_id = current_user.get("school_id")
    
    if not supabase_admin:
        return []
    
    result = supabase_admin.table("student_lifecycle_events").select(
        "*, recorded_by:user_profiles(first_name, last_name)"
    ).eq("student_id", student_id).eq("school_id", school_id).order("event_date", desc=True).execute()
    
    return result.data


@router.post("/events", status_code=status.HTTP_201_CREATED)
async def record_lifecycle_event(
    event_data: Dict[str, Any],
    current_user: dict = Depends(require_office_admin),
):
    """Record a lifecycle event"""
    school_id = current_user.get("school_id")
    user_id = current_user.get("id")
    
    event_dict = {
        "school_id": school_id,
        "student_id": event_data["student_id"],
        "event_type": event_data["event_type"],
        "from_status": event_data.get("from_status"),
        "to_status": event_data.get("to_status"),
        "from_grade_id": event_data.get("from_grade_id"),
        "to_grade_id": event_data.get("to_grade_id"),
        "event_date": event_data.get("event_date", date.today().isoformat()),
        "reason": event_data.get("reason"),
        "notes": event_data.get("notes"),
        "recorded_by": user_id,
    }
    
    if not supabase_admin:
        return {**event_dict, "id": "mock-event-id"}
    
    result = supabase_admin.table("student_lifecycle_events").insert(event_dict).execute()
    return result.data[0]


@router.get("/stats")
async def get_lifecycle_stats(
    year: Optional[int] = None,
    current_user: dict = Depends(require_office_admin),
):
    """Get lifecycle statistics"""
    school_id = current_user.get("school_id")
    
    if not supabase_admin:
        return {"admissions": 0, "promotions": 0, "transfers": 0, "graduations": 0}
    
    query = supabase_admin.table("student_lifecycle_events").select("event_type", count="exact").eq("school_id", school_id)
    
    if year:
        query = query.gte("event_date", f"{year}-01-01").lte("event_date", f"{year}-12-31")
    
    result = query.execute()
    
    stats = {"admissions": 0, "promotions": 0, "transfers": 0, "graduations": 0, "withdrawals": 0}
    for event in result.data:
        event_type = event["event_type"]
        if event_type == "admission":
            stats["admissions"] += 1
        elif event_type == "promotion":
            stats["promotions"] += 1
        elif event_type == "transfer":
            stats["transfers"] += 1
        elif event_type == "graduation":
            stats["graduations"] += 1
        elif event_type == "withdrawal":
            stats["withdrawals"] += 1
    
    return stats


@router.post("/promote-students")
async def bulk_promote_students(
    promotion_data: Dict[str, Any],
    current_user: dict = Depends(require_office_admin),
):
    """Bulk promote students to next grade"""
    school_id = current_user.get("school_id")
    user_id = current_user.get("id")
    
    student_ids: List[str] = promotion_data["student_ids"]
    to_grade_id: str = promotion_data["to_grade_id"]
    event_date: str = promotion_data.get("event_date", date.today().isoformat())
    
    if not supabase_admin:
        return {"promoted": len(student_ids)}
    
    promoted_count = 0
    
    for student_id in student_ids:
        # Get current grade
        student = supabase_admin.table("students").select("grade_id").eq("id", student_id).eq("school_id", school_id).execute()
        if not student.data:
            continue
        
        from_grade_id = student.data[0].get("grade_id")
        
        # Update student grade
        supabase_admin.table("students").update({"grade_id": to_grade_id}).eq("id", student_id).execute()
        
        # Record lifecycle event
        supabase_admin.table("student_lifecycle_events").insert({
            "school_id": school_id,
            "student_id": student_id,
            "event_type": "promotion",
            "from_grade_id": from_grade_id,
            "to_grade_id": to_grade_id,
            "event_date": event_date,
            "recorded_by": user_id
        }).execute()
        
        promoted_count += 1
    
    return {"promoted": promoted_count}


@router.post("/graduate-students")
async def bulk_graduate_students(
    graduation_data: Dict[str, Any],
    current_user: dict = Depends(require_office_admin),
):
    """Bulk graduate students"""
    school_id = current_user.get("school_id")
    user_id = current_user.get("id")
    
    student_ids: List[str] = graduation_data["student_ids"]
    event_date: str = graduation_data.get("event_date", date.today().isoformat())
    
    if not supabase_admin:
        return {"graduated": len(student_ids)}
    
    graduated_count = 0
    
    for student_id in student_ids:
        # Update student status
        supabase_admin.table("students").update({"status": "graduated"}).eq("id", student_id).eq("school_id", school_id).execute()
        
        # Record lifecycle event
        supabase_admin.table("student_lifecycle_events").insert({
            "school_id": school_id,
            "student_id": student_id,
            "event_type": "graduation",
            "from_status": "active",
            "to_status": "graduated",
            "event_date": event_date,
            "recorded_by": user_id
        }).execute()
        
        graduated_count += 1
    
    return {"graduated": graduated_count}
