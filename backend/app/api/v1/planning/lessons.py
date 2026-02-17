"""
EduCore Backend - Lesson Plans API
Create and manage lesson plans
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

class LessonSection(BaseModel):
    """A section within a lesson plan"""
    id: str
    name: str
    duration_minutes: int = 10
    content: str = ""
    notes: Optional[str] = None
    resources: List[str] = []  # Resource IDs
    order_index: int = 0


class LessonPlanCreate(BaseModel):
    """Create a lesson plan"""
    title: str
    class_id: UUID
    subject_id: UUID
    lesson_date: date
    period: Optional[int] = None
    template_id: Optional[UUID] = None
    curriculum_unit_id: Optional[str] = None

    # Learning objectives
    objectives: List[str] = []
    standard_ids: Optional[List[UUID]] = None
    essential_questions: List[str] = []

    # Content
    sections: List[LessonSection] = []
    materials_needed: List[str] = []
    vocabulary: List[str] = []

    # Differentiation
    differentiation_notes: Optional[str] = None
    accommodations: Optional[str] = None
    extensions: Optional[str] = None

    # Assessment
    assessment_strategy: Optional[str] = None
    homework: Optional[str] = None

    # Reflection (filled after lesson)
    reflection: Optional[str] = None


class LessonPlanUpdate(BaseModel):
    """Update a lesson plan"""
    title: Optional[str] = None
    lesson_date: Optional[date] = None
    period: Optional[int] = None
    objectives: Optional[List[str]] = None
    standard_ids: Optional[List[UUID]] = None
    essential_questions: Optional[List[str]] = None
    sections: Optional[List[LessonSection]] = None
    materials_needed: Optional[List[str]] = None
    vocabulary: Optional[List[str]] = None
    differentiation_notes: Optional[str] = None
    accommodations: Optional[str] = None
    extensions: Optional[str] = None
    assessment_strategy: Optional[str] = None
    homework: Optional[str] = None
    reflection: Optional[str] = None
    status: Optional[str] = None  # draft, ready, taught, reflected


class LessonPlanCopy(BaseModel):
    """Copy lesson plan to new dates"""
    target_dates: List[date]
    target_class_id: Optional[UUID] = None


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("")
async def list_lesson_plans(
    class_id: Optional[UUID] = None,
    subject_id: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List lesson plans with filters"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    query = supabase.table("lesson_plans").select(
        "*, classes(name), subjects(name)"
    ).eq("school_id", school_id).eq("teacher_id", user_id).eq("is_active", True)

    if class_id:
        query = query.eq("class_id", str(class_id))
    if subject_id:
        query = query.eq("subject_id", str(subject_id))
    if date_from:
        query = query.gte("lesson_date", date_from.isoformat())
    if date_to:
        query = query.lte("lesson_date", date_to.isoformat())
    if status:
        query = query.eq("status", status)
    if search:
        query = query.ilike("title", f"%{search}%")

    query = query.order("lesson_date", desc=True).range(offset, offset + limit - 1)

    result = query.execute()

    return {
        "lesson_plans": result.data or [],
        "total": len(result.data) if result.data else 0,
        "limit": limit,
        "offset": offset
    }


@router.get("/calendar")
async def get_lesson_calendar(
    year: int,
    month: int,
    class_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get lesson plans for a calendar month view"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    # Calculate date range
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    query = supabase.table("lesson_plans").select(
        "id, title, lesson_date, period, status, class_id, subject_id, classes(name), subjects(name)"
    ).eq("school_id", school_id).eq("teacher_id", user_id).eq("is_active", True)

    query = query.gte("lesson_date", start_date.isoformat())
    query = query.lt("lesson_date", end_date.isoformat())

    if class_id:
        query = query.eq("class_id", str(class_id))

    query = query.order("lesson_date").order("period")

    result = query.execute()

    # Group by date
    calendar = {}
    for plan in (result.data or []):
        date_key = plan["lesson_date"]
        if date_key not in calendar:
            calendar[date_key] = []
        calendar[date_key].append(plan)

    return {
        "year": year,
        "month": month,
        "lessons_by_date": calendar,
        "total_lessons": len(result.data) if result.data else 0
    }


@router.get("/week")
async def get_week_plans(
    week_start: date,
    class_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get lesson plans for a week view"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    from datetime import timedelta
    week_end = week_start + timedelta(days=6)

    query = supabase.table("lesson_plans").select(
        "*, classes(name), subjects(name)"
    ).eq("school_id", school_id).eq("teacher_id", user_id).eq("is_active", True)

    query = query.gte("lesson_date", week_start.isoformat())
    query = query.lte("lesson_date", week_end.isoformat())

    if class_id:
        query = query.eq("class_id", str(class_id))

    query = query.order("lesson_date").order("period")

    result = query.execute()

    # Group by day of week
    days = {}
    for i in range(7):
        day = week_start + timedelta(days=i)
        days[day.isoformat()] = []

    for plan in (result.data or []):
        date_key = plan["lesson_date"]
        if date_key in days:
            days[date_key].append(plan)

    return {
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "days": days
    }


@router.get("/{lesson_id}")
async def get_lesson_plan(
    lesson_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get a lesson plan with full details"""
    result = supabase.table("lesson_plans").select(
        "*, classes(name), subjects(name), lesson_templates(name)"
    ).eq("id", str(lesson_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Lesson plan not found")

    lesson = result.data

    # Get standards details
    if lesson.get("standard_ids"):
        standards = supabase.table("learning_standards").select(
            "id, code, description"
        ).in_("id", lesson["standard_ids"]).execute()
        lesson["standards"] = standards.data or []

    # Get resource details for sections
    all_resource_ids = []
    for section in (lesson.get("sections") or []):
        all_resource_ids.extend(section.get("resources") or [])

    if all_resource_ids:
        resources = supabase.table("teaching_resources").select(
            "id, title, resource_type, thumbnail_url"
        ).in_("id", all_resource_ids).execute()
        lesson["resource_details"] = {r["id"]: r for r in (resources.data or [])}

    return lesson


@router.post("")
async def create_lesson_plan(
    lesson: LessonPlanCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a new lesson plan"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    # If template provided, get template structure
    sections = [s.dict() for s in lesson.sections]
    if lesson.template_id and not sections:
        template = supabase.table("lesson_templates").select(
            "structure"
        ).eq("id", str(lesson.template_id)).single().execute()

        if template.data:
            # Convert template sections to lesson sections
            sections = []
            for ts in (template.data.get("structure") or []):
                sections.append({
                    "id": ts.get("id"),
                    "name": ts.get("name"),
                    "duration_minutes": ts.get("duration_minutes", 10),
                    "content": "",
                    "notes": ts.get("description"),
                    "resources": [],
                    "order_index": ts.get("order_index", 0)
                })

    lesson_data = {
        "school_id": school_id,
        "teacher_id": user_id,
        "class_id": str(lesson.class_id),
        "subject_id": str(lesson.subject_id),
        "title": lesson.title,
        "lesson_date": lesson.lesson_date.isoformat(),
        "period": lesson.period,
        "template_id": str(lesson.template_id) if lesson.template_id else None,
        "curriculum_unit_id": lesson.curriculum_unit_id,
        "objectives": lesson.objectives,
        "standard_ids": [str(s) for s in lesson.standard_ids] if lesson.standard_ids else None,
        "essential_questions": lesson.essential_questions,
        "sections": sections,
        "materials_needed": lesson.materials_needed,
        "vocabulary": lesson.vocabulary,
        "differentiation_notes": lesson.differentiation_notes,
        "accommodations": lesson.accommodations,
        "extensions": lesson.extensions,
        "assessment_strategy": lesson.assessment_strategy,
        "homework": lesson.homework,
        "reflection": lesson.reflection,
        "status": "draft",
        "is_active": True
    }

    result = supabase.table("lesson_plans").insert(lesson_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create lesson plan")

    return result.data[0]


@router.put("/{lesson_id}")
async def update_lesson_plan(
    lesson_id: UUID,
    update: LessonPlanUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update a lesson plan"""
    user_id = current_user["id"]

    existing = supabase.table("lesson_plans").select(
        "teacher_id"
    ).eq("id", str(lesson_id)).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Lesson plan not found")

    if existing.data["teacher_id"] != user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own lesson plans")

    update_data = {}
    if update.title is not None:
        update_data["title"] = update.title
    if update.lesson_date is not None:
        update_data["lesson_date"] = update.lesson_date.isoformat()
    if update.period is not None:
        update_data["period"] = update.period
    if update.objectives is not None:
        update_data["objectives"] = update.objectives
    if update.standard_ids is not None:
        update_data["standard_ids"] = [str(s) for s in update.standard_ids]
    if update.essential_questions is not None:
        update_data["essential_questions"] = update.essential_questions
    if update.sections is not None:
        update_data["sections"] = [s.dict() for s in update.sections]
    if update.materials_needed is not None:
        update_data["materials_needed"] = update.materials_needed
    if update.vocabulary is not None:
        update_data["vocabulary"] = update.vocabulary
    if update.differentiation_notes is not None:
        update_data["differentiation_notes"] = update.differentiation_notes
    if update.accommodations is not None:
        update_data["accommodations"] = update.accommodations
    if update.extensions is not None:
        update_data["extensions"] = update.extensions
    if update.assessment_strategy is not None:
        update_data["assessment_strategy"] = update.assessment_strategy
    if update.homework is not None:
        update_data["homework"] = update.homework
    if update.reflection is not None:
        update_data["reflection"] = update.reflection
    if update.status is not None:
        update_data["status"] = update.status

    result = supabase.table("lesson_plans").update(update_data).eq(
        "id", str(lesson_id)
    ).execute()

    return result.data[0] if result.data else None


@router.delete("/{lesson_id}")
async def delete_lesson_plan(
    lesson_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a lesson plan"""
    user_id = current_user["id"]

    existing = supabase.table("lesson_plans").select(
        "teacher_id"
    ).eq("id", str(lesson_id)).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Lesson plan not found")

    if existing.data["teacher_id"] != user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own lesson plans")

    supabase.table("lesson_plans").update({
        "is_active": False
    }).eq("id", str(lesson_id)).execute()

    return {"success": True}


@router.post("/{lesson_id}/copy")
async def copy_lesson_plan(
    lesson_id: UUID,
    copy_request: LessonPlanCopy,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Copy a lesson plan to one or more dates"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    original = supabase.table("lesson_plans").select("*").eq(
        "id", str(lesson_id)
    ).single().execute()

    if not original.data:
        raise HTTPException(status_code=404, detail="Lesson plan not found")

    created_plans = []
    for target_date in copy_request.target_dates:
        new_plan = {**original.data}
        del new_plan["id"]
        del new_plan["created_at"]
        del new_plan["updated_at"]
        new_plan["teacher_id"] = user_id
        new_plan["school_id"] = school_id
        new_plan["lesson_date"] = target_date.isoformat()
        new_plan["status"] = "draft"
        new_plan["reflection"] = None

        if copy_request.target_class_id:
            new_plan["class_id"] = str(copy_request.target_class_id)

        result = supabase.table("lesson_plans").insert(new_plan).execute()
        if result.data:
            created_plans.append(result.data[0])

    return {
        "success": True,
        "created_count": len(created_plans),
        "plans": created_plans
    }


@router.post("/{lesson_id}/mark-taught")
async def mark_lesson_taught(
    lesson_id: UUID,
    reflection: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Mark a lesson as taught and optionally add reflection"""
    user_id = current_user["id"]

    existing = supabase.table("lesson_plans").select(
        "teacher_id"
    ).eq("id", str(lesson_id)).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Lesson plan not found")

    if existing.data["teacher_id"] != user_id:
        raise HTTPException(status_code=403, detail="You can only update your own lesson plans")

    update_data = {
        "status": "reflected" if reflection else "taught",
        "taught_at": datetime.utcnow().isoformat()
    }

    if reflection:
        update_data["reflection"] = reflection

    supabase.table("lesson_plans").update(update_data).eq("id", str(lesson_id)).execute()

    return {"success": True}


@router.get("/{lesson_id}/print")
async def get_printable_lesson(
    lesson_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get lesson plan in a format suitable for printing"""
    lesson = await get_lesson_plan(lesson_id, current_user, supabase)

    # Format for printing
    printable = {
        "title": lesson["title"],
        "date": lesson["lesson_date"],
        "class": lesson.get("classes", {}).get("name", ""),
        "subject": lesson.get("subjects", {}).get("name", ""),
        "period": lesson.get("period"),
        "objectives": lesson.get("objectives", []),
        "standards": [s["code"] for s in lesson.get("standards", [])],
        "essential_questions": lesson.get("essential_questions", []),
        "materials": lesson.get("materials_needed", []),
        "vocabulary": lesson.get("vocabulary", []),
        "sections": [],
        "differentiation": lesson.get("differentiation_notes"),
        "accommodations": lesson.get("accommodations"),
        "extensions": lesson.get("extensions"),
        "assessment": lesson.get("assessment_strategy"),
        "homework": lesson.get("homework")
    }

    for section in (lesson.get("sections") or []):
        printable["sections"].append({
            "name": section.get("name"),
            "duration": section.get("duration_minutes"),
            "content": section.get("content"),
            "notes": section.get("notes")
        })

    return printable


# ============================================================
# STATISTICS & INSIGHTS
# ============================================================

@router.get("/stats/overview")
async def get_planning_stats(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get lesson planning statistics"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    query = supabase.table("lesson_plans").select(
        "id, status, lesson_date, class_id, subject_id"
    ).eq("school_id", school_id).eq("teacher_id", user_id).eq("is_active", True)

    if date_from:
        query = query.gte("lesson_date", date_from.isoformat())
    if date_to:
        query = query.lte("lesson_date", date_to.isoformat())

    result = query.execute()
    lessons = result.data or []

    # Calculate stats
    status_counts = {"draft": 0, "ready": 0, "taught": 0, "reflected": 0}
    classes = set()
    subjects = set()

    for lesson in lessons:
        status = lesson.get("status", "draft")
        if status in status_counts:
            status_counts[status] += 1
        classes.add(lesson.get("class_id"))
        subjects.add(lesson.get("subject_id"))

    return {
        "total_lessons": len(lessons),
        "status_breakdown": status_counts,
        "classes_planned": len(classes),
        "subjects_planned": len(subjects),
        "completion_rate": round(
            (status_counts["taught"] + status_counts["reflected"]) / len(lessons) * 100, 1
        ) if lessons else 0,
        "reflection_rate": round(
            status_counts["reflected"] / len(lessons) * 100, 1
        ) if lessons else 0
    }


@router.get("/stats/standards-coverage")
async def get_standards_coverage(
    class_id: Optional[UUID] = None,
    subject_id: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get standards coverage statistics"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    query = supabase.table("lesson_plans").select(
        "standard_ids"
    ).eq("school_id", school_id).eq("teacher_id", user_id).eq("is_active", True)

    if class_id:
        query = query.eq("class_id", str(class_id))
    if subject_id:
        query = query.eq("subject_id", str(subject_id))
    if date_from:
        query = query.gte("lesson_date", date_from.isoformat())
    if date_to:
        query = query.lte("lesson_date", date_to.isoformat())

    result = query.execute()

    # Count standard occurrences
    standard_counts = {}
    for lesson in (result.data or []):
        for sid in (lesson.get("standard_ids") or []):
            standard_counts[sid] = standard_counts.get(sid, 0) + 1

    # Get standard details
    if standard_counts:
        standards = supabase.table("learning_standards").select(
            "id, code, description"
        ).in_("id", list(standard_counts.keys())).execute()

        coverage = []
        for std in (standards.data or []):
            coverage.append({
                "standard_id": std["id"],
                "code": std["code"],
                "description": std["description"],
                "lesson_count": standard_counts.get(std["id"], 0)
            })

        coverage.sort(key=lambda x: x["lesson_count"], reverse=True)
    else:
        coverage = []

    return {
        "standards_covered": len(standard_counts),
        "coverage_details": coverage
    }
