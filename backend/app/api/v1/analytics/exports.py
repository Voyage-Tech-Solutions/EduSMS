"""
EduCore Backend - Analytics Exports API
Export data in various formats
"""
import logging
import csv
import io
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from enum import Enum

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


class ExportFormat(str, Enum):
    CSV = "csv"
    JSON = "json"
    EXCEL = "xlsx"


class ExportRequest(BaseModel):
    """Data export request"""
    data_type: str  # students, teachers, grades, attendance, fees, payments
    format: ExportFormat = ExportFormat.CSV
    filters: Optional[dict] = None
    fields: Optional[List[str]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


# ============================================================
# EXPORT ENDPOINTS
# ============================================================

@router.post("/export")
async def export_data(
    request: ExportRequest,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Export data in specified format"""
    school_id = current_user.get("school_id")

    # Get data based on type
    if request.data_type == "students":
        data = await _export_students(school_id, request, supabase)
    elif request.data_type == "teachers":
        data = await _export_teachers(school_id, request, supabase)
    elif request.data_type == "grades":
        data = await _export_grades(school_id, request, supabase)
    elif request.data_type == "attendance":
        data = await _export_attendance(school_id, request, supabase)
    elif request.data_type == "fees":
        data = await _export_fees(school_id, request, supabase)
    elif request.data_type == "payments":
        data = await _export_payments(school_id, request, supabase)
    else:
        raise HTTPException(status_code=400, detail="Invalid data type")

    # Format output
    if request.format == ExportFormat.CSV:
        return _create_csv_response(data, request.data_type)
    elif request.format == ExportFormat.JSON:
        return {
            "data": data,
            "exported_at": datetime.utcnow().isoformat(),
            "total_records": len(data)
        }
    else:
        raise HTTPException(status_code=400, detail="Format not supported")


async def _export_students(school_id, request, supabase):
    """Export student data"""
    result = supabase.table("students").select(
        "student_number, first_name, last_name, date_of_birth, gender, email, phone, address, status, enrollment_date, grades(name), classes(name)"
    ).eq("school_id", school_id).execute()

    students = []
    for s in (result.data or []):
        students.append({
            "Student Number": s.get("student_number"),
            "First Name": s.get("first_name"),
            "Last Name": s.get("last_name"),
            "Date of Birth": s.get("date_of_birth"),
            "Gender": s.get("gender"),
            "Email": s.get("email"),
            "Phone": s.get("phone"),
            "Address": s.get("address"),
            "Status": s.get("status"),
            "Enrollment Date": s.get("enrollment_date"),
            "Grade": s["grades"]["name"] if s.get("grades") else "",
            "Class": s["classes"]["name"] if s.get("classes") else ""
        })

    return students


async def _export_teachers(school_id, request, supabase):
    """Export teacher data"""
    result = supabase.table("teachers").select(
        "employee_id, first_name, last_name, email, phone, position, hire_date, is_active"
    ).eq("school_id", school_id).execute()

    teachers = []
    for t in (result.data or []):
        teachers.append({
            "Employee ID": t.get("employee_id"),
            "First Name": t.get("first_name"),
            "Last Name": t.get("last_name"),
            "Email": t.get("email"),
            "Phone": t.get("phone"),
            "Position": t.get("position"),
            "Hire Date": t.get("hire_date"),
            "Active": "Yes" if t.get("is_active") else "No"
        })

    return teachers


async def _export_grades(school_id, request, supabase):
    """Export grade data"""
    query = supabase.table("grades").select(
        "score, students(student_number, first_name, last_name), subjects(name), terms(name), created_at"
    ).eq("school_id", school_id)

    if request.start_date:
        query = query.gte("created_at", request.start_date.isoformat())
    if request.end_date:
        query = query.lte("created_at", request.end_date.isoformat())

    result = query.execute()

    grades = []
    for g in (result.data or []):
        student = g.get("students", {})
        grades.append({
            "Student Number": student.get("student_number"),
            "Student Name": f"{student.get('first_name', '')} {student.get('last_name', '')}",
            "Subject": g["subjects"]["name"] if g.get("subjects") else "",
            "Term": g["terms"]["name"] if g.get("terms") else "",
            "Score": g.get("score"),
            "Date": g.get("created_at", "")[:10]
        })

    return grades


async def _export_attendance(school_id, request, supabase):
    """Export attendance data"""
    query = supabase.table("attendance").select(
        "date, status, students(student_number, first_name, last_name, classes(name))"
    ).eq("school_id", school_id)

    if request.start_date:
        query = query.gte("date", request.start_date.isoformat())
    if request.end_date:
        query = query.lte("date", request.end_date.isoformat())

    result = query.execute()

    attendance = []
    for a in (result.data or []):
        student = a.get("students", {})
        attendance.append({
            "Date": a.get("date"),
            "Student Number": student.get("student_number"),
            "Student Name": f"{student.get('first_name', '')} {student.get('last_name', '')}",
            "Class": student.get("classes", {}).get("name", ""),
            "Status": a.get("status")
        })

    return attendance


async def _export_fees(school_id, request, supabase):
    """Export fee data"""
    query = supabase.table("fee_records").select(
        "amount, amount_paid, status, due_date, students(student_number, first_name, last_name), fee_types(name)"
    ).eq("school_id", school_id)

    result = query.execute()

    fees = []
    for f in (result.data or []):
        student = f.get("students", {})
        fees.append({
            "Student Number": student.get("student_number"),
            "Student Name": f"{student.get('first_name', '')} {student.get('last_name', '')}",
            "Fee Type": f["fee_types"]["name"] if f.get("fee_types") else "",
            "Amount": f.get("amount"),
            "Amount Paid": f.get("amount_paid"),
            "Balance": f.get("amount", 0) - f.get("amount_paid", 0),
            "Due Date": f.get("due_date"),
            "Status": f.get("status")
        })

    return fees


async def _export_payments(school_id, request, supabase):
    """Export payment data"""
    query = supabase.table("payments").select(
        "amount, payment_method, payment_date, reference_number, students(student_number, first_name, last_name)"
    ).eq("school_id", school_id)

    if request.start_date:
        query = query.gte("payment_date", request.start_date.isoformat())
    if request.end_date:
        query = query.lte("payment_date", request.end_date.isoformat())

    result = query.execute()

    payments = []
    for p in (result.data or []):
        student = p.get("students", {})
        payments.append({
            "Payment Date": p.get("payment_date"),
            "Student Number": student.get("student_number"),
            "Student Name": f"{student.get('first_name', '')} {student.get('last_name', '')}",
            "Amount": p.get("amount"),
            "Payment Method": p.get("payment_method"),
            "Reference Number": p.get("reference_number")
        })

    return payments


def _create_csv_response(data, data_type):
    """Create CSV streaming response"""
    if not data:
        return StreamingResponse(
            iter(["No data to export"]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={data_type}_export.csv"}
        )

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={data_type}_export_{datetime.utcnow().strftime('%Y%m%d')}.csv"
        }
    )


# ============================================================
# BULK EXPORT
# ============================================================

@router.get("/bulk-export")
async def bulk_export(
    format: ExportFormat = ExportFormat.JSON,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Export all school data for backup"""
    school_id = current_user.get("school_id")

    # Verify admin access
    role = current_user.get("role")
    if role not in ["system_admin", "school_admin", "principal"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Collect all data
    export_data = {
        "school_id": school_id,
        "exported_at": datetime.utcnow().isoformat(),
        "tables": {}
    }

    # Students
    students = supabase.table("students").select("*").eq("school_id", school_id).execute()
    export_data["tables"]["students"] = students.data or []

    # Teachers
    teachers = supabase.table("teachers").select("*").eq("school_id", school_id).execute()
    export_data["tables"]["teachers"] = teachers.data or []

    # Classes
    classes = supabase.table("classes").select("*").eq("school_id", school_id).execute()
    export_data["tables"]["classes"] = classes.data or []

    # Grades
    grades = supabase.table("grades").select("*").eq("school_id", school_id).execute()
    export_data["tables"]["grades"] = grades.data or []

    # Attendance
    attendance = supabase.table("attendance").select("*").eq("school_id", school_id).execute()
    export_data["tables"]["attendance"] = attendance.data or []

    # Fee records
    fees = supabase.table("fee_records").select("*").eq("school_id", school_id).execute()
    export_data["tables"]["fee_records"] = fees.data or []

    # Payments
    payments = supabase.table("payments").select("*").eq("school_id", school_id).execute()
    export_data["tables"]["payments"] = payments.data or []

    return export_data


# ============================================================
# EXPORT TEMPLATES
# ============================================================

@router.get("/templates")
async def get_export_templates():
    """Get available export templates"""
    return {
        "templates": [
            {
                "id": "students_full",
                "name": "Full Student Roster",
                "data_type": "students",
                "description": "Complete student information including contact details",
                "fields": ["student_number", "first_name", "last_name", "grade", "class", "email", "phone", "status"]
            },
            {
                "id": "students_basic",
                "name": "Basic Student List",
                "data_type": "students",
                "description": "Simple student list with names and grades",
                "fields": ["student_number", "first_name", "last_name", "grade"]
            },
            {
                "id": "attendance_daily",
                "name": "Daily Attendance Report",
                "data_type": "attendance",
                "description": "Attendance records for a specific date range",
                "fields": ["date", "student_number", "student_name", "status"]
            },
            {
                "id": "grades_term",
                "name": "Term Grades Report",
                "data_type": "grades",
                "description": "All grades for a term",
                "fields": ["student_number", "student_name", "subject", "score"]
            },
            {
                "id": "fees_outstanding",
                "name": "Outstanding Fees Report",
                "data_type": "fees",
                "description": "All unpaid and partially paid fees",
                "fields": ["student_number", "student_name", "fee_type", "amount", "paid", "balance"]
            },
            {
                "id": "payment_history",
                "name": "Payment History",
                "data_type": "payments",
                "description": "All payments received",
                "fields": ["date", "student_name", "amount", "method", "reference"]
            }
        ]
    }


# ============================================================
# EXPORT HISTORY
# ============================================================

@router.get("/history")
async def get_export_history(
    limit: int = Query(default=20, le=100),
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get export history"""
    school_id = current_user.get("school_id")

    result = supabase.table("export_history").select(
        "id, data_type, format, record_count, file_url, created_at, requested_by"
    ).eq("school_id", school_id).order("created_at", desc=True).limit(limit).execute()

    return {"history": result.data or []}


@router.post("/log")
async def log_export(
    data_type: str,
    format: str,
    record_count: int,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Log an export for history tracking"""
    school_id = current_user.get("school_id")
    user_id = current_user.get("id")

    log_data = {
        "school_id": school_id,
        "requested_by": user_id,
        "data_type": data_type,
        "format": format,
        "record_count": record_count
    }

    supabase.table("export_history").insert(log_data).execute()

    return {"success": True}
