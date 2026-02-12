from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import date, datetime, timedelta
from app.core.auth import get_current_user, get_user_school_id
from app.db.supabase_client import get_supabase_client

router = APIRouter()

# ============================================================
# PRINCIPAL STUDENTS (OVERSIGHT MODE)
# ============================================================

@router.get("/students/summary")
async def get_students_summary(
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    school_id = get_user_school_id(user)
    
    total = supabase.table("students").select("id", count="exact").eq("school_id", school_id).execute()
    active = supabase.table("students").select("id", count="exact").eq("school_id", school_id).eq("status", "active").execute()
    inactive = supabase.table("students").select("id", count="exact").eq("school_id", school_id).eq("status", "inactive").execute()
    transferred = supabase.table("students").select("id", count="exact").eq("school_id", school_id).eq("status", "transferred").execute()
    
    risk_cases = supabase.table("risk_cases").select("id", count="exact").eq("school_id", school_id).eq("status", "open").execute()
    
    attendance = supabase.table("attendance_records").select("student_id, status").eq("school_id", school_id).gte("date", (date.today() - timedelta(days=30)).isoformat()).execute()
    chronic_absent = len(set([r["student_id"] for r in attendance.data if r["status"] == "absent"]))
    
    return {
        "total": total.count or 0,
        "active": active.count or 0,
        "inactive": inactive.count or 0,
        "transferred": transferred.count or 0,
        "at_risk": risk_cases.count or 0,
        "chronic_absent": chronic_absent
    }

@router.get("/students")
async def get_students(
    search: Optional[str] = None,
    grade: Optional[str] = None,
    status: str = "active",
    risk: Optional[str] = None,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    school_id = get_user_school_id(user)
    
    query = supabase.table("students").select("*, grades(name)").eq("school_id", school_id)
    
    if status:
        query = query.eq("status", status)
    if grade:
        query = query.eq("grade_id", grade)
    if search:
        query = query.or_(f"first_name.ilike.%{search}%,last_name.ilike.%{search}%,admission_number.ilike.%{search}%")
    
    students = query.execute().data
    
    for student in students:
        attendance = supabase.table("attendance_records").select("status").eq("student_id", student["id"]).gte("date", (date.today() - timedelta(days=30)).isoformat()).execute()
        present = len([r for r in attendance.data if r["status"] in ["present", "late"]])
        student["attendance_rate"] = round((present / len(attendance.data) * 100), 1) if attendance.data else 0
        
        scores = supabase.table("assessment_scores").select("percentage").eq("student_id", student["id"]).execute()
        student["academic_avg"] = round(sum(s["percentage"] for s in scores.data) / len(scores.data), 1) if scores.data else None
        
        invoices = supabase.table("invoices").select("amount, amount_paid").eq("student_id", student["id"]).execute()
        student["outstanding"] = sum(inv["amount"] - inv["amount_paid"] for inv in invoices.data)
        
        student["grade_name"] = student.get("grades", {}).get("name", "")
    
    return students

@router.post("/students/risk")
async def create_student_risk(
    student_id: str,
    risk_type: str,
    severity: str,
    notes: str,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    school_id = get_user_school_id(user)
    
    data = {
        "school_id": school_id,
        "student_id": student_id,
        "risk_type": risk_type,
        "severity": severity,
        "notes": notes,
        "opened_by": user["id"],
        "status": "open"
    }
    
    return supabase.table("risk_cases").insert(data).execute().data[0]

@router.patch("/students/{student_id}/status")
async def update_student_status(
    student_id: str,
    status: str,
    reason: str,
    effective_date: date,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    school_id = get_user_school_id(user)
    
    supabase.table("students").update({"status": status}).eq("id", student_id).execute()
    
    supabase.table("audit_logs").insert({
        "school_id": school_id,
        "user_id": user["id"],
        "action": "UPDATE_STUDENT_STATUS",
        "resource_type": "student",
        "resource_id": student_id,
        "details": {"status": status, "reason": reason, "effective_date": effective_date.isoformat()}
    }).execute()
    
    return {"success": True}

# ============================================================
# PRINCIPAL REPORTS & ANALYTICS
# ============================================================

@router.get("/reports/summary")
async def get_reports_summary(
    range: str = "this_term",
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    school_id = get_user_school_id(user)
    
    students = supabase.table("students").select("id", count="exact").eq("school_id", school_id).eq("status", "active").execute()
    
    attendance = supabase.table("attendance_records").select("status").eq("school_id", school_id).execute()
    present = len([r for r in attendance.data if r["status"] in ["present", "late"]])
    avg_attendance = round((present / len(attendance.data) * 100), 1) if attendance.data else 0
    
    invoices = supabase.table("invoices").select("amount, amount_paid").eq("school_id", school_id).execute()
    total_billed = sum(inv["amount"] for inv in invoices.data)
    total_collected = sum(inv["amount_paid"] for inv in invoices.data)
    collection_rate = round((total_collected / total_billed * 100), 1) if total_billed > 0 else 0
    
    scores = supabase.table("assessment_scores").select("percentage").execute()
    academic_avg = round(sum(s["percentage"] for s in scores.data) / len(scores.data), 1) if scores.data else 0
    
    return {
        "total_enrollment": students.count or 0,
        "avg_attendance": avg_attendance,
        "fee_collection": total_collected,
        "collection_rate": collection_rate,
        "academic_avg": academic_avg
    }

@router.post("/reports/generate")
async def generate_report(
    type: str,
    filters: dict,
    range: str,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    school_id = get_user_school_id(user)
    
    supabase.table("audit_logs").insert({
        "school_id": school_id,
        "user_id": user["id"],
        "action": "GENERATE_REPORT",
        "resource_type": "report",
        "details": {"type": type, "filters": filters, "range": range}
    }).execute()
    
    return {"success": True, "message": "Report generated"}

# ============================================================
# PRINCIPAL APPROVALS
# ============================================================

@router.get("/approvals/summary")
async def get_approvals_summary(
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    school_id = get_user_school_id(user)
    
    total_pending = supabase.table("approval_requests").select("id", count="exact").eq("school_id", school_id).eq("status", "pending").execute()
    high_priority = supabase.table("approval_requests").select("id", count="exact").eq("school_id", school_id).eq("status", "pending").eq("priority", "high").execute()
    
    today = date.today().isoformat()
    approved_today = supabase.table("approval_requests").select("id", count="exact").eq("school_id", school_id).eq("status", "approved").gte("decided_at", today).execute()
    rejected_today = supabase.table("approval_requests").select("id", count="exact").eq("school_id", school_id).eq("status", "rejected").gte("decided_at", today).execute()
    
    return {
        "total_pending": total_pending.count or 0,
        "high_priority": high_priority.count or 0,
        "approved_today": approved_today.count or 0,
        "rejected_today": rejected_today.count or 0
    }

@router.get("/approvals")
async def get_approvals(
    status: str = "pending",
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    school_id = get_user_school_id(user)
    
    query = supabase.table("approval_requests").select("*, user_profiles!requested_by(first_name, last_name)").eq("school_id", school_id)
    
    if status == "high_priority":
        query = query.eq("status", "pending").eq("priority", "high")
    else:
        query = query.eq("status", status)
    
    approvals = query.order("submitted_at", desc=True).execute().data
    
    for approval in approvals:
        approval["submitted_by_name"] = f"{approval.get('user_profiles', {}).get('first_name', '')} {approval.get('user_profiles', {}).get('last_name', '')}"
    
    return approvals

@router.post("/approvals/{approval_id}/decision")
async def make_approval_decision(
    approval_id: str,
    decision: str,
    notes: str,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    school_id = get_user_school_id(user)
    
    supabase.table("approval_requests").update({
        "status": decision,
        "decision": decision,
        "decided_by": user["id"],
        "decided_at": datetime.now().isoformat(),
        "notes": notes
    }).eq("id", approval_id).execute()
    
    supabase.table("audit_logs").insert({
        "school_id": school_id,
        "user_id": user["id"],
        "action": "APPROVAL_DECISION",
        "resource_type": "approval",
        "resource_id": approval_id,
        "details": {"decision": decision, "notes": notes}
    }).execute()
    
    return {"success": True}
