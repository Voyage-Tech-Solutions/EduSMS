"""
EduCore Backend - Attendance API Endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional, List
from datetime import datetime, date

from app.models import (
    AttendanceCreate,
    AttendanceBulkCreate,
    AttendanceResponse,
    AttendanceStatus,
)
from app.core.security import get_current_user, require_teacher, require_authenticated
from app.db.supabase import supabase_admin


router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.get("", response_model=List[AttendanceResponse])
async def list_attendance(
    class_id: Optional[str] = None,
    student_id: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    status_filter: Optional[AttendanceStatus] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(require_teacher),
):
    """List attendance records with filters"""
    school_id = current_user.get("school_id")
    
    if supabase_admin:
        query = supabase_admin.table("attendance_records").select("*").eq("school_id", school_id)
        
        if class_id:
            # Get students in class first
            students = supabase_admin.table("students").select("id").eq("class_id", class_id).execute()
            student_ids = [s["id"] for s in students.data]
            query = query.in_("student_id", student_ids)
        
        if student_id:
            query = query.eq("student_id", student_id)
        if date_from:
            query = query.gte("date", date_from.isoformat())
        if date_to:
            query = query.lte("date", date_to.isoformat())
        if status_filter:
            query = query.eq("status", status_filter.value)
        
        result = query.range(skip, skip + limit - 1).order("date", desc=True).execute()
        return result.data
    else:
        return [
            {
                "id": "mock-attendance-1",
                "school_id": school_id,
                "student_id": "mock-student-1",
                "date": date.today().isoformat(),
                "status": "present",
                "notes": None,
                "recorded_by": current_user["id"],
                "created_at": datetime.now().isoformat(),
            }
        ]


@router.post("", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
async def record_attendance(
    attendance_data: AttendanceCreate,
    current_user: dict = Depends(require_teacher),
):
    """Record individual attendance"""
    school_id = current_user.get("school_id")
    user_id = current_user.get("id")
    
    attendance_dict = {
        "school_id": school_id,
        "student_id": attendance_data.student_id,
        "date": attendance_data.date.isoformat(),
        "status": attendance_data.status.value,
        "notes": attendance_data.notes,
        "recorded_by": user_id,
    }
    
    if supabase_admin:
        # Verify student belongs to school
        student = supabase_admin.table("students").select("id").eq("id", attendance_data.student_id).eq("school_id", school_id).execute()
        
        if not student.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        # Check for existing record
        existing = supabase_admin.table("attendance_records").select("id").eq("student_id", attendance_data.student_id).eq("date", attendance_data.date.isoformat()).execute()
        
        if existing.data:
            # Update existing
            result = supabase_admin.table("attendance_records").update({
                "status": attendance_data.status.value,
                "notes": attendance_data.notes,
                "recorded_by": user_id,
            }).eq("id", existing.data[0]["id"]).execute()
        else:
            result = supabase_admin.table("attendance_records").insert(attendance_dict).execute()
        
        return result.data[0]
    else:
        return {**attendance_dict, "id": "mock-new-attendance", "created_at": datetime.now().isoformat()}


@router.post("/bulk", response_model=List[AttendanceResponse], status_code=status.HTTP_201_CREATED)
async def record_bulk_attendance(
    bulk_data: AttendanceBulkCreate,
    current_user: dict = Depends(require_teacher),
):
    """Record attendance for entire class at once"""
    school_id = current_user.get("school_id")
    user_id = current_user.get("id")
    
    if supabase_admin:
        # Verify class exists and belongs to school
        class_check = supabase_admin.table("classes").select("id").eq("id", bulk_data.class_id).eq("school_id", school_id).execute()
        
        if not class_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found"
            )
        
        records = []
        for record in bulk_data.records:
            attendance_dict = {
                "school_id": school_id,
                "student_id": record["student_id"],
                "date": bulk_data.date.isoformat(),
                "status": record["status"],
                "notes": record.get("notes"),
                "recorded_by": user_id,
            }
            records.append(attendance_dict)
        
        # Upsert records
        result = supabase_admin.table("attendance_records").upsert(
            records,
            on_conflict="student_id,date"
        ).execute()
        
        return result.data
    else:
        return [
            {
                "id": f"mock-attendance-{i}",
                "school_id": school_id,
                "student_id": r["student_id"],
                "date": bulk_data.date.isoformat(),
                "status": r["status"],
                "notes": r.get("notes"),
                "recorded_by": user_id,
                "created_at": datetime.now().isoformat(),
            }
            for i, r in enumerate(bulk_data.records)
        ]


@router.get("/summary")
async def get_attendance_summary(
    class_id: Optional[str] = None,
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = None,
    current_user: dict = Depends(require_teacher),
):
    """Get attendance summary statistics"""
    school_id = current_user.get("school_id")
    
    if not year:
        year = datetime.now().year
    if not month:
        month = datetime.now().month
    
    # Calculate date range
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    
    if supabase_admin:
        query = supabase_admin.table("attendance_records").select("status").eq("school_id", school_id).gte("date", start_date.isoformat()).lt("date", end_date.isoformat())
        
        if class_id:
            students = supabase_admin.table("students").select("id").eq("class_id", class_id).execute()
            student_ids = [s["id"] for s in students.data]
            query = query.in_("student_id", student_ids)
        
        result = query.execute()
        
        # Calculate stats
        total = len(result.data)
        present = sum(1 for r in result.data if r["status"] == "present")
        absent = sum(1 for r in result.data if r["status"] == "absent")
        late = sum(1 for r in result.data if r["status"] == "late")
        excused = sum(1 for r in result.data if r["status"] == "excused")
        
        return {
            "period": {"year": year, "month": month},
            "total_records": total,
            "present": present,
            "absent": absent,
            "late": late,
            "excused": excused,
            "attendance_rate": round((present + late) / total * 100, 2) if total > 0 else 0,
        }
    else:
        return {
            "period": {"year": year, "month": month},
            "total_records": 100,
            "present": 85,
            "absent": 10,
            "late": 3,
            "excused": 2,
            "attendance_rate": 88.0,
        }


@router.get("/chronic-absentees")
async def get_chronic_absentees(
    threshold: int = Query(5, ge=1, description="Minimum absences to be flagged"),
    days: int = Query(30, ge=7, le=90, description="Look-back period in days"),
    current_user: dict = Depends(require_teacher),
):
    """Get list of students with chronic absenteeism"""
    school_id = current_user.get("school_id")
    
    from datetime import timedelta
    start_date = (date.today() - timedelta(days=days)).isoformat()
    
    if supabase_admin:
        # Get absent counts per student
        result = supabase_admin.rpc(
            "get_chronic_absentees",
            {"p_school_id": school_id, "p_start_date": start_date, "p_threshold": threshold}
        ).execute()
        
        return result.data if result.data else []
    else:
        return [
            {
                "student_id": "mock-student-1",
                "student_name": "John Doe",
                "class_name": "Grade 5A",
                "absences": 7,
                "attendance_rate": 76.5,
            }
        ]


# ============== PARENT/STUDENT VIEW ==============

@router.get("/my-attendance", response_model=List[AttendanceResponse])
async def get_my_attendance(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = None,
    current_user: dict = Depends(require_authenticated),
):
    """Get attendance for parent's children or student's own attendance"""
    user_id = current_user.get("id")
    role = current_user.get("role")
    
    if role not in ["parent", "student"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is for parents and students only"
        )
    
    if not year:
        year = datetime.now().year
    if not month:
        month = datetime.now().month
    
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    
    if supabase_admin:
        if role == "student":
            student = supabase_admin.table("students").select("id").eq("user_id", user_id).execute()
            if student.data:
                result = supabase_admin.table("attendance_records").select("*").eq("student_id", student.data[0]["id"]).gte("date", start_date.isoformat()).lt("date", end_date.isoformat()).execute()
                return result.data
        else:
            guardians = supabase_admin.table("guardians").select("student_id").eq("user_id", user_id).execute()
            if guardians.data:
                student_ids = [g["student_id"] for g in guardians.data]
                result = supabase_admin.table("attendance_records").select("*").in_("student_id", student_ids).gte("date", start_date.isoformat()).lt("date", end_date.isoformat()).execute()
                return result.data
    
    return []
