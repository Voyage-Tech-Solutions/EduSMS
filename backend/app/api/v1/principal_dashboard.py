from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import date, datetime, timedelta
from pydantic import BaseModel
from app.core.auth import get_current_user, get_user_school_id
from app.db.supabase_client import get_supabase_client

router = APIRouter()

class RiskCaseCreate(BaseModel):
    student_id: str
    risk_type: str
    severity: str
    assigned_to: Optional[str] = None
    notes: Optional[str] = None

class InterventionCreate(BaseModel):
    risk_case_id: str
    intervention_type: str
    assigned_to: str
    due_date: date
    notes: str

@router.get("/summary")
async def get_principal_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    term_id: Optional[str] = None,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    school_id = get_user_school_id(user)
    
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()
    
    # Total students
    students = supabase.table("students").select("id", count="exact").eq("school_id", school_id).eq("status", "active").execute()
    total_students = students.count or 0
    
    # Attendance rate
    attendance = supabase.table("attendance_records").select("status", count="exact").eq("school_id", school_id).gte("date", start_date.isoformat()).lte("date", end_date.isoformat()).execute()
    present_count = len([r for r in attendance.data if r.get("status") in ["present", "late"]])
    attendance_rate = (present_count / len(attendance.data) * 100) if attendance.data else 0
    
    # At risk students
    risk_cases = supabase.table("risk_cases").select("id", count="exact").eq("school_id", school_id).eq("status", "open").execute()
    students_at_risk = risk_cases.count or 0
    
    # Fee collection
    invoices = supabase.table("invoices").select("amount, amount_paid").eq("school_id", school_id).execute()
    total_billed = sum(inv.get("amount", 0) for inv in invoices.data)
    total_collected = sum(inv.get("amount_paid", 0) for inv in invoices.data)
    collection_rate = (total_collected / total_billed * 100) if total_billed > 0 else 0
    outstanding = total_billed - total_collected
    
    return {
        "total_students": total_students,
        "attendance_rate": round(attendance_rate, 1),
        "students_at_risk": students_at_risk,
        "fee_collection_rate": round(collection_rate, 1),
        "outstanding_balance": outstanding,
        "academic": {
            "pass_rate": 0,
            "assessment_completion": 0,
            "reports_submitted": 0,
            "reports_expected": 0
        },
        "finance": {
            "collection_rate": round(collection_rate, 1),
            "outstanding": outstanding,
            "overdue_30": 0
        },
        "staff": {
            "active_teachers": 0,
            "marking_complete_rate": 0,
            "absent_today": 0,
            "late_submissions": 0
        }
    }

@router.get("/risk-cases")
async def get_risk_cases(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    school_id = get_user_school_id(user)
    query = supabase.table("risk_cases").select("*, students(first_name, last_name, admission_number)").eq("school_id", school_id)
    
    if status:
        query = query.eq("status", status)
    if severity:
        query = query.eq("severity", severity)
    
    result = query.order("opened_at", desc=True).execute()
    return result.data

@router.post("/risk-cases")
async def create_risk_case(
    case: RiskCaseCreate,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    school_id = get_user_school_id(user)
    data = {
        **case.dict(),
        "school_id": school_id,
        "opened_by": user["id"]
    }
    result = supabase.table("risk_cases").insert(data).execute()
    return result.data[0]

@router.post("/interventions")
async def create_intervention(
    intervention: InterventionCreate,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    data = {
        **intervention.dict(),
        "created_by": user["id"]
    }
    result = supabase.table("interventions").insert(data).execute()
    return result.data[0]

@router.get("/academic/summary")
async def get_academic_summary(
    term_id: Optional[str] = None,
    grade_id: Optional[str] = None,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    school_id = get_user_school_id(user)
    
    # Get assessments and scores
    assessments = supabase.table("assessments").select("id").eq("school_id", school_id).execute()
    scores = supabase.table("assessment_scores").select("score, percentage").execute()
    
    # Get report submissions
    reports = supabase.table("report_submissions").select("id, status").eq("school_id", school_id).execute()
    submitted = len([r for r in reports.data if r.get("status") == "submitted"])
    
    return {
        "pass_rate": 0,
        "assessment_completion": {
            "recorded_entries": len(scores.data),
            "expected_entries": 0,
            "completion_rate": 0
        },
        "reports_submitted": {
            "submitted": submitted,
            "expected": len(reports.data),
            "rate": (submitted / len(reports.data) * 100) if reports.data else 0
        }
    }

@router.get("/finance/arrears")
async def get_arrears(
    min_days: int = 30,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    school_id = get_user_school_id(user)
    cutoff_date = (date.today() - timedelta(days=min_days)).isoformat()
    
    result = supabase.table("invoices").select("*, students(first_name, last_name, admission_number)").eq("school_id", school_id).lt("due_date", cutoff_date).gt("amount_paid", 0).execute()
    return result.data

@router.post("/finance/writeoff")
async def create_writeoff(
    invoice_id: str,
    amount: float,
    reason: str,
    notes: Optional[str] = None,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    data = {
        "invoice_id": invoice_id,
        "adjustment_type": "writeoff",
        "amount": amount,
        "reason": reason,
        "notes": notes,
        "approved_by": user["id"]
    }
    result = supabase.table("invoice_adjustments").insert(data).execute()
    return result.data[0]

@router.get("/staff")
async def get_staff(
    role: Optional[str] = None,
    status: Optional[str] = "active",
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    school_id = get_user_school_id(user)
    query = supabase.table("user_profiles").select("*").eq("school_id", school_id)
    
    if role:
        query = query.eq("role", role)
    if status:
        query = query.eq("is_active", status == "active")
    
    result = query.order("first_name").execute()
    return result.data

@router.post("/staff/{staff_id}/deactivate")
async def deactivate_staff(
    staff_id: str,
    reason: str,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    result = supabase.table("user_profiles").update({"is_active": False}).eq("id", staff_id).execute()
    return {"success": True}
