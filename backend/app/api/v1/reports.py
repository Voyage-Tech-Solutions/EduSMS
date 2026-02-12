"""
EduCore Backend - Reports & Analytics API
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional, Dict, Any
from datetime import datetime, date, timedelta
from app.core.security import require_office_admin, require_teacher
from app.db.supabase import supabase_admin

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/summary")
async def get_summary_metrics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(require_teacher),
):
    """Get summary metrics for dashboard"""
    school_id = current_user.get("school_id")
    
    if not start_date:
        start_date = (date.today().replace(day=1)).isoformat()
    if not end_date:
        end_date = date.today().isoformat()
    
    if not supabase_admin:
        return {"total_enrollment": 0, "avg_attendance": 0, "fee_collection": 0, "collection_rate": 0, "academic_avg": 0}
    
    # Total enrollment
    students = supabase_admin.table("students").select("id", count="exact").eq("school_id", school_id).eq("status", "active").execute()
    total_enrollment = students.count or 0
    
    # Attendance
    attendance = supabase_admin.table("attendance_records").select("status").eq("school_id", school_id).gte("date", start_date).lte("date", end_date).execute()
    total_records = len(attendance.data)
    present = sum(1 for r in attendance.data if r["status"] in ["present", "late"])
    avg_attendance = round((present / total_records * 100), 2) if total_records > 0 else 0
    
    # Fees
    invoices = supabase_admin.table("invoices").select("amount, amount_paid").eq("school_id", school_id).execute()
    total_billed = sum(float(i["amount"]) for i in invoices.data)
    total_collected = sum(float(i["amount_paid"]) for i in invoices.data)
    collection_rate = round((total_collected / total_billed * 100), 2) if total_billed > 0 else 0
    
    # Academic (placeholder)
    academic_avg = 0
    
    return {
        "total_enrollment": total_enrollment,
        "avg_attendance": avg_attendance,
        "fee_collection": total_collected,
        "collection_rate": collection_rate,
        "academic_avg": academic_avg
    }


@router.post("/student-directory")
async def generate_student_directory(
    report_data: Dict[str, Any],
    current_user: dict = Depends(require_office_admin),
):
    """Generate student directory report"""
    school_id = current_user.get("school_id")
    grade_id = report_data.get("grade_id")
    class_id = report_data.get("class_id")
    status_filter = report_data.get("status", "active")
    include_contact = report_data.get("include_contact", False)
    
    if not supabase_admin:
        return {"data": [], "total": 0}
    
    query = supabase_admin.table("students").select("*").eq("school_id", school_id).eq("status", status_filter)
    if grade_id:
        query = query.eq("grade_id", grade_id)
    if class_id:
        query = query.eq("class_id", class_id)
    
    result = query.execute()
    
    if include_contact:
        for student in result.data:
            guardians = supabase_admin.table("guardians").select("*").eq("student_id", student["id"]).execute()
            student["guardians"] = guardians.data
    
    return {"data": result.data, "total": len(result.data)}


@router.post("/fee-statement")
async def generate_fee_statement(
    report_data: Dict[str, Any],
    current_user: dict = Depends(require_office_admin),
):
    """Generate fee statement report"""
    school_id = current_user.get("school_id")
    student_id = report_data.get("student_id")
    grade_id = report_data.get("grade_id")
    overdue_only = report_data.get("overdue_only", False)
    
    if not supabase_admin:
        return {"data": [], "total": 0}
    
    query = supabase_admin.table("invoices").select("*, students!inner(first_name, last_name, admission_number)").eq("school_id", school_id)
    
    if student_id:
        query = query.eq("student_id", student_id)
    if grade_id:
        query = query.eq("students.grade_id", grade_id)
    if overdue_only:
        query = query.eq("status", "overdue")
    
    result = query.execute()
    
    # Add payment history
    for invoice in result.data:
        payments = supabase_admin.table("payments").select("*").eq("invoice_id", invoice["id"]).execute()
        invoice["payments"] = payments.data
    
    return {"data": result.data, "total": len(result.data)}


@router.post("/attendance-summary")
async def generate_attendance_summary(
    report_data: Dict[str, Any],
    current_user: dict = Depends(require_teacher),
):
    """Generate attendance summary report"""
    school_id = current_user.get("school_id")
    grade_id = report_data.get("grade_id")
    class_id = report_data.get("class_id")
    start_date = report_data.get("start_date")
    end_date = report_data.get("end_date")
    
    if not supabase_admin:
        return {"data": [], "summary": {}}
    
    query = supabase_admin.table("attendance_records").select("*, students!inner(first_name, last_name, admission_number, grade_id, class_id)").eq("school_id", school_id)
    
    if start_date:
        query = query.gte("date", start_date)
    if end_date:
        query = query.lte("date", end_date)
    if grade_id:
        query = query.eq("students.grade_id", grade_id)
    if class_id:
        query = query.eq("students.class_id", class_id)
    
    result = query.execute()
    
    # Calculate summary
    total = len(result.data)
    present = sum(1 for r in result.data if r["status"] == "present")
    absent = sum(1 for r in result.data if r["status"] == "absent")
    late = sum(1 for r in result.data if r["status"] == "late")
    excused = sum(1 for r in result.data if r["status"] == "excused")
    
    summary = {
        "total_records": total,
        "present": present,
        "absent": absent,
        "late": late,
        "excused": excused,
        "attendance_rate": round((present + late) / total * 100, 2) if total > 0 else 0
    }
    
    return {"data": result.data, "summary": summary}


@router.post("/academic-summary")
async def generate_academic_summary(
    report_data: Dict[str, Any],
    current_user: dict = Depends(require_teacher),
):
    """Generate academic performance report"""
    school_id = current_user.get("school_id")
    term_id = report_data.get("term_id")
    grade_id = report_data.get("grade_id")
    class_id = report_data.get("class_id")
    
    if not supabase_admin:
        return {"data": [], "summary": {}}
    
    query = supabase_admin.table("grade_entries").select("*, students!inner(first_name, last_name, admission_number, grade_id, class_id)").eq("school_id", school_id)
    
    if term_id:
        query = query.eq("term", term_id)
    if grade_id:
        query = query.eq("students.grade_id", grade_id)
    if class_id:
        query = query.eq("students.class_id", class_id)
    
    result = query.execute()
    
    # Calculate averages
    if result.data:
        avg_score = sum(float(r["score"]) for r in result.data) / len(result.data)
    else:
        avg_score = 0
    
    summary = {
        "total_entries": len(result.data),
        "average_score": round(avg_score, 2)
    }
    
    return {"data": result.data, "summary": summary}


@router.get("/export-all")
async def export_all_reports(
    format: str = Query("csv"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(require_office_admin),
):
    """Export all reports"""
    return {"message": "Export all reports functionality", "format": format}


@router.get("/charts/attendance-trend")
async def get_attendance_trend(
    days: int = Query(30, ge=7, le=90),
    current_user: dict = Depends(require_teacher),
):
    """Get attendance trend data for charts"""
    school_id = current_user.get("school_id")
    start_date = (date.today() - timedelta(days=days)).isoformat()
    
    if not supabase_admin:
        return []
    
    result = supabase_admin.table("attendance_records").select("date, status").eq("school_id", school_id).gte("date", start_date).execute()
    
    # Group by date
    trend = {}
    for record in result.data:
        d = record["date"]
        if d not in trend:
            trend[d] = {"date": d, "present": 0, "absent": 0, "total": 0}
        trend[d]["total"] += 1
        if record["status"] in ["present", "late"]:
            trend[d]["present"] += 1
        else:
            trend[d]["absent"] += 1
    
    # Calculate rates
    for d in trend.values():
        d["rate"] = round((d["present"] / d["total"] * 100), 2) if d["total"] > 0 else 0
    
    return list(trend.values())


@router.get("/charts/fee-collection")
async def get_fee_collection_by_grade(current_user: dict = Depends(require_office_admin)):
    """Get fee collection by grade for charts"""
    school_id = current_user.get("school_id")
    
    if not supabase_admin:
        return []
    
    result = supabase_admin.table("invoices").select("amount, amount_paid, students!inner(grade_id, grades!inner(name))").eq("school_id", school_id).execute()
    
    # Group by grade
    by_grade = {}
    for invoice in result.data:
        grade_name = invoice["students"]["grades"]["name"]
        if grade_name not in by_grade:
            by_grade[grade_name] = {"grade": grade_name, "billed": 0, "collected": 0}
        by_grade[grade_name]["billed"] += float(invoice["amount"])
        by_grade[grade_name]["collected"] += float(invoice["amount_paid"])
    
    return list(by_grade.values())
