"""
EduCore Backend - Progress Reports API
Generate and manage student progress reports
"""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# MODELS
# ============================================================

class SubjectProgress(BaseModel):
    """Progress for a single subject"""
    subject_id: str
    subject_name: str
    current_grade: Optional[float] = None
    letter_grade: Optional[str] = None
    trend: Optional[str] = None  # improving, stable, declining
    strengths: List[str] = []
    areas_to_improve: List[str] = []
    teacher_comments: Optional[str] = None


class ReportCreate(BaseModel):
    """Create a progress report"""
    student_id: UUID
    report_type: str  # interim, quarter, semester, annual, custom
    term_id: Optional[UUID] = None
    report_date: date
    subject_progress: List[SubjectProgress] = []
    attendance_summary: Optional[dict] = None
    behavior_summary: Optional[str] = None
    overall_comments: Optional[str] = None
    recommendations: List[str] = []
    goals_for_next_period: List[str] = []


class ReportUpdate(BaseModel):
    """Update a progress report"""
    subject_progress: Optional[List[SubjectProgress]] = None
    attendance_summary: Optional[dict] = None
    behavior_summary: Optional[str] = None
    overall_comments: Optional[str] = None
    recommendations: Optional[List[str]] = None
    goals_for_next_period: Optional[List[str]] = None
    status: Optional[str] = None  # draft, pending_review, approved, sent


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("")
async def list_reports(
    student_id: Optional[UUID] = None,
    class_id: Optional[UUID] = None,
    report_type: Optional[str] = None,
    term_id: Optional[UUID] = None,
    status: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List progress reports with filters"""
    school_id = current_user.get("school_id")

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    query = supabase.table("progress_reports").select(
        "*, students(first_name, last_name, student_number, class_id, classes(name))"
    ).eq("school_id", school_id)

    if student_id:
        query = query.eq("student_id", str(student_id))
    if report_type:
        query = query.eq("report_type", report_type)
    if term_id:
        query = query.eq("term_id", str(term_id))
    if status:
        query = query.eq("status", status)

    query = query.order("report_date", desc=True).range(offset, offset + limit - 1)

    result = query.execute()

    reports = result.data or []

    # Filter by class if needed
    if class_id:
        reports = [
            r for r in reports
            if r.get("students", {}).get("class_id") == str(class_id)
        ]

    return {
        "reports": reports,
        "total": len(reports),
        "limit": limit,
        "offset": offset
    }


@router.get("/student/{student_id}")
async def get_student_reports(
    student_id: UUID,
    limit: int = Query(default=10, le=50),
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get all progress reports for a specific student"""
    result = supabase.table("progress_reports").select(
        "*"
    ).eq("student_id", str(student_id)).order("report_date", desc=True).limit(limit).execute()

    return {
        "student_id": str(student_id),
        "reports": result.data or []
    }


@router.get("/{report_id}")
async def get_report(
    report_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get a specific progress report with full details"""
    result = supabase.table("progress_reports").select(
        "*, students(first_name, last_name, student_number, date_of_birth, class_id, classes(name))"
    ).eq("id", str(report_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Report not found")

    return result.data


@router.post("")
async def create_report(
    report: ReportCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a new progress report"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    report_data = {
        "school_id": school_id,
        "student_id": str(report.student_id),
        "created_by": user_id,
        "report_type": report.report_type,
        "term_id": str(report.term_id) if report.term_id else None,
        "report_date": report.report_date.isoformat(),
        "subject_progress": [sp.dict() for sp in report.subject_progress],
        "attendance_summary": report.attendance_summary,
        "behavior_summary": report.behavior_summary,
        "overall_comments": report.overall_comments,
        "recommendations": report.recommendations,
        "goals_for_next_period": report.goals_for_next_period,
        "status": "draft"
    }

    result = supabase.table("progress_reports").insert(report_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create report")

    return result.data[0]


@router.post("/generate/{student_id}")
async def generate_report(
    student_id: UUID,
    report_type: str,
    term_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Auto-generate a progress report based on student data"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    # Get student info
    student = supabase.table("students").select(
        "id, first_name, last_name, class_id"
    ).eq("id", str(student_id)).single().execute()

    if not student.data:
        raise HTTPException(status_code=404, detail="Student not found")

    # Get grades from gradebook
    grades_result = supabase.table("gradebook_entries").select(
        "subject_id, score, total_points, subjects(name)"
    ).eq("student_id", str(student_id)).execute()

    # Calculate subject averages
    subject_grades = {}
    for entry in (grades_result.data or []):
        subject_id = entry.get("subject_id")
        if subject_id not in subject_grades:
            subject_grades[subject_id] = {
                "name": entry.get("subjects", {}).get("name", "Unknown"),
                "scores": [],
                "totals": []
            }
        if entry.get("score") is not None and entry.get("total_points"):
            subject_grades[subject_id]["scores"].append(entry["score"])
            subject_grades[subject_id]["totals"].append(entry["total_points"])

    # Build subject progress
    subject_progress = []
    for subject_id, data in subject_grades.items():
        if data["totals"]:
            avg = sum(data["scores"]) / sum(data["totals"]) * 100
            letter = _get_letter_grade(avg)

            subject_progress.append({
                "subject_id": subject_id,
                "subject_name": data["name"],
                "current_grade": round(avg, 1),
                "letter_grade": letter,
                "trend": "stable",
                "strengths": [],
                "areas_to_improve": [],
                "teacher_comments": None
            })

    # Get attendance summary
    attendance_result = supabase.table("attendance").select(
        "status"
    ).eq("student_id", str(student_id)).execute()

    attendance_data = attendance_result.data or []
    attendance_summary = {
        "total_days": len(attendance_data),
        "present": len([a for a in attendance_data if a.get("status") == "present"]),
        "absent": len([a for a in attendance_data if a.get("status") == "absent"]),
        "late": len([a for a in attendance_data if a.get("status") == "late"]),
        "excused": len([a for a in attendance_data if a.get("status") == "excused"])
    }

    # Create report
    report_data = {
        "school_id": school_id,
        "student_id": str(student_id),
        "created_by": user_id,
        "report_type": report_type,
        "term_id": str(term_id) if term_id else None,
        "report_date": date.today().isoformat(),
        "subject_progress": subject_progress,
        "attendance_summary": attendance_summary,
        "behavior_summary": None,
        "overall_comments": None,
        "recommendations": [],
        "goals_for_next_period": [],
        "status": "draft"
    }

    result = supabase.table("progress_reports").insert(report_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to generate report")

    return result.data[0]


@router.put("/{report_id}")
async def update_report(
    report_id: UUID,
    update: ReportUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update a progress report"""
    existing = supabase.table("progress_reports").select("id, status").eq(
        "id", str(report_id)
    ).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Report not found")

    if existing.data.get("status") == "sent":
        raise HTTPException(status_code=400, detail="Cannot edit a sent report")

    update_data = {}
    if update.subject_progress is not None:
        update_data["subject_progress"] = [sp.dict() for sp in update.subject_progress]
    if update.attendance_summary is not None:
        update_data["attendance_summary"] = update.attendance_summary
    if update.behavior_summary is not None:
        update_data["behavior_summary"] = update.behavior_summary
    if update.overall_comments is not None:
        update_data["overall_comments"] = update.overall_comments
    if update.recommendations is not None:
        update_data["recommendations"] = update.recommendations
    if update.goals_for_next_period is not None:
        update_data["goals_for_next_period"] = update.goals_for_next_period
    if update.status is not None:
        update_data["status"] = update.status

    result = supabase.table("progress_reports").update(update_data).eq(
        "id", str(report_id)
    ).execute()

    return result.data[0] if result.data else None


@router.post("/{report_id}/approve")
async def approve_report(
    report_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Approve a progress report"""
    user_id = current_user["id"]

    existing = supabase.table("progress_reports").select("id, status").eq(
        "id", str(report_id)
    ).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Report not found")

    if existing.data.get("status") not in ["draft", "pending_review"]:
        raise HTTPException(status_code=400, detail="Report cannot be approved in current status")

    supabase.table("progress_reports").update({
        "status": "approved",
        "approved_by": user_id,
        "approved_at": datetime.utcnow().isoformat()
    }).eq("id", str(report_id)).execute()

    return {"success": True, "status": "approved"}


@router.post("/{report_id}/send")
async def send_report(
    report_id: UUID,
    notify_parent: bool = True,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Send a progress report to parents"""
    existing = supabase.table("progress_reports").select(
        "id, status, student_id"
    ).eq("id", str(report_id)).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Report not found")

    if existing.data.get("status") != "approved":
        raise HTTPException(status_code=400, detail="Report must be approved before sending")

    # Update status
    supabase.table("progress_reports").update({
        "status": "sent",
        "sent_at": datetime.utcnow().isoformat()
    }).eq("id", str(report_id)).execute()

    # TODO: Send notification to parent (email/push)
    if notify_parent:
        # This would integrate with notification system
        pass

    return {"success": True, "status": "sent"}


@router.delete("/{report_id}")
async def delete_report(
    report_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a progress report (only draft reports)"""
    existing = supabase.table("progress_reports").select("id, status").eq(
        "id", str(report_id)
    ).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Report not found")

    if existing.data.get("status") != "draft":
        raise HTTPException(status_code=400, detail="Only draft reports can be deleted")

    supabase.table("progress_reports").delete().eq("id", str(report_id)).execute()

    return {"success": True}


@router.post("/bulk-generate")
async def bulk_generate_reports(
    class_id: UUID,
    report_type: str,
    term_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Generate progress reports for all students in a class"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    # Get all students in class
    students = supabase.table("students").select("id").eq(
        "class_id", str(class_id)
    ).execute()

    if not students.data:
        raise HTTPException(status_code=404, detail="No students found in class")

    generated_count = 0
    failed_count = 0

    for student in students.data:
        try:
            # Generate report for each student
            await generate_report(
                UUID(student["id"]),
                report_type,
                term_id,
                current_user,
                supabase
            )
            generated_count += 1
        except Exception as e:
            logger.error(f"Failed to generate report for student {student['id']}: {e}")
            failed_count += 1

    return {
        "success": True,
        "generated": generated_count,
        "failed": failed_count,
        "total_students": len(students.data)
    }


@router.get("/{report_id}/print")
async def get_printable_report(
    report_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get report in a format suitable for printing"""
    report = await get_report(report_id, current_user, supabase)

    student = report.get("students", {})

    printable = {
        "school_name": "",  # Would get from school settings
        "report_date": report.get("report_date"),
        "report_type": report.get("report_type"),
        "student_name": f"{student.get('first_name', '')} {student.get('last_name', '')}",
        "student_number": student.get("student_number"),
        "class_name": student.get("classes", {}).get("name", ""),
        "subjects": report.get("subject_progress", []),
        "attendance": report.get("attendance_summary"),
        "behavior": report.get("behavior_summary"),
        "overall_comments": report.get("overall_comments"),
        "recommendations": report.get("recommendations", []),
        "goals": report.get("goals_for_next_period", [])
    }

    return printable


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _get_letter_grade(percentage: float) -> str:
    """Convert percentage to letter grade"""
    if percentage >= 93:
        return "A"
    elif percentage >= 90:
        return "A-"
    elif percentage >= 87:
        return "B+"
    elif percentage >= 83:
        return "B"
    elif percentage >= 80:
        return "B-"
    elif percentage >= 77:
        return "C+"
    elif percentage >= 73:
        return "C"
    elif percentage >= 70:
        return "C-"
    elif percentage >= 67:
        return "D+"
    elif percentage >= 63:
        return "D"
    elif percentage >= 60:
        return "D-"
    else:
        return "F"
