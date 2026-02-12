from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
from ..models.teacher import (
    CreateLessonPlanRequest, CreateAssessmentPlanRequest,
    UploadResourceRequest, CopyWeekRequest
)
from ..core.auth import get_current_user, get_user_school_id
from ..db.supabase import get_supabase_client

router = APIRouter(prefix="/teacher/planning", tags=["teacher-planning"])

@router.get("")
async def get_weekly_plan(
    week: str,  # Format: "2024-W01"
    class_id: UUID,
    subject_id: UUID,
    term_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get weekly lesson plan"""
    supabase = get_supabase_client()
    school_id = get_user_school_id(current_user)
    
    # Parse week
    year, week_num = week.split('-W')
    start_date = datetime.strptime(f"{year}-W{week_num}-1", "%Y-W%W-%w").date()
    end_date = start_date + timedelta(days=6)
    
    # Get lesson plans
    lessons = supabase.table("lesson_plans").select("*").eq(
        "teacher_id", current_user["id"]
    ).eq("class_id", str(class_id)).eq("subject_id", str(subject_id)).gte(
        "date", str(start_date)
    ).lte("date", str(end_date)).order("date").execute()
    
    # Get resources
    resources = supabase.table("resources").select("*").eq(
        "uploaded_by", current_user["id"]
    ).eq("class_id", str(class_id)).eq("subject_id", str(subject_id)).execute()
    
    # Get assessment plans
    assessments = supabase.table("assessment_plans").select("*").eq(
        "teacher_id", current_user["id"]
    ).eq("class_id", str(class_id)).eq("subject_id", str(subject_id)).gte(
        "planned_date", str(start_date)
    ).lte("planned_date", str(end_date)).execute()
    
    # Build weekly grid
    weekly_grid = {}
    for i in range(7):
        day = start_date + timedelta(days=i)
        weekly_grid[str(day)] = {
            "date": str(day),
            "lessons": [l for l in lessons.data if l["date"] == str(day)],
            "assessments": [a for a in assessments.data if a.get("planned_date") == str(day)]
        }
    
    return {
        "week": week,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "weekly_grid": weekly_grid,
        "resources": resources.data
    }

@router.post("/lessons")
async def create_lesson_plan(
    request: CreateLessonPlanRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create lesson plan"""
    supabase = get_supabase_client()
    school_id = get_user_school_id(current_user)
    
    lesson = supabase.table("lesson_plans").insert({
        "school_id": school_id,
        "teacher_id": current_user["id"],
        "class_id": str(request.class_id),
        "subject_id": str(request.subject_id),
        "term_id": str(request.term_id) if request.term_id else None,
        "date": str(request.date),
        "time_slot": request.time_slot,
        "topic": request.topic,
        "objectives": request.objectives,
        "activities": request.activities,
        "homework": request.homework,
        "status": "planned",
        "notes": request.notes
    }).execute()
    
    return {"message": "Lesson plan created", "lesson_id": lesson.data[0]["id"]}

@router.patch("/lessons/{lesson_id}")
async def update_lesson_plan(
    lesson_id: UUID,
    request: CreateLessonPlanRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update lesson plan"""
    supabase = get_supabase_client()
    
    result = supabase.table("lesson_plans").update({
        "topic": request.topic,
        "objectives": request.objectives,
        "activities": request.activities,
        "homework": request.homework,
        "notes": request.notes
    }).eq("id", str(lesson_id)).eq("teacher_id", current_user["id"]).execute()
    
    return {"message": "Lesson plan updated"}

@router.patch("/lessons/{lesson_id}/status")
async def mark_lesson_delivered(
    lesson_id: UUID,
    status: str,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Mark lesson as delivered/missed"""
    supabase = get_supabase_client()
    
    result = supabase.table("lesson_plans").update({
        "status": status,
        "notes": notes
    }).eq("id", str(lesson_id)).eq("teacher_id", current_user["id"]).execute()
    
    return {"message": f"Lesson marked as {status}"}

@router.post("/copy-week")
async def copy_previous_week(
    request: CopyWeekRequest,
    current_user: dict = Depends(get_current_user)
):
    """Copy previous week's plans"""
    supabase = get_supabase_client()
    school_id = get_user_school_id(current_user)
    
    # Parse weeks
    from_year, from_week = request.from_week.split('-W')
    to_year, to_week = request.to_week.split('-W')
    
    from_start = datetime.strptime(f"{from_year}-W{from_week}-1", "%Y-W%W-%w").date()
    from_end = from_start + timedelta(days=6)
    
    to_start = datetime.strptime(f"{to_year}-W{to_week}-1", "%Y-W%W-%w").date()
    
    # Get source lessons
    source_lessons = supabase.table("lesson_plans").select("*").eq(
        "teacher_id", current_user["id"]
    ).gte("date", str(from_start)).lte("date", str(from_end)).execute()
    
    # Copy lessons
    new_lessons = []
    for lesson in source_lessons.data:
        # Calculate new date
        days_offset = (datetime.strptime(lesson["date"], "%Y-%m-%d").date() - from_start).days
        new_date = to_start + timedelta(days=days_offset)
        
        new_lesson = {
            "school_id": school_id,
            "teacher_id": current_user["id"],
            "class_id": lesson["class_id"],
            "subject_id": lesson["subject_id"],
            "term_id": lesson["term_id"],
            "date": str(new_date),
            "time_slot": lesson["time_slot"],
            "topic": lesson["topic"],
            "objectives": lesson["objectives"],
            "activities": lesson["activities"] if request.copy_resources else None,
            "homework": lesson["homework"] if request.copy_homework else None,
            "status": "planned"
        }
        new_lessons.append(new_lesson)
    
    if new_lessons:
        supabase.table("lesson_plans").insert(new_lessons).execute()
    
    return {"message": f"Copied {len(new_lessons)} lessons"}

@router.post("/assessments")
async def create_assessment_plan(
    request: CreateAssessmentPlanRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create assessment plan"""
    supabase = get_supabase_client()
    school_id = get_user_school_id(current_user)
    
    assessment = supabase.table("assessment_plans").insert({
        "school_id": school_id,
        "teacher_id": current_user["id"],
        "class_id": str(request.class_id),
        "subject_id": str(request.subject_id),
        "term_id": str(request.term_id) if request.term_id else None,
        "title": request.title,
        "type": request.type,
        "planned_date": str(request.planned_date) if request.planned_date else None,
        "total_marks": request.total_marks,
        "status": "planned",
        "notes": request.notes
    }).execute()
    
    return {"message": "Assessment plan created", "plan_id": assessment.data[0]["id"]}

@router.post("/assessments/{plan_id}/convert")
async def convert_to_assessment(
    plan_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """Convert assessment plan to actual assessment"""
    supabase = get_supabase_client()
    school_id = get_user_school_id(current_user)
    
    # Get plan
    plan = supabase.table("assessment_plans").select("*").eq(
        "id", str(plan_id)
    ).eq("teacher_id", current_user["id"]).single().execute()
    
    if not plan.data:
        raise HTTPException(status_code=404, detail="Assessment plan not found")
    
    # Create actual assessment
    assessment = supabase.table("assessments").insert({
        "school_id": school_id,
        "teacher_id": current_user["id"],
        "class_id": plan.data["class_id"],
        "subject_id": plan.data["subject_id"],
        "term_id": plan.data["term_id"],
        "type": plan.data["type"],
        "title": plan.data["title"],
        "total_marks": plan.data["total_marks"],
        "date_assigned": str(datetime.now().date()),
        "status": "published"
    }).execute()
    
    # Update plan
    supabase.table("assessment_plans").update({
        "status": "converted",
        "linked_assessment_id": assessment.data[0]["id"]
    }).eq("id", str(plan_id)).execute()
    
    # Pre-generate score rows
    students = supabase.table("students").select("id").eq(
        "class_id", plan.data["class_id"]
    ).eq("status", "active").execute()
    
    score_rows = [{
        "assessment_id": assessment.data[0]["id"],
        "student_id": student["id"],
        "score": None
    } for student in students.data]
    
    if score_rows:
        supabase.table("assessment_scores").insert(score_rows).execute()
    
    return {"message": "Assessment created", "assessment_id": assessment.data[0]["id"]}

@router.post("/resources")
async def upload_resource(
    request: UploadResourceRequest,
    current_user: dict = Depends(get_current_user)
):
    """Upload teaching resource"""
    supabase = get_supabase_client()
    school_id = get_user_school_id(current_user)
    
    resource = supabase.table("resources").insert({
        "school_id": school_id,
        "uploaded_by": current_user["id"],
        "class_id": str(request.class_id) if request.class_id else None,
        "subject_id": str(request.subject_id) if request.subject_id else None,
        "title": request.title,
        "type": request.type,
        "url": request.url,
        "tags": request.tags,
        "visibility": request.visibility
    }).execute()
    
    return {"message": "Resource uploaded", "resource_id": resource.data[0]["id"]}

@router.get("/coverage")
async def get_curriculum_coverage(
    class_id: UUID,
    subject_id: UUID,
    term_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get curriculum coverage progress"""
    supabase = get_supabase_client()
    
    # Get curriculum units
    units = supabase.table("curriculum_units").select("*").eq(
        "subject_id", str(subject_id)
    ).order("order_index").execute()
    
    # Get coverage tracking
    coverage = supabase.table("coverage_tracking").select("*").eq(
        "class_id", str(class_id)
    ).execute()
    
    # Build coverage map
    coverage_map = {c["unit_id"]: c for c in coverage.data}
    
    units_with_coverage = []
    for unit in units.data:
        unit_coverage = coverage_map.get(unit["id"], {})
        units_with_coverage.append({
            **unit,
            "planned_date": unit_coverage.get("planned_date"),
            "completed_date": unit_coverage.get("completed_date"),
            "status": unit_coverage.get("status", "pending")
        })
    
    # Calculate coverage %
    total_units = len(units.data)
    completed_units = len([u for u in units_with_coverage if u["status"] == "completed"])
    coverage_percentage = (completed_units / total_units * 100) if total_units > 0 else 0
    
    return {
        "coverage_percentage": round(coverage_percentage, 1),
        "total_units": total_units,
        "completed_units": completed_units,
        "units": units_with_coverage
    }

@router.get("/export")
async def export_weekly_plan(
    week: str,
    class_id: UUID,
    subject_id: UUID,
    format: str = "pdf",
    current_user: dict = Depends(get_current_user)
):
    """Export weekly plan"""
    # Get plan data
    data = await get_weekly_plan(week, class_id, subject_id, None, current_user)
    
    return {"message": "Export functionality - implement with reportlab/docx"}
