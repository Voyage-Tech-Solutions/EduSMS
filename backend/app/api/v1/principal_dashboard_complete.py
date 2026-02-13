from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import date, datetime, timedelta
from decimal import Decimal
from pydantic import BaseModel
from app.core.auth import get_current_user, get_user_school_id
from app.db.supabase import get_supabase_admin

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
    range: Optional[str] = "last_30_days",
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    
    # Calculate date range
    if range == "today":
        start_date = end_date = date.today()
    elif range == "this_week":
        start_date = date.today() - timedelta(days=date.today().weekday())
        end_date = date.today()
    elif range == "this_term":
        # Get current term
        term = supabase.table("terms").select("start_date, end_date").eq("school_id", school_id).eq("is_current", True).execute()
        if term.data:
            start_date = date.fromisoformat(term.data[0]["start_date"])
            end_date = date.fromisoformat(term.data[0]["end_date"])
    else:
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()
    
    # Total students
    students = supabase.table("students").select("id", count="exact").eq("school_id", school_id).eq("status", "active").execute()
    
    # Attendance rate
    attendance = supabase.table("attendance_records").select("status").eq("school_id", school_id).gte("date", start_date.isoformat()).lte("date", end_date.isoformat()).execute()
    present_count = len([r for r in attendance.data if r.get("status") in ["present", "late"]])
    attendance_rate = round((present_count / len(attendance.data) * 100), 1) if attendance.data else 0
    
    # At-risk students
    risk_cases = supabase.table("risk_cases").select("id", count="exact").eq("school_id", school_id).eq("status", "open").execute()
    
    # Finance metrics
    invoices = supabase.table("invoices").select("amount, amount_paid, due_date").eq("school_id", school_id).execute()
    total_billed = sum(float(inv.get("amount", 0)) for inv in invoices.data)
    total_collected = sum(float(inv.get("amount_paid", 0)) for inv in invoices.data)
    collection_rate = round((total_collected / total_billed * 100), 1) if total_billed > 0 else 0
    outstanding = total_billed - total_collected
    overdue_30 = sum(
        float(inv.get("amount", 0)) - float(inv.get("amount_paid", 0))
        for inv in invoices.data
        if inv.get("due_date") and (date.today() - date.fromisoformat(inv["due_date"])).days > 30
    )
    
    # Academic metrics
    assessments = supabase.table("assessments").select("id").eq("school_id", school_id).execute()
    scores = supabase.table("assessment_scores").select("percentage, assessment_id").execute()
    pass_count = len([s for s in scores.data if s.get("percentage", 0) >= 50])
    pass_rate = round((pass_count / len(scores.data) * 100), 1) if scores.data else None
    
    students_count = students.count or 0
    expected_entries = len(assessments.data) * students_count if students_count > 0 else 0
    completion_rate = round((len(scores.data) / expected_entries * 100), 1) if expected_entries > 0 else None
    
    reports = supabase.table("report_submissions").select("id, status").eq("school_id", school_id).gte("submitted_at", start_date.isoformat()).execute()
    submitted = len([r for r in reports.data if r.get("status") == "submitted"])
    
    # Staff metrics
    teachers = supabase.table("user_profiles").select("id", count="exact").eq("school_id", school_id).eq("role", "teacher").eq("is_active", True).execute()
    staff_perf = supabase.rpc("get_staff_performance", {"p_school_id": school_id}).execute()
    avg_marking = sum(float(s.get("marking_completion", 0)) for s in staff_perf.data) / len(staff_perf.data) if staff_perf.data else 0
    late_subs = sum(int(s.get("late_submissions", 0)) for s in staff_perf.data) if staff_perf.data else 0
    
    return {
        "total_students": students.count or 0,
        "attendance_rate": attendance_rate,
        "students_at_risk": risk_cases.count or 0,
        "fee_collection_rate": collection_rate,
        "outstanding_balance": round(outstanding, 2),
        "academic": {
            "pass_rate": pass_rate,
            "assessment_completion": completion_rate,
            "reports_submitted": submitted,
            "reports_expected": len(reports.data)
        },
        "finance": {
            "collection_rate": collection_rate,
            "outstanding": round(outstanding, 2),
            "overdue_30": round(overdue_30, 2)
        },
        "staff": {
            "active_teachers": teachers.count or 0,
            "marking_complete_rate": round(avg_marking, 1),
            "absent_today": 0,  # TODO: Implement staff attendance
            "late_submissions": late_subs
        }
    }

@router.get("/risk-cases")
async def get_risk_cases(
    status: Optional[str] = None,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    query = supabase.table("risk_cases").select("*, students(first_name, last_name, admission_number)").eq("school_id", school_id)
    if status:
        query = query.eq("status", status)
    return query.order("opened_at", desc=True).execute().data

@router.post("/risk-cases")
async def create_risk_case(
    case: RiskCaseCreate,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    data = {**case.dict(), "school_id": school_id, "opened_by": user["id"]}
    return supabase.table("risk_cases").insert(data).execute().data[0]

@router.post("/risk-cases/auto-detect")
async def auto_detect_risk_cases(
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    result = supabase.rpc("detect_at_risk_students", {"p_school_id": school_id}).execute()
    created = 0
    for risk in result.data:
        existing = supabase.table("risk_cases").select("id").eq("student_id", risk["student_id"]).eq("status", "open").execute()
        if not existing.data:
            supabase.table("risk_cases").insert({
                "school_id": school_id,
                "student_id": risk["student_id"],
                "risk_type": risk["risk_type"],
                "severity": risk["severity"],
                "notes": risk["reason"],
                "opened_by": user["id"]
            }).execute()
            created += 1
    return {"detected": len(result.data), "created": created}

@router.post("/interventions")
async def create_intervention(
    intervention: InterventionCreate,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    data = {**intervention.dict(), "created_by": user["id"]}
    return supabase.table("interventions").insert(data).execute().data[0]

@router.get("/academic/summary")
async def get_academic_summary(
    term_id: Optional[str] = None,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    assessments = supabase.table("assessments").select("id").eq("school_id", school_id).execute()
    scores = supabase.table("assessment_scores").select("percentage").execute()
    pass_count = len([s for s in scores.data if s.get("percentage", 0) >= 50])
    pass_rate = (pass_count / len(scores.data) * 100) if scores.data else 0
    reports = supabase.table("report_submissions").select("id, status").eq("school_id", school_id).execute()
    submitted = len([r for r in reports.data if r.get("status") == "submitted"])
    return {
        "pass_rate": round(pass_rate, 1),
        "assessment_completion": {
            "recorded_entries": len(scores.data),
            "expected_entries": len(assessments.data) * 30,
            "completion_rate": round((len(scores.data) / (len(assessments.data) * 30) * 100), 1) if assessments.data else 0
        },
        "reports_submitted": {
            "submitted": submitted,
            "expected": len(reports.data),
            "rate": round((submitted / len(reports.data) * 100), 1) if reports.data else 0
        }
    }

@router.get("/academic/grades")
async def get_grade_performance(
    term_id: Optional[str] = None,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    return supabase.rpc("get_grade_performance", {"p_school_id": school_id, "p_term_id": term_id}).execute().data

@router.get("/academic/subjects")
async def get_subject_rankings(
    term_id: Optional[str] = None,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    return supabase.rpc("get_subject_rankings", {"p_school_id": school_id, "p_term_id": term_id}).execute().data

@router.get("/academic/teachers")
async def get_teacher_performance(
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    return supabase.rpc("get_staff_performance", {"p_school_id": school_id}).execute().data

@router.post("/academic/reminders/marking")
async def send_marking_reminder(
    target_group: str,
    deadline: date,
    message: str,
    channel: str,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    supabase.table("notifications_log").insert({
        "school_id": school_id,
        "recipient_type": "teacher",
        "delivery_method": channel,
        "message_type": "marking_reminder",
        "subject": "Marking Completion Request",
        "message": message,
        "status": "sent"
    }).execute()
    return {"success": True}

@router.get("/attendance/summary")
async def get_attendance_summary(
    date: Optional[date] = Query(default=None),
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    """Get attendance summary for a date"""
    try:
        school_id = get_user_school_id(user)
        target_date = date.isoformat() if date else datetime.now().date().isoformat()
        
        records = supabase.table("attendance_records").select("status").eq("school_id", school_id).eq("date", target_date).execute().data
        
        if not records:
            return {
                "present": 0,
                "absent": 0,
                "late": 0,
                "excused": 0,
                "attendance_rate": 0
            }
        
        present = len([r for r in records if r["status"] == "present"])
        absent = len([r for r in records if r["status"] == "absent"])
        late = len([r for r in records if r["status"] == "late"])
        excused = len([r for r in records if r["status"] == "excused"])
        total = len(records)
        
        return {
            "present": present,
            "absent": absent,
            "late": late,
            "excused": excused,
            "attendance_rate": round(((present + late) / total * 100), 1) if total > 0 else 0
        }
    except Exception as e:
        print(f"Error in get_attendance_summary: {str(e)}")
        return {
            "present": 0,
            "absent": 0,
            "late": 0,
            "excused": 0,
            "attendance_rate": 0
        }

@router.get("/attendance/classes")
async def get_attendance_by_classes(
    date: Optional[date] = Query(default=None),
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    """Get attendance breakdown by class for a given date"""
    school_id = get_user_school_id(user)
    target_date = date.isoformat() if date else datetime.now().date().isoformat()

    classes = supabase.table("classes").select(
        "id, name, grade_id, grades(name)"
    ).eq("school_id", school_id).execute().data

    result = []
    for cls in classes:
        students = supabase.table("students").select("id").eq(
            "class_id", cls["id"]
        ).eq("status", "active").execute().data
        student_ids = [s["id"] for s in students]

        if not student_ids:
            continue

        attendance = supabase.table("attendance_records").select(
            "status"
        ).in_("student_id", student_ids).eq("date", target_date).execute().data

        submitted = len(attendance) > 0
        present = len([a for a in attendance if a["status"] in ("present", "late")])
        absent = len([a for a in attendance if a["status"] == "absent"])
        rate = round((present / len(attendance) * 100), 1) if attendance else 0

        grade_name = cls.get("grades", {}).get("name", "N/A") if cls.get("grades") else "N/A"

        result.append({
            "id": cls["id"],
            "name": cls["name"],
            "grade": grade_name,
            "teacher": "—",
            "submitted": submitted,
            "total_students": len(student_ids),
            "attendance_rate": rate,
            "absent": absent,
        })

    return result

@router.get("/attendance/missing-submissions")
async def get_missing_submissions(
    date: date = Query(default_factory=date.today),
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    return supabase.rpc("get_missing_attendance_submissions", {"p_school_id": school_id, "p_date": date.isoformat()}).execute().data

@router.post("/attendance/reminders")
async def send_attendance_reminder(
    target_group: str,
    deadline: str,
    message: str,
    channel: str,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    supabase.table("notifications_log").insert({
        "school_id": school_id,
        "recipient_type": "teacher",
        "delivery_method": channel,
        "message_type": "attendance_reminder",
        "subject": "Attendance Submission Reminder",
        "message": message,
        "status": "sent",
        "sent_by": user["id"]
    }).execute()
    return {"success": True, "message": "Reminders sent successfully"}

@router.get("/export-dashboard")
async def export_dashboard(
    range: str = "last_30_days",
    format: str = "pdf",
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    # Get summary data
    summary = await get_principal_summary(range=range, user=user, supabase=supabase)
    
    # Log export
    supabase.table("audit_logs").insert({
        "school_id": school_id,
        "user_id": user["id"],
        "action": "EXPORT_DASHBOARD",
        "resource_type": "principal_dashboard",
        "details": {"range": range, "format": format}
    }).execute()
    
    # Return data for PDF generation (frontend handles PDF generation)
    return {"success": True, "data": summary, "format": format}

@router.get("/finance/summary")
async def get_finance_summary(
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    invoices = supabase.table("invoices").select("amount, amount_paid, due_date").eq("school_id", school_id).execute()
    total_billed = sum(inv.get("amount", 0) for inv in invoices.data)
    total_collected = sum(inv.get("amount_paid", 0) for inv in invoices.data)
    overdue_30 = sum(inv.get("amount", 0) - inv.get("amount_paid", 0) for inv in invoices.data if (date.today() - date.fromisoformat(inv["due_date"])).days > 30)
    return {
        "total_billed": total_billed,
        "total_collected": total_collected,
        "collection_rate": round((total_collected / total_billed * 100), 1) if total_billed > 0 else 0,
        "outstanding": total_billed - total_collected,
        "overdue_30": overdue_30
    }

@router.get("/finance/arrears")
async def get_arrears(
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    cutoff = (date.today() - timedelta(days=30)).isoformat()
    return supabase.table("invoices").select("*, students(first_name, last_name)").eq("school_id", school_id).lt("due_date", cutoff).execute().data

@router.post("/finance/writeoff")
async def create_writeoff(
    invoice_id: str,
    amount: float,
    reason: str,
    notes: Optional[str] = None,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    data = {"invoice_id": invoice_id, "adjustment_type": "writeoff", "amount": amount, "reason": reason, "notes": notes, "approved_by": user["id"]}
    return supabase.table("invoice_adjustments").insert(data).execute().data[0]

@router.get("/staff")
async def get_staff(
    role: Optional[str] = None,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    query = supabase.table("user_profiles").select("*").eq("school_id", school_id)
    if role:
        query = query.eq("role", role)
    return query.order("first_name").execute().data

@router.post("/finance/payment-plan")
async def create_payment_plan(
    invoice_id: str,
    installment_count: int,
    installment_amount: float,
    start_date: date,
    notes: Optional[str] = None,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    data = {
        "invoice_id": invoice_id,
        "installment_count": installment_count,
        "installment_amount": installment_amount,
        "start_date": start_date.isoformat(),
        "status": "active",
        "notes": notes,
        "created_by": user["id"]
    }
    return supabase.table("payment_plans").insert(data).execute().data[0]

@router.post("/finance/reminders")
async def send_finance_reminder(
    target_group: str,
    message: str,
    channel: str,
    min_balance: Optional[float] = None,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    supabase.table("notifications_log").insert({
        "school_id": school_id,
        "recipient_type": "parent",
        "delivery_method": channel,
        "message_type": "payment_reminder",
        "subject": "Payment Reminder",
        "message": message,
        "status": "sent",
        "sent_by": user["id"]
    }).execute()
    return {"success": True, "message": "Payment reminders sent"}

@router.post("/staff")
async def create_staff(
    first_name: str,
    last_name: str,
    email: str,
    phone: Optional[str] = None,
    role: str = "teacher",
    department: Optional[str] = None,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    data = {
        "school_id": school_id,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "role": role,
        "department": department,
        "is_active": True
    }
    return supabase.table("user_profiles").insert(data).execute().data[0]

@router.patch("/staff/{staff_id}")
async def update_staff(
    staff_id: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    role: Optional[str] = None,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    data = {k: v for k, v in {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "role": role
    }.items() if v is not None}
    return supabase.table("user_profiles").update(data).eq("id", staff_id).execute().data[0]

@router.post("/staff/{staff_id}/deactivate")
async def deactivate_staff(
    staff_id: str,
    reason: str,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    supabase.table("user_profiles").update({"is_active": False}).eq("id", staff_id).execute()
    supabase.table("audit_logs").insert({
        "school_id": school_id,
        "user_id": user["id"],
        "action": "DEACTIVATE_STAFF",
        "resource_type": "staff",
        "resource_id": staff_id,
        "details": {"reason": reason}
    }).execute()
    return {"success": True}
