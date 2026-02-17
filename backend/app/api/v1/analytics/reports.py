"""
EduCore Backend - Analytics Reports API
Generate and manage analytical reports
"""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime, timedelta
from enum import Enum

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


class ReportType(str, Enum):
    ACADEMIC_SUMMARY = "academic_summary"
    ATTENDANCE_REPORT = "attendance_report"
    FINANCIAL_REPORT = "financial_report"
    ENROLLMENT_REPORT = "enrollment_report"
    TEACHER_PERFORMANCE = "teacher_performance"
    STUDENT_PROGRESS = "student_progress"
    CUSTOM = "custom"


class ReportFormat(str, Enum):
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"


class ReportRequest(BaseModel):
    """Request to generate a report"""
    report_type: ReportType
    title: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    term_id: Optional[UUID] = None
    academic_year_id: Optional[UUID] = None
    grade_ids: Optional[List[UUID]] = None
    class_ids: Optional[List[UUID]] = None
    subject_ids: Optional[List[UUID]] = None
    format: ReportFormat = ReportFormat.PDF
    include_charts: bool = True
    include_details: bool = True


class ScheduledReportCreate(BaseModel):
    """Create a scheduled report"""
    report_type: ReportType
    title: str
    schedule: str  # daily, weekly, monthly
    day_of_week: Optional[int] = None  # 0-6 for weekly
    day_of_month: Optional[int] = None  # 1-31 for monthly
    time: str = "08:00"
    format: ReportFormat = ReportFormat.PDF
    recipients: List[str] = []  # email addresses
    filters: Optional[dict] = None


# ============================================================
# REPORT GENERATION
# ============================================================

@router.post("/generate")
async def generate_report(
    request: ReportRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Generate a new report"""
    school_id = current_user.get("school_id")
    user_id = current_user.get("id")

    # Create report record
    report_data = {
        "school_id": school_id,
        "requested_by": user_id,
        "report_type": request.report_type.value,
        "title": request.title or f"{request.report_type.value.replace('_', ' ').title()} Report",
        "parameters": {
            "start_date": request.start_date.isoformat() if request.start_date else None,
            "end_date": request.end_date.isoformat() if request.end_date else None,
            "term_id": str(request.term_id) if request.term_id else None,
            "academic_year_id": str(request.academic_year_id) if request.academic_year_id else None,
            "grade_ids": [str(g) for g in request.grade_ids] if request.grade_ids else None,
            "include_charts": request.include_charts,
            "include_details": request.include_details
        },
        "format": request.format.value,
        "status": "pending"
    }

    result = supabase.table("generated_reports").insert(report_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create report")

    report_id = result.data[0]["id"]

    # Queue background generation (in production, this would be a Celery task)
    background_tasks.add_task(
        _generate_report_async,
        report_id,
        request,
        school_id,
        supabase
    )

    return {
        "report_id": report_id,
        "status": "pending",
        "message": "Report generation started"
    }


async def _generate_report_async(report_id, request, school_id, supabase):
    """Background task to generate report"""
    try:
        # Update status to processing
        supabase.table("generated_reports").update({
            "status": "processing",
            "started_at": datetime.utcnow().isoformat()
        }).eq("id", report_id).execute()

        # Generate report data based on type
        report_data = {}

        if request.report_type == ReportType.ACADEMIC_SUMMARY:
            report_data = await _generate_academic_report(school_id, request, supabase)
        elif request.report_type == ReportType.ATTENDANCE_REPORT:
            report_data = await _generate_attendance_report(school_id, request, supabase)
        elif request.report_type == ReportType.FINANCIAL_REPORT:
            report_data = await _generate_financial_report(school_id, request, supabase)
        elif request.report_type == ReportType.ENROLLMENT_REPORT:
            report_data = await _generate_enrollment_report(school_id, request, supabase)

        # In production, convert to PDF/Excel here
        # For now, store as JSON
        supabase.table("generated_reports").update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "data": report_data,
            "file_url": f"/api/v1/analytics/reports/{report_id}/download"
        }).eq("id", report_id).execute()

    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        supabase.table("generated_reports").update({
            "status": "failed",
            "error": str(e)
        }).eq("id", report_id).execute()


async def _generate_academic_report(school_id, request, supabase):
    """Generate academic summary report"""
    query = supabase.table("grades").select(
        "score, student_id, subject_id, class_id, students(first_name, last_name), subjects(name), classes(name)"
    ).eq("school_id", school_id)

    if request.term_id:
        query = query.eq("term_id", str(request.term_id))

    result = query.execute()
    grades = result.data or []

    scores = [g["score"] for g in grades if g.get("score")]

    return {
        "summary": {
            "total_grades": len(grades),
            "average_score": round(sum(scores) / len(scores), 2) if scores else 0,
            "pass_rate": round(sum(1 for s in scores if s >= 60) / len(scores) * 100, 2) if scores else 0,
            "highest_score": max(scores) if scores else 0,
            "lowest_score": min(scores) if scores else 0
        },
        "distribution": {
            "A (90-100)": sum(1 for s in scores if s >= 90),
            "B (80-89)": sum(1 for s in scores if 80 <= s < 90),
            "C (70-79)": sum(1 for s in scores if 70 <= s < 80),
            "D (60-69)": sum(1 for s in scores if 60 <= s < 70),
            "F (0-59)": sum(1 for s in scores if s < 60)
        },
        "generated_at": datetime.utcnow().isoformat()
    }


async def _generate_attendance_report(school_id, request, supabase):
    """Generate attendance report"""
    query = supabase.table("attendance").select(
        "date, status, student_id, students(first_name, last_name, class_id)"
    ).eq("school_id", school_id)

    if request.start_date:
        query = query.gte("date", request.start_date.isoformat())
    if request.end_date:
        query = query.lte("date", request.end_date.isoformat())

    result = query.execute()
    records = result.data or []

    total = len(records)
    present = sum(1 for r in records if r.get("status") == "present")

    return {
        "summary": {
            "total_records": total,
            "attendance_rate": round(present / total * 100, 2) if total > 0 else 0,
            "present": present,
            "absent": sum(1 for r in records if r.get("status") == "absent"),
            "late": sum(1 for r in records if r.get("status") == "late"),
            "excused": sum(1 for r in records if r.get("status") == "excused")
        },
        "generated_at": datetime.utcnow().isoformat()
    }


async def _generate_financial_report(school_id, request, supabase):
    """Generate financial report"""
    fees = supabase.table("fee_records").select(
        "amount, amount_paid, status, fee_types(name)"
    ).eq("school_id", school_id).execute()

    fee_data = fees.data or []
    total = sum(f.get("amount", 0) for f in fee_data)
    collected = sum(f.get("amount_paid", 0) for f in fee_data)

    return {
        "summary": {
            "total_billed": total,
            "total_collected": collected,
            "outstanding": total - collected,
            "collection_rate": round(collected / total * 100, 2) if total > 0 else 0
        },
        "by_status": {
            "paid": sum(1 for f in fee_data if f.get("status") == "paid"),
            "partial": sum(1 for f in fee_data if f.get("status") == "partial"),
            "pending": sum(1 for f in fee_data if f.get("status") == "pending"),
            "overdue": sum(1 for f in fee_data if f.get("status") == "overdue")
        },
        "generated_at": datetime.utcnow().isoformat()
    }


async def _generate_enrollment_report(school_id, request, supabase):
    """Generate enrollment report"""
    students = supabase.table("students").select(
        "id, status, gender, grade_id, enrollment_date, grades(name)"
    ).eq("school_id", school_id).execute()

    all_students = students.data or []
    active = [s for s in all_students if s.get("status") == "active"]

    return {
        "summary": {
            "total_active": len(active),
            "total_all": len(all_students),
            "by_gender": {
                "male": sum(1 for s in active if s.get("gender") == "male"),
                "female": sum(1 for s in active if s.get("gender") == "female")
            }
        },
        "generated_at": datetime.utcnow().isoformat()
    }


# ============================================================
# REPORT MANAGEMENT
# ============================================================

@router.get("")
async def list_reports(
    report_type: Optional[ReportType] = None,
    status: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List generated reports"""
    school_id = current_user.get("school_id")

    query = supabase.table("generated_reports").select(
        "id, report_type, title, status, format, created_at, completed_at, file_url"
    ).eq("school_id", school_id)

    if report_type:
        query = query.eq("report_type", report_type.value)
    if status:
        query = query.eq("status", status)

    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

    result = query.execute()

    return {
        "reports": result.data or [],
        "limit": limit,
        "offset": offset
    }


@router.get("/{report_id}")
async def get_report(
    report_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get report details"""
    result = supabase.table("generated_reports").select("*").eq(
        "id", str(report_id)
    ).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Report not found")

    return result.data


@router.get("/{report_id}/download")
async def download_report(
    report_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Download report file"""
    result = supabase.table("generated_reports").select(
        "data, format, title, status"
    ).eq("id", str(report_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Report not found")

    if result.data["status"] != "completed":
        raise HTTPException(status_code=400, detail="Report not ready for download")

    # In production, return actual file
    # For now, return JSON data
    from fastapi.responses import JSONResponse
    return JSONResponse(
        content=result.data["data"],
        headers={
            "Content-Disposition": f"attachment; filename={result.data['title']}.json"
        }
    )


@router.delete("/{report_id}")
async def delete_report(
    report_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a report"""
    supabase.table("generated_reports").delete().eq("id", str(report_id)).execute()
    return {"success": True}


# ============================================================
# SCHEDULED REPORTS
# ============================================================

@router.get("/scheduled")
async def list_scheduled_reports(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List scheduled reports"""
    school_id = current_user.get("school_id")

    result = supabase.table("scheduled_reports").select("*").eq(
        "school_id", school_id
    ).eq("is_active", True).execute()

    return {"scheduled_reports": result.data or []}


@router.post("/scheduled")
async def create_scheduled_report(
    report: ScheduledReportCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a scheduled report"""
    school_id = current_user.get("school_id")
    user_id = current_user.get("id")

    report_data = {
        "school_id": school_id,
        "created_by": user_id,
        "report_type": report.report_type.value,
        "title": report.title,
        "schedule": report.schedule,
        "day_of_week": report.day_of_week,
        "day_of_month": report.day_of_month,
        "time": report.time,
        "format": report.format.value,
        "recipients": report.recipients,
        "filters": report.filters,
        "is_active": True
    }

    result = supabase.table("scheduled_reports").insert(report_data).execute()

    return result.data[0] if result.data else None


@router.delete("/scheduled/{schedule_id}")
async def delete_scheduled_report(
    schedule_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a scheduled report"""
    supabase.table("scheduled_reports").update({
        "is_active": False
    }).eq("id", str(schedule_id)).execute()

    return {"success": True}


# ============================================================
# REPORT TEMPLATES
# ============================================================

@router.get("/templates")
async def get_report_templates():
    """Get available report templates"""
    return {
        "templates": [
            {
                "type": "academic_summary",
                "name": "Academic Summary Report",
                "description": "Overview of academic performance including grades, pass rates, and distributions",
                "parameters": ["term_id", "academic_year_id", "grade_ids", "subject_ids"]
            },
            {
                "type": "attendance_report",
                "name": "Attendance Report",
                "description": "Detailed attendance analysis with trends and chronic absenteeism",
                "parameters": ["start_date", "end_date", "grade_ids", "class_ids"]
            },
            {
                "type": "financial_report",
                "name": "Financial Report",
                "description": "Fee collection, outstanding balances, and payment trends",
                "parameters": ["academic_year_id", "start_date", "end_date"]
            },
            {
                "type": "enrollment_report",
                "name": "Enrollment Report",
                "description": "Student enrollment statistics and demographics",
                "parameters": ["academic_year_id"]
            },
            {
                "type": "teacher_performance",
                "name": "Teacher Performance Report",
                "description": "Teacher effectiveness metrics and class performance",
                "parameters": ["term_id", "teacher_ids"]
            },
            {
                "type": "student_progress",
                "name": "Student Progress Report",
                "description": "Individual student academic progress over time",
                "parameters": ["student_id", "academic_year_id"]
            }
        ]
    }
