from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from uuid import UUID
from datetime import date
from ..models.principal import (
    StudentOversightFilter, StudentOversightRow, FlagInterventionRequest,
    SendNotificationRequest, ChangeStatusRequest
)
from ..core.auth import get_current_user, get_user_school_id
from ..db.supabase import get_supabase_client

router = APIRouter(prefix="/principal/students", tags=["principal-students"])

@router.get("")
async def get_students_oversight(
    search: Optional[str] = None,
    grade_id: Optional[str] = None,
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    attendance_below: Optional[float] = None,
    academic_below: Optional[float] = None,
    overdue_fees: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get students with oversight metrics"""
    supabase = get_supabase_client()
    school_id = get_user_school_id(current_user)
    
    query = supabase.table("students").select("""
        id, admission_number, first_name, last_name, gender, status,
        grades(name), classes(name)
    """).eq("school_id", school_id)
    
    if search:
        query = query.or_(f"first_name.ilike.%{search}%,last_name.ilike.%{search}%,admission_number.ilike.%{search}%")
    if grade_id:
        query = query.eq("grade_id", grade_id)
    if status:
        query = query.eq("status", status)
    
    result = query.execute()
    
    # Get attendance and academic metrics
    students = []
    for student in result.data:
        # Get attendance %
        att_result = supabase.rpc("get_student_attendance_percentage", {
            "p_student_id": str(student["id"])
        }).execute()
        attendance_pct = att_result.data if att_result.data else 0.0
        
        # Get academic average
        grade_result = supabase.rpc("get_student_academic_average", {
            "p_student_id": str(student["id"])
        }).execute()
        academic_avg = grade_result.data if grade_result.data else 0.0
        
        # Get outstanding fees
        fee_result = supabase.table("invoices").select("amount, paid_amount").eq(
            "student_id", str(student["id"])
        ).eq("status", "pending").execute()
        outstanding = sum(inv["amount"] - inv["paid_amount"] for inv in fee_result.data)
        
        # Determine risk level
        risk_level = None
        if attendance_pct < 75:
            risk_level = "attendance"
        elif academic_avg < 50:
            risk_level = "academic"
        elif outstanding > 0:
            risk_level = "financial"
        
        # Apply filters
        if attendance_below and attendance_pct >= attendance_below:
            continue
        if academic_below and academic_avg >= academic_below:
            continue
        if overdue_fees and outstanding == 0:
            continue
        
        students.append({
            "id": student["id"],
            "admission_number": student["admission_number"],
            "name": f"{student['first_name']} {student['last_name']}",
            "grade": student["grades"]["name"] if student.get("grades") else "",
            "class_name": student["classes"]["name"] if student.get("classes") else "",
            "gender": student["gender"],
            "status": student["status"],
            "attendance_percentage": attendance_pct,
            "academic_average": academic_avg,
            "outstanding_fees": outstanding,
            "risk_level": risk_level
        })
    
    # Summary stats
    total = len(students)
    active = len([s for s in students if s["status"] == "active"])
    inactive = len([s for s in students if s["status"] == "inactive"])
    transferred = len([s for s in students if s["status"] == "transferred"])
    at_risk = len([s for s in students if s["risk_level"]])
    chronic_absent = len([s for s in students if s["attendance_percentage"] < 75])
    below_pass = len([s for s in students if s["academic_average"] < 50])
    
    return {
        "summary": {
            "total": total,
            "active": active,
            "inactive": inactive,
            "transferred": transferred,
            "at_risk": at_risk,
            "chronic_absentees": chronic_absent,
            "academic_below_pass": below_pass
        },
        "students": students
    }

@router.get("/{student_id}")
async def get_student_profile(
    student_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed student profile with trends"""
    supabase = get_supabase_client()
    school_id = get_user_school_id(current_user)
    
    # Get student details
    student = supabase.table("students").select("*").eq("id", str(student_id)).eq("school_id", school_id).single().execute()
    
    # Get attendance trend (last 30 days)
    att_trend = supabase.table("attendance").select("date, status").eq(
        "student_id", str(student_id)
    ).order("date", desc=True).limit(30).execute()
    
    # Get academic trend
    grade_trend = supabase.table("grades").select("*").eq("student_id", str(student_id)).execute()
    
    # Get fee history
    fee_history = supabase.table("invoices").select("*").eq("student_id", str(student_id)).execute()
    
    # Get interventions
    interventions = supabase.table("risk_cases").select("""
        *, interventions(*)
    """).eq("student_id", str(student_id)).execute()
    
    return {
        "student": student.data,
        "attendance_trend": att_trend.data,
        "academic_trend": grade_trend.data,
        "fee_history": fee_history.data,
        "interventions": interventions.data
    }

@router.post("/risk")
async def flag_for_intervention(
    request: FlagInterventionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Flag student for intervention"""
    supabase = get_supabase_client()
    school_id = get_user_school_id(current_user)
    
    # Create risk case
    risk_case = supabase.table("risk_cases").insert({
        "school_id": school_id,
        "student_id": str(request.student_id),
        "risk_type": request.risk_type,
        "severity": request.severity,
        "opened_by": current_user["id"],
        "status": "open",
        "notes": request.notes
    }).execute()
    
    # Create intervention
    if request.assigned_to:
        supabase.table("interventions").insert({
            "risk_case_id": risk_case.data[0]["id"],
            "intervention_type": f"{request.risk_type}_intervention",
            "assigned_to": str(request.assigned_to),
            "due_date": str(request.due_date) if request.due_date else None,
            "status": "pending"
        }).execute()
    
    return {"message": "Intervention flagged successfully", "risk_case_id": risk_case.data[0]["id"]}

@router.post("/notify")
async def send_parent_notification(
    request: SendNotificationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Send notification to parent"""
    supabase = get_supabase_client()
    school_id = get_user_school_id(current_user)
    
    notification = supabase.table("parent_notifications").insert({
        "school_id": school_id,
        "student_id": str(request.student_id),
        "sent_by": current_user["id"],
        "notification_type": request.template,
        "channel": request.channel,
        "include_performance_summary": request.include_performance,
        "message": f"Notification via {request.template}",
        "status": "pending"
    }).execute()
    
    return {"message": "Notification queued", "notification_id": notification.data[0]["id"]}

@router.patch("/status")
async def change_student_status(
    request: ChangeStatusRequest,
    current_user: dict = Depends(get_current_user)
):
    """Change student status"""
    supabase = get_supabase_client()
    school_id = get_user_school_id(current_user)
    
    # Update student status
    result = supabase.table("students").update({
        "status": request.new_status
    }).eq("id", str(request.student_id)).eq("school_id", school_id).execute()
    
    # Log audit
    supabase.table("audit_logs").insert({
        "school_id": school_id,
        "user_id": current_user["id"],
        "action": "change_student_status",
        "entity_type": "student",
        "entity_id": str(request.student_id),
        "after_state": {
            "status": request.new_status,
            "reason": request.reason,
            "effective_date": str(request.effective_date)
        }
    }).execute()
    
    return {"message": "Status updated successfully"}

@router.get("/export")
async def export_student_report(
    student_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """Export student report (PDF)"""
    return {"message": "Export functionality - implement with reportlab/weasyprint"}
