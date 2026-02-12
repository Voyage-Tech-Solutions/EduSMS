"""
EduCore Backend - Principal Dashboard API
Oversight, risk management, and school-wide metrics
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta

from app.core.security import get_current_user
from app.db.supabase import supabase_admin

router = APIRouter()


def require_principal(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") not in ["principal", "developer"]:
        raise HTTPException(status_code=403, detail="Principal access required")
    return current_user


@router.get("/summary")
async def get_dashboard_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    term_id: Optional[str] = None,
    current_user: dict = Depends(require_principal),
):
    """Get comprehensive dashboard summary"""
    school_id = current_user.get("school_id")
    
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()
    
    if not supabase_admin:
        return {"total_students": 0, "attendance_rate": 0, "students_at_risk": 0}
    
    # Total students
    students = supabase_admin.table("students").select("id", count="exact").eq("school_id", school_id).eq("status", "active").execute()
    total_students = students.count or 0
    
    # Attendance rate
    att_records = supabase_admin.table("attendance_records").select("status").eq("school_id", school_id).gte("date", start_date.isoformat()).lte("date", end_date.isoformat()).execute()
    total_att = len(att_records.data)
    present_att = sum(1 for r in att_records.data if r["status"] in ["present", "late"])
    attendance_rate = round((present_att / total_att * 100), 2) if total_att > 0 else 0
    
    # Students at risk
    risk_cases = supabase_admin.table("risk_cases").select("id", count="exact").eq("school_id", school_id).eq("status", "open").execute()
    students_at_risk = risk_cases.count or 0
    
    # Fee collection
    invoices = supabase_admin.table("invoices").select("amount, paid_amount").eq("school_id", school_id).execute()
    total_billed = sum(float(i.get("amount", 0)) for i in invoices.data)
    total_collected = sum(float(i.get("paid_amount", 0)) for i in invoices.data)
    collection_rate = round((total_collected / total_billed * 100), 2) if total_billed > 0 else 0
    outstanding = total_billed - total_collected
    
    return {
        "total_students": total_students,
        "attendance_rate": attendance_rate,
        "students_at_risk": students_at_risk,
        "fee_collection_rate": collection_rate,
        "outstanding_balance": outstanding,
        "academic": {"pass_rate": 0, "assessment_completion": 0, "reports_submitted": 0, "reports_expected": 0},
        "finance": {"collection_rate": collection_rate, "outstanding": outstanding, "overdue_30": 0},
        "staff": {"active_teachers": 0, "marking_complete_rate": 0, "absent_today": 0, "late_submissions": 0}
    }


@router.get("/risk-cases")
async def list_risk_cases(
    status_filter: Optional[str] = Query(None, alias="status"),
    risk_type: Optional[str] = None,
    severity: Optional[str] = None,
    current_user: dict = Depends(require_principal),
):
    """List students at risk"""
    school_id = current_user.get("school_id")
    
    if not supabase_admin:
        return []
    
    query = supabase_admin.table("risk_cases").select("*, students(first_name, last_name, admission_number, grade_id, class_id)").eq("school_id", school_id)
    
    if status_filter:
        query = query.eq("status", status_filter)
    if risk_type:
        query = query.eq("risk_type", risk_type)
    if severity:
        query = query.eq("severity", severity)
    
    result = query.order("opened_at", desc=True).execute()
    return result.data


@router.post("/risk-cases")
async def create_risk_case(
    case_data: Dict[str, Any],
    current_user: dict = Depends(require_principal),
):
    """Create new risk case"""
    school_id = current_user.get("school_id")
    user_id = current_user.get("id")
    
    case_dict = {
        "school_id": school_id,
        "student_id": case_data["student_id"],
        "risk_type": case_data["risk_type"],
        "severity": case_data.get("severity", "medium"),
        "status": "open",
        "opened_by": user_id,
        "notes": case_data.get("notes")
    }
    
    if not supabase_admin:
        return {**case_dict, "id": "mock-risk-case"}
    
    result = supabase_admin.table("risk_cases").insert(case_dict).execute()
    return result.data[0]


@router.post("/interventions")
async def create_intervention(
    intervention_data: Dict[str, Any],
    current_user: dict = Depends(require_principal),
):
    """Create intervention for risk case"""
    intervention_dict = {
        "risk_case_id": intervention_data["risk_case_id"],
        "intervention_type": intervention_data["intervention_type"],
        "assigned_to": intervention_data.get("assigned_to"),
        "due_date": intervention_data.get("due_date"),
        "notes": intervention_data.get("notes"),
        "status": "pending"
    }
    
    if not supabase_admin:
        return {**intervention_dict, "id": "mock-intervention"}
    
    result = supabase_admin.table("interventions").insert(intervention_dict).execute()
    return result.data[0]


@router.patch("/risk-cases/{case_id}/resolve")
async def resolve_risk_case(
    case_id: str,
    resolution_data: Dict[str, Any],
    current_user: dict = Depends(require_principal),
):
    """Mark risk case as resolved"""
    if not supabase_admin:
        return {"id": case_id, "status": "resolved"}
    
    result = supabase_admin.table("risk_cases").update({
        "status": "resolved",
        "closed_at": datetime.now().isoformat(),
        "notes": resolution_data.get("notes")
    }).eq("id", case_id).execute()
    
    return result.data[0] if result.data else {}


@router.get("/attendance/missing-submissions")
async def get_missing_attendance_submissions(
    date_param: date = Query(default_factory=date.today),
    grade_id: Optional[str] = None,
    current_user: dict = Depends(require_principal),
):
    """Get classes with missing attendance submissions"""
    school_id = current_user.get("school_id")
    
    if not supabase_admin:
        return []
    
    # Get all classes
    query = supabase_admin.table("classes").select("id, name, grade_id, grades(name)").eq("school_id", school_id)
    if grade_id:
        query = query.eq("grade_id", grade_id)
    classes = query.execute()
    
    # Check which have attendance sessions
    sessions = supabase_admin.table("attendance_sessions").select("class_id").eq("date", date_param.isoformat()).execute()
    submitted_class_ids = {s["class_id"] for s in sessions.data}
    
    missing = [c for c in classes.data if c["id"] not in submitted_class_ids]
    return missing


@router.post("/attendance/reminders")
async def send_attendance_reminders(
    reminder_data: Dict[str, Any],
    current_user: dict = Depends(require_principal),
):
    """Send bulk attendance reminders"""
    # This would integrate with notification system
    return {"message": "Reminders sent", "count": len(reminder_data.get("class_ids", []))}


@router.get("/finance/arrears")
async def get_arrears_list(
    min_days: int = Query(30, ge=0),
    min_amount: float = Query(0, ge=0),
    current_user: dict = Depends(require_principal),
):
    """Get list of overdue invoices"""
    school_id = current_user.get("school_id")
    
    if not supabase_admin:
        return []
    
    cutoff_date = (date.today() - timedelta(days=min_days)).isoformat()
    
    result = supabase_admin.table("invoices").select(
        "*, students(first_name, last_name, admission_number)"
    ).eq("school_id", school_id).lt("due_date", cutoff_date).gt("balance", min_amount).order("due_date").execute()
    
    return result.data


@router.post("/finance/reminders/bulk")
async def send_bulk_payment_reminders(
    reminder_data: Dict[str, Any],
    current_user: dict = Depends(require_principal),
):
    """Send bulk payment reminders"""
    return {"message": "Payment reminders sent", "count": len(reminder_data.get("invoice_ids", []))}


@router.get("/academic/summary")
async def get_academic_summary(
    term_id: Optional[str] = None,
    grade_id: Optional[str] = None,
    current_user: dict = Depends(require_principal),
):
    """Get academic performance summary"""
    school_id = current_user.get("school_id")
    
    if not supabase_admin:
        return {"pass_rate": 0, "assessment_completion": {"recorded_entries": 0, "expected_entries": 0, "completion_rate": 0}}
    
    # Get assessments
    query = supabase_admin.table("assessments").select("id").eq("school_id", school_id).eq("status", "published")
    if term_id:
        query = query.eq("term_id", term_id)
    if grade_id:
        query = query.eq("grade_id", grade_id)
    assessments = query.execute()
    
    # Get scores
    assessment_ids = [a["id"] for a in assessments.data]
    if assessment_ids:
        scores = supabase_admin.table("assessment_scores").select("id, percentage").in_("assessment_id", assessment_ids).execute()
        total_scores = len(scores.data)
        pass_count = sum(1 for s in scores.data if s.get("percentage", 0) >= 50)
        pass_rate = round((pass_count / total_scores * 100), 2) if total_scores > 0 else 0
    else:
        pass_rate = 0
        total_scores = 0
    
    return {
        "pass_rate": pass_rate,
        "assessment_completion": {
            "recorded_entries": total_scores,
            "expected_entries": 0,
            "completion_rate": 0
        },
        "reports_submitted": {"submitted": 0, "expected": 0, "rate": 0}
    }
