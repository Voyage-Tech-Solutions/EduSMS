from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.core.auth import get_current_user
from app.db.supabase_client import get_supabase_client

router = APIRouter()

@router.get("/dashboard/metrics")
async def get_dashboard_metrics(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "principal":
        raise HTTPException(status_code=403, detail="Principal access required")
    
    supabase = get_supabase_client()
    school_id = current_user["school_id"]
    
    # Total students
    students = supabase.table("students").select("id, status", count="exact").eq("school_id", school_id).eq("status", "active").execute()
    total_students = students.count
    
    # Attendance rate (last 30 days)
    thirty_days_ago = (datetime.now() - timedelta(days=30)).date().isoformat()
    attendance = supabase.table("attendance_records").select("status").eq("school_id", school_id).gte("date", thirty_days_ago).execute()
    present_count = sum(1 for r in attendance.data if r["status"] in ["present", "late"])
    attendance_rate = round((present_count / len(attendance.data) * 100), 1) if attendance.data else 0
    
    # Students at risk (chronic absentees + discipline issues)
    chronic_absentees = supabase.rpc("get_chronic_absentees", {"p_school_id": school_id, "p_start_date": thirty_days_ago, "p_threshold": 5}).execute()
    discipline_students = supabase.table("discipline_incidents").select("student_id").eq("school_id", school_id).gte("incident_date", thirty_days_ago).execute()
    at_risk_count = len(set([r["student_id"] for r in chronic_absentees.data] + [r["student_id"] for r in discipline_students.data]))
    
    # Fee collection
    invoices = supabase.table("invoices").select("amount, amount_paid").eq("school_id", school_id).execute()
    total_expected = sum(float(i["amount"]) for i in invoices.data)
    total_collected = sum(float(i["amount_paid"]) for i in invoices.data)
    collection_rate = round((total_collected / total_expected * 100), 1) if total_expected > 0 else 0
    outstanding = total_expected - total_collected
    
    return {
        "total_students": total_students,
        "attendance_rate": attendance_rate,
        "at_risk_count": at_risk_count,
        "collection_rate": collection_rate,
        "outstanding_balance": round(outstanding, 2)
    }

@router.get("/alerts")
async def get_school_alerts(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "principal":
        raise HTTPException(status_code=403, detail="Principal access required")
    
    supabase = get_supabase_client()
    school_id = current_user["school_id"]
    alerts = []
    
    # Low attendance by grade
    grades = supabase.table("grades").select("id, name").eq("school_id", school_id).execute()
    for grade in grades.data:
        students_in_grade = supabase.table("students").select("id").eq("grade_id", grade["id"]).eq("status", "active").execute()
        if not students_in_grade.data:
            continue
        
        thirty_days_ago = (datetime.now() - timedelta(days=30)).date().isoformat()
        attendance = supabase.table("attendance_records").select("status").in_("student_id", [s["id"] for s in students_in_grade.data]).gte("date", thirty_days_ago).execute()
        present = sum(1 for r in attendance.data if r["status"] in ["present", "late"])
        rate = (present / len(attendance.data) * 100) if attendance.data else 0
        
        if rate < 90:
            alerts.append({"severity": "high", "message": f"Attendance below threshold in {grade['name']} ({rate:.1f}%)"})
    
    # At-risk students
    chronic_absentees = supabase.rpc("get_chronic_absentees", {"p_school_id": school_id, "p_start_date": (datetime.now() - timedelta(days=30)).date().isoformat(), "p_threshold": 5}).execute()
    if len(chronic_absentees.data) > 0:
        alerts.append({"severity": "high", "message": f"{len(chronic_absentees.data)} students flagged 'At Risk'"})
    
    # Fee collection
    invoices = supabase.table("invoices").select("amount, amount_paid").eq("school_id", school_id).execute()
    total_expected = sum(float(i["amount"]) for i in invoices.data)
    total_collected = sum(float(i["amount_paid"]) for i in invoices.data)
    rate = (total_collected / total_expected * 100) if total_expected > 0 else 100
    if rate < 85:
        alerts.append({"severity": "medium", "message": f"Fee collection below target ({rate:.1f}%)"})
    
    # Teachers not submitting marks
    teachers = supabase.table("user_profiles").select("id, first_name, last_name").eq("school_id", school_id).eq("role", "teacher").execute()
    teachers_with_entries = supabase.table("grade_entries").select("entered_by").eq("school_id", school_id).gte("created_at", (datetime.now() - timedelta(days=30)).isoformat()).execute()
    submitted_teachers = set(e["entered_by"] for e in teachers_with_entries.data if e["entered_by"])
    not_submitted = len([t for t in teachers.data if t["id"] not in submitted_teachers])
    if not_submitted > 0:
        alerts.append({"severity": "low", "message": f"{not_submitted} teachers haven't submitted marks"})
    
    return alerts[:10]

@router.get("/approvals")
async def get_pending_approvals(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "principal":
        raise HTTPException(status_code=403, detail="Principal access required")
    
    # Mock approval data - would need approval tables in real implementation
    return [
        {"type": "Fee Discounts", "count": 6, "priority": "high"},
        {"type": "Late Mark Changes", "count": 4, "priority": "medium"},
        {"type": "Student Transfers", "count": 2, "priority": "high"},
        {"type": "Disciplinary Cases", "count": 3, "priority": "high"}
    ]

@router.get("/academic/performance")
async def get_academic_performance(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "principal":
        raise HTTPException(status_code=403, detail="Principal access required")
    
    supabase = get_supabase_client()
    school_id = current_user["school_id"]
    
    # Pass rate calculation
    grade_entries = supabase.table("grade_entries").select("score, max_score").eq("school_id", school_id).execute()
    passing_grades = sum(1 for e in grade_entries.data if (float(e["score"]) / float(e["max_score"]) * 100) >= 50)
    pass_rate = round((passing_grades / len(grade_entries.data) * 100), 1) if grade_entries.data else 0
    
    # Assessment completion
    students = supabase.table("students").select("id").eq("school_id", school_id).eq("status", "active").execute()
    subjects = supabase.table("subjects").select("id").eq("school_id", school_id).execute()
    expected_entries = len(students.data) * len(subjects.data)
    actual_entries = len(grade_entries.data)
    completion_rate = round((actual_entries / expected_entries * 100), 1) if expected_entries > 0 else 0
    
    # Reports submitted
    teachers = supabase.table("user_profiles").select("id").eq("school_id", school_id).eq("role", "teacher").execute()
    teachers_with_entries = supabase.table("grade_entries").select("entered_by").eq("school_id", school_id).gte("created_at", (datetime.now() - timedelta(days=30)).isoformat()).execute()
    submitted = len(set(e["entered_by"] for e in teachers_with_entries.data if e["entered_by"]))
    
    return {
        "pass_rate": pass_rate,
        "completion_rate": completion_rate,
        "reports_submitted": submitted,
        "total_teachers": len(teachers.data)
    }

@router.get("/finance/overview")
async def get_finance_overview(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "principal":
        raise HTTPException(status_code=403, detail="Principal access required")
    
    supabase = get_supabase_client()
    school_id = current_user["school_id"]
    
    invoices = supabase.table("invoices").select("amount, amount_paid, due_date").eq("school_id", school_id).execute()
    
    total_expected = sum(float(i["amount"]) for i in invoices.data)
    total_collected = sum(float(i["amount_paid"]) for i in invoices.data)
    collection_rate = round((total_collected / total_expected * 100), 1) if total_expected > 0 else 0
    outstanding = total_expected - total_collected
    
    # Overdue calculation
    today = datetime.now().date()
    overdue = sum(float(i["amount"]) - float(i["amount_paid"]) for i in invoices.data if datetime.fromisoformat(i["due_date"].replace('Z', '+00:00')).date() < today and float(i["amount_paid"]) < float(i["amount"]))
    
    return {
        "collection_rate": collection_rate,
        "outstanding_balance": round(outstanding, 2),
        "overdue_amount": round(overdue, 2),
        "total_collected": round(total_collected, 2)
    }

@router.get("/staff/insight")
async def get_staff_insight(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "principal":
        raise HTTPException(status_code=403, detail="Principal access required")
    
    supabase = get_supabase_client()
    school_id = current_user["school_id"]
    
    teachers = supabase.table("user_profiles").select("id").eq("school_id", school_id).eq("role", "teacher").eq("is_active", True).execute()
    
    # Marking completion
    teachers_with_entries = supabase.table("grade_entries").select("entered_by").eq("school_id", school_id).gte("created_at", (datetime.now() - timedelta(days=30)).isoformat()).execute()
    submitted = len(set(e["entered_by"] for e in teachers_with_entries.data if e["entered_by"]))
    marking_complete = round((submitted / len(teachers.data) * 100), 1) if teachers.data else 0
    
    # Late submissions (teachers who haven't submitted in 30 days)
    late_submissions = len(teachers.data) - submitted
    
    return {
        "active_teachers": len(teachers.data),
        "marking_complete": marking_complete,
        "staff_absent": 0,  # Would need attendance tracking for staff
        "late_submissions": late_submissions
    }

@router.get("/activity/recent")
async def get_recent_activity(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "principal":
        raise HTTPException(status_code=403, detail="Principal access required")
    
    supabase = get_supabase_client()
    school_id = current_user["school_id"]
    
    # Get recent audit logs
    logs = supabase.table("audit_logs").select("action, entity_type, created_at").eq("school_id", school_id).order("created_at", desc=True).limit(20).execute()
    
    activities = []
    for log in logs.data:
        if "payment" in log["action"].lower() and "large" in log["action"].lower():
            activities.append({"action": log["action"], "time": log["created_at"]})
        elif "report" in log["action"].lower():
            activities.append({"action": log["action"], "time": log["created_at"]})
        elif "discipline" in log["entity_type"].lower():
            activities.append({"action": f"Disciplinary case {log['action']}", "time": log["created_at"]})
    
    return activities[:10]
