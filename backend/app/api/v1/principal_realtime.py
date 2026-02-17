"""
Principal Dashboard Real-Time API
Rule: Every action writes to DB first, then returns created record
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.security import get_current_user
from app.db.supabase import supabase_admin

router = APIRouter(prefix="/principal-realtime", tags=["Principal Real-Time"])

# ============================================
# MODELS
# ============================================

class RiskCaseCreate(BaseModel):
    student_id: str
    risk_type: str  # attendance/academic/finance/behavior/multi
    severity: str  # low/moderate/high
    notes: str
    assigned_to_user_id: Optional[str] = None

class MarkingRequestCreate(BaseModel):
    target_scope: str  # teacher/class/grade/subject
    teacher_id: Optional[str] = None
    grade_id: Optional[str] = None
    class_id: Optional[str] = None
    subject_id: Optional[str] = None
    term_id: Optional[str] = None
    message: str
    due_at: Optional[datetime] = None

class KPITargetCreate(BaseModel):
    year: int
    pass_rate_target: float = 75.0
    assessment_completion_target: float = 95.0
    attendance_target: float = 90.0

# ============================================
# STUDENT SEARCH (Real search, not ID-only)
# ============================================

@router.get("/students/search")
async def search_students(
    q: str = Query(..., min_length=2),
    grade_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Search students by name, not just ID
    Uses full-text search + filters
    """
    if not supabase_admin:
        return []
    
    school_id = current_user.get("school_id")
    
    # Build query with ilike for partial matching
    query = supabase_admin.table("students").select(
        "id, first_name, last_name, admission_number, grade_id, class_id, status, grades(name)"
    ).eq("school_id", school_id).eq("status", "active")
    
    # Search in first_name, last_name, or admission_number
    query = query.or_(f"first_name.ilike.%{q}%,last_name.ilike.%{q}%,admission_number.ilike.%{q}%")
    
    if grade_id:
        query = query.eq("grade_id", grade_id)
    
    result = query.limit(50).execute()
    
    return result.data

# ============================================
# RISK CASES (Persist to DB)
# ============================================

@router.post("/risk-cases")
async def create_risk_case(
    risk_case: RiskCaseCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create risk case - WRITES TO DB FIRST
    Returns created record
    """
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Database unavailable")
    
    school_id = current_user.get("school_id")
    user_id = current_user.get("id")
    
    # Insert into database
    result = supabase_admin.table("risk_cases").insert({
        "school_id": school_id,
        "student_id": risk_case.student_id,
        "risk_type": risk_case.risk_type,
        "severity": risk_case.severity,
        "notes": risk_case.notes,
        "assigned_to_user_id": risk_case.assigned_to_user_id,
        "created_by": user_id,
        "status": "open"
    }).execute()
    
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create risk case")
    
    # Return the created record
    return result.data[0]

@router.get("/risk-cases")
async def list_risk_cases(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """List risk cases with filters"""
    if not supabase_admin:
        return []
    
    school_id = current_user.get("school_id")
    
    query = supabase_admin.table("risk_cases").select(
        "*, students(first_name, last_name, admission_number, grades(name))"
    ).eq("school_id", school_id)
    
    if status:
        query = query.eq("status", status)
    if severity:
        query = query.eq("severity", severity)
    
    result = query.order("created_at", desc=True).execute()
    
    return result.data

@router.patch("/risk-cases/{risk_case_id}")
async def update_risk_case(
    risk_case_id: str,
    status: Optional[str] = None,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Update risk case status"""
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Database unavailable")
    
    updates = {"updated_at": datetime.now().isoformat()}
    if status:
        updates["status"] = status
    if notes:
        updates["notes"] = notes
    
    result = supabase_admin.table("risk_cases").update(updates).eq("id", risk_case_id).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Risk case not found")
    
    return result.data[0]

# ============================================
# MARKING REQUESTS (Persist + Notify)
# ============================================

@router.post("/marking-requests")
async def create_marking_request(
    request: MarkingRequestCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create marking request - WRITES TO DB FIRST
    Trigger automatically creates notifications for teachers
    """
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Database unavailable")
    
    school_id = current_user.get("school_id")
    user_id = current_user.get("id")
    
    # Insert into database (trigger handles notifications)
    result = supabase_admin.table("marking_requests").insert({
        "school_id": school_id,
        "requested_by": user_id,
        "target_scope": request.target_scope,
        "teacher_id": request.teacher_id,
        "grade_id": request.grade_id,
        "class_id": request.class_id,
        "subject_id": request.subject_id,
        "term_id": request.term_id,
        "message": request.message,
        "due_at": request.due_at.isoformat() if request.due_at else None,
        "status": "open"
    }).execute()
    
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create marking request")
    
    # Return the created record
    return result.data[0]

@router.get("/marking-requests")
async def list_marking_requests(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """List marking requests"""
    if not supabase_admin:
        return []
    
    school_id = current_user.get("school_id")
    
    query = supabase_admin.table("marking_requests").select("*").eq("school_id", school_id)
    
    if status:
        query = query.eq("status", status)
    
    result = query.order("created_at", desc=True).execute()
    
    return result.data

# ============================================
# NOTIFICATIONS (Read + Mark Read)
# ============================================

@router.get("/notifications")
async def get_notifications(
    unread_only: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Get user notifications"""
    if not supabase_admin:
        return []
    
    user_id = current_user.get("id")
    
    query = supabase_admin.table("notifications").select("*").eq("user_id", user_id)
    
    if unread_only:
        query = query.is_("read_at", "null")
    
    result = query.order("created_at", desc=True).limit(50).execute()
    
    return result.data

@router.patch("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark notification as read"""
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Database unavailable")
    
    result = supabase_admin.table("notifications").update({
        "read_at": datetime.now().isoformat()
    }).eq("id", notification_id).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return result.data[0]

# ============================================
# KPI TARGETS (Set targets)
# ============================================

@router.post("/kpi-targets")
async def set_kpi_targets(
    targets: KPITargetCreate,
    current_user: dict = Depends(get_current_user)
):
    """Set KPI targets for the year"""
    if not supabase_admin:
        raise HTTPException(status_code=503, detail="Database unavailable")
    
    school_id = current_user.get("school_id")
    user_id = current_user.get("id")
    
    # Upsert (insert or update if exists)
    result = supabase_admin.table("kpi_targets").upsert({
        "school_id": school_id,
        "year": targets.year,
        "pass_rate_target": targets.pass_rate_target,
        "assessment_completion_target": targets.assessment_completion_target,
        "attendance_target": targets.attendance_target,
        "created_by": user_id,
        "updated_at": datetime.now().isoformat()
    }, on_conflict="school_id,year").execute()
    
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to set KPI targets")
    
    return result.data[0]

@router.get("/kpi-targets/{year}")
async def get_kpi_targets(
    year: int,
    current_user: dict = Depends(get_current_user)
):
    """Get KPI targets for a year"""
    if not supabase_admin:
        return None
    
    school_id = current_user.get("school_id")
    
    result = supabase_admin.table("kpi_targets").select("*").eq(
        "school_id", school_id
    ).eq("year", year).execute()
    
    return result.data[0] if result.data else None

# ============================================
# VIEWS: Read from DB views (not computed in frontend)
# ============================================

@router.get("/kpis/academics")
async def get_academic_kpis(current_user: dict = Depends(get_current_user)):
    """Get academic KPIs from view"""
    if not supabase_admin:
        return {}
    
    school_id = current_user.get("school_id")
    
    result = supabase_admin.table("v_kpi_academics").select("*").eq("school_id", school_id).execute()
    
    return result.data[0] if result.data else {}

@router.get("/kpis/finance")
async def get_finance_kpis(current_user: dict = Depends(get_current_user)):
    """Get finance KPIs from view"""
    if not supabase_admin:
        return {}
    
    school_id = current_user.get("school_id")
    
    result = supabase_admin.table("v_finance_kpis_principal").select("*").eq("school_id", school_id).execute()
    
    return result.data[0] if result.data else {}

@router.get("/kpis/reports")
async def get_reports_kpis(current_user: dict = Depends(get_current_user)):
    """Get reports KPIs from view"""
    if not supabase_admin:
        return {}
    
    school_id = current_user.get("school_id")
    
    result = supabase_admin.table("v_reports_kpis_principal").select("*").eq("school_id", school_id).execute()
    
    return result.data[0] if result.data else {}

@router.get("/performance/bands")
async def get_performance_bands(
    grade_id: Optional[str] = None,
    subject_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get performance bands from view"""
    if not supabase_admin:
        return []
    
    school_id = current_user.get("school_id")
    
    query = supabase_admin.table("v_performance_bands").select("*").eq("school_id", school_id)
    
    if grade_id:
        query = query.eq("grade_id", grade_id)
    if subject_id:
        query = query.eq("subject_id", subject_id)
    
    result = query.execute()
    
    return result.data

@router.get("/performance/students")
async def get_student_performance(
    grade_id: Optional[str] = None,
    subject_id: Optional[str] = None,
    performance_band: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get student performance details from view"""
    if not supabase_admin:
        return []
    
    school_id = current_user.get("school_id")
    
    query = supabase_admin.table("v_student_performance").select("*").eq("school_id", school_id)
    
    if grade_id:
        query = query.eq("grade_id", grade_id)
    if subject_id:
        query = query.eq("subject_id", subject_id)
    if performance_band:
        query = query.eq("performance_band", performance_band)
    
    result = query.limit(100).execute()
    
    return result.data

@router.get("/arrears")
async def get_arrears_list(current_user: dict = Depends(get_current_user)):
    """Get arrears list from view"""
    if not supabase_admin:
        return []
    
    school_id = current_user.get("school_id")
    
    result = supabase_admin.table("v_arrears_list").select("*").eq("school_id", school_id).limit(100).execute()
    
    return result.data

# ============================================
# STAFF LIST (Teachers + Office Admin only)
# ============================================

@router.get("/staff")
async def list_staff(
    role: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """List staff (teachers and office admin only, no parents)"""
    if not supabase_admin:
        return []
    
    school_id = current_user.get("school_id")
    
    query = supabase_admin.table("user_profiles").select("*").eq(
        "school_id", school_id
    ).in_("role", ["teacher", "office_admin"])
    
    if role:
        query = query.eq("role", role)
    
    result = query.order("first_name").execute()
    
    return result.data
