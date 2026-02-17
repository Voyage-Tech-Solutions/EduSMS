"""
EduCore Backend - Gradebook Routes
Main gradebook entry management endpoints
"""
import logging
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_supabase
from app.core.audit import audit_logger

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# MODELS
# ============================================================

class GradebookEntryCreate(BaseModel):
    """Create a gradebook entry"""
    student_id: UUID
    class_id: UUID
    subject_id: UUID
    assessment_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    score: float
    max_score: float = 100
    weight: float = 1.0
    is_extra_credit: bool = False
    notes: Optional[str] = None


class GradebookEntryUpdate(BaseModel):
    """Update a gradebook entry"""
    score: Optional[float] = None
    max_score: Optional[float] = None
    weight: Optional[float] = None
    is_missing: Optional[bool] = None
    is_excused: Optional[bool] = None
    notes: Optional[str] = None


class BulkGradeEntry(BaseModel):
    """Bulk grade entry for a class"""
    assessment_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    max_score: float = 100
    entries: List[dict]  # [{student_id, score, notes}]


class GradebookEntryResponse(BaseModel):
    """Gradebook entry response"""
    id: UUID
    student_id: UUID
    student_name: Optional[str] = None
    class_id: UUID
    subject_id: UUID
    assessment_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    category_name: Optional[str] = None
    score: Optional[float] = None
    max_score: float
    percentage: Optional[float] = None
    letter_grade: Optional[str] = None
    weight: float
    is_extra_credit: bool
    is_missing: bool
    is_excused: bool
    notes: Optional[str] = None
    entered_by: Optional[UUID] = None
    entered_at: Optional[datetime] = None


class StudentGradeSummary(BaseModel):
    """Summary of a student's grades in a class"""
    student_id: UUID
    student_name: str
    class_id: UUID
    subject_id: UUID
    total_entries: int
    graded_entries: int
    missing_entries: int
    raw_average: Optional[float] = None
    weighted_average: Optional[float] = None
    letter_grade: Optional[str] = None
    category_breakdown: List[dict] = []


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/class/{class_id}/subject/{subject_id}")
async def get_class_gradebook(
    class_id: UUID,
    subject_id: UUID,
    term_id: Optional[UUID] = None,
    category_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Get the full gradebook for a class/subject.
    Returns all students with their grades.
    """
    school_id = current_user.get("school_id")
    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    # Get all students in the class
    students_result = supabase.table("students").select(
        "id, first_name, last_name, admission_number"
    ).eq("class_id", str(class_id)).eq("status", "active").order("last_name").execute()

    students = students_result.data or []

    # Get all gradebook entries for this class/subject
    query = supabase.table("gradebook_entries").select(
        "*, grade_categories(name)"
    ).eq("class_id", str(class_id)).eq("subject_id", str(subject_id))

    if term_id:
        query = query.eq("term_id", str(term_id))
    if category_id:
        query = query.eq("category_id", str(category_id))

    entries_result = query.execute()
    entries = entries_result.data or []

    # Get categories for this class/subject
    categories_result = supabase.table("grade_categories").select(
        "id, name, weight"
    ).eq("class_id", str(class_id)).eq("subject_id", str(subject_id)).execute()

    categories = categories_result.data or []

    # Get assessments for this class
    assessments_result = supabase.table("assessments").select(
        "id, title, max_score, category_id"
    ).eq("class_id", str(class_id)).eq("subject_id", str(subject_id)).order("created_at", desc=True).execute()

    assessments = assessments_result.data or []

    # Organize entries by student
    student_entries = {}
    for student in students:
        student_id = student["id"]
        student_entries[student_id] = {
            "student": student,
            "entries": [],
            "summary": {}
        }

    for entry in entries:
        student_id = entry["student_id"]
        if student_id in student_entries:
            student_entries[student_id]["entries"].append(entry)

    # Calculate summaries
    for student_id, data in student_entries.items():
        entries = data["entries"]
        graded = [e for e in entries if e["score"] is not None and not e["is_excused"]]
        missing = [e for e in entries if e["is_missing"]]

        if graded:
            total_score = sum(e["score"] for e in graded)
            total_max = sum(e["max_score"] for e in graded)
            raw_avg = (total_score / total_max * 100) if total_max > 0 else None
        else:
            raw_avg = None

        data["summary"] = {
            "total_entries": len(entries),
            "graded_entries": len(graded),
            "missing_entries": len(missing),
            "raw_average": round(raw_avg, 2) if raw_avg else None
        }

    return {
        "class_id": str(class_id),
        "subject_id": str(subject_id),
        "categories": categories,
        "assessments": assessments,
        "students": list(student_entries.values())
    }


@router.post("/entry", response_model=GradebookEntryResponse)
async def create_gradebook_entry(
    entry: GradebookEntryCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a single gradebook entry"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    # Calculate percentage
    percentage = (entry.score / entry.max_score * 100) if entry.max_score > 0 else 0

    entry_data = {
        "school_id": school_id,
        "student_id": str(entry.student_id),
        "class_id": str(entry.class_id),
        "subject_id": str(entry.subject_id),
        "assessment_id": str(entry.assessment_id) if entry.assessment_id else None,
        "category_id": str(entry.category_id) if entry.category_id else None,
        "score": entry.score,
        "max_score": entry.max_score,
        "percentage": round(percentage, 2),
        "weight": entry.weight,
        "is_extra_credit": entry.is_extra_credit,
        "is_missing": False,
        "is_excused": False,
        "notes": entry.notes,
        "entered_by": user_id,
        "entered_at": datetime.utcnow().isoformat()
    }

    result = supabase.table("gradebook_entries").insert(entry_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create entry")

    # Audit log
    await audit_logger.log(
        supabase=supabase,
        action="gradebook.entry_create",
        user_id=user_id,
        school_id=school_id,
        entity_type="gradebook_entry",
        entity_id=result.data[0]["id"],
        metadata={
            "student_id": str(entry.student_id),
            "score": entry.score,
            "max_score": entry.max_score
        }
    )

    return GradebookEntryResponse(**result.data[0])


@router.post("/bulk-entry")
async def create_bulk_gradebook_entries(
    bulk_entry: BulkGradeEntry,
    class_id: UUID,
    subject_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create multiple gradebook entries at once (for an assessment)"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    now = datetime.utcnow().isoformat()
    entries_to_insert = []

    for entry in bulk_entry.entries:
        student_id = entry.get("student_id")
        score = entry.get("score")

        if student_id is None:
            continue

        percentage = (score / bulk_entry.max_score * 100) if score is not None and bulk_entry.max_score > 0 else None

        entries_to_insert.append({
            "school_id": school_id,
            "student_id": str(student_id),
            "class_id": str(class_id),
            "subject_id": str(subject_id),
            "assessment_id": str(bulk_entry.assessment_id) if bulk_entry.assessment_id else None,
            "category_id": str(bulk_entry.category_id) if bulk_entry.category_id else None,
            "score": score,
            "max_score": bulk_entry.max_score,
            "percentage": round(percentage, 2) if percentage else None,
            "is_missing": score is None,
            "notes": entry.get("notes"),
            "entered_by": user_id,
            "entered_at": now
        })

    if not entries_to_insert:
        raise HTTPException(status_code=400, detail="No valid entries provided")

    result = supabase.table("gradebook_entries").insert(entries_to_insert).execute()

    # Audit log
    await audit_logger.log(
        supabase=supabase,
        action="gradebook.bulk_entry",
        user_id=user_id,
        school_id=school_id,
        entity_type="gradebook_entry",
        metadata={
            "class_id": str(class_id),
            "subject_id": str(subject_id),
            "entries_count": len(entries_to_insert)
        }
    )

    return {
        "success": True,
        "entries_created": len(result.data) if result.data else 0
    }


@router.put("/entry/{entry_id}", response_model=GradebookEntryResponse)
async def update_gradebook_entry(
    entry_id: UUID,
    update: GradebookEntryUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update a gradebook entry"""
    user_id = current_user["id"]
    school_id = current_user.get("school_id")

    # Get existing entry
    existing = supabase.table("gradebook_entries").select(
        "*"
    ).eq("id", str(entry_id)).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Entry not found")

    update_data = {}
    if update.score is not None:
        update_data["score"] = update.score
        max_score = update.max_score or existing.data["max_score"]
        update_data["percentage"] = round(update.score / max_score * 100, 2) if max_score > 0 else 0

    if update.max_score is not None:
        update_data["max_score"] = update.max_score
        if "score" not in update_data and existing.data["score"]:
            update_data["percentage"] = round(existing.data["score"] / update.max_score * 100, 2)

    if update.weight is not None:
        update_data["weight"] = update.weight
    if update.is_missing is not None:
        update_data["is_missing"] = update.is_missing
    if update.is_excused is not None:
        update_data["is_excused"] = update.is_excused
    if update.notes is not None:
        update_data["notes"] = update.notes

    update_data["modified_by"] = user_id
    update_data["modified_at"] = datetime.utcnow().isoformat()

    result = supabase.table("gradebook_entries").update(
        update_data
    ).eq("id", str(entry_id)).execute()

    # Audit log
    await audit_logger.log(
        supabase=supabase,
        action="gradebook.entry_update",
        user_id=user_id,
        school_id=school_id,
        entity_type="gradebook_entry",
        entity_id=str(entry_id),
        before_data=existing.data,
        after_data=update_data
    )

    return GradebookEntryResponse(**result.data[0])


@router.delete("/entry/{entry_id}")
async def delete_gradebook_entry(
    entry_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a gradebook entry"""
    user_id = current_user["id"]
    school_id = current_user.get("school_id")

    # Get existing entry for audit
    existing = supabase.table("gradebook_entries").select(
        "*"
    ).eq("id", str(entry_id)).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Entry not found")

    supabase.table("gradebook_entries").delete().eq("id", str(entry_id)).execute()

    # Audit log
    await audit_logger.log(
        supabase=supabase,
        action="gradebook.entry_delete",
        user_id=user_id,
        school_id=school_id,
        entity_type="gradebook_entry",
        entity_id=str(entry_id),
        before_data=existing.data,
        severity="warning"
    )

    return {"success": True}


@router.get("/student/{student_id}/summary")
async def get_student_grade_summary(
    student_id: UUID,
    class_id: Optional[UUID] = None,
    subject_id: Optional[UUID] = None,
    term_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get grade summary for a student"""
    school_id = current_user.get("school_id")

    # Get student info
    student = supabase.table("students").select(
        "id, first_name, last_name, class_id"
    ).eq("id", str(student_id)).single().execute()

    if not student.data:
        raise HTTPException(status_code=404, detail="Student not found")

    # Build query for entries
    query = supabase.table("gradebook_entries").select(
        "*, grade_categories(name, weight)"
    ).eq("student_id", str(student_id))

    if class_id:
        query = query.eq("class_id", str(class_id))
    if subject_id:
        query = query.eq("subject_id", str(subject_id))
    if term_id:
        query = query.eq("term_id", str(term_id))

    entries_result = query.execute()
    entries = entries_result.data or []

    # Calculate summary
    graded = [e for e in entries if e["score"] is not None and not e["is_excused"]]
    missing = [e for e in entries if e["is_missing"]]

    # Raw average
    if graded:
        total_score = sum(e["score"] for e in graded)
        total_max = sum(e["max_score"] for e in graded)
        raw_average = round((total_score / total_max * 100), 2) if total_max > 0 else None
    else:
        raw_average = None

    # Category breakdown
    category_scores = {}
    for entry in graded:
        cat_id = entry.get("category_id") or "uncategorized"
        cat_name = entry.get("grade_categories", {}).get("name", "Uncategorized") if entry.get("grade_categories") else "Uncategorized"
        cat_weight = entry.get("grade_categories", {}).get("weight", 0) if entry.get("grade_categories") else 0

        if cat_id not in category_scores:
            category_scores[cat_id] = {
                "category_id": cat_id,
                "name": cat_name,
                "weight": cat_weight,
                "total_score": 0,
                "total_max": 0,
                "count": 0
            }

        category_scores[cat_id]["total_score"] += entry["score"]
        category_scores[cat_id]["total_max"] += entry["max_score"]
        category_scores[cat_id]["count"] += 1

    # Calculate category averages
    category_breakdown = []
    for cat_data in category_scores.values():
        avg = (cat_data["total_score"] / cat_data["total_max"] * 100) if cat_data["total_max"] > 0 else None
        category_breakdown.append({
            "category_id": cat_data["category_id"],
            "name": cat_data["name"],
            "weight": cat_data["weight"],
            "average": round(avg, 2) if avg else None,
            "entries_count": cat_data["count"]
        })

    return {
        "student_id": str(student_id),
        "student_name": f"{student.data['first_name']} {student.data['last_name']}",
        "total_entries": len(entries),
        "graded_entries": len(graded),
        "missing_entries": len(missing),
        "raw_average": raw_average,
        "category_breakdown": category_breakdown
    }


@router.post("/entry/{entry_id}/excuse")
async def excuse_gradebook_entry(
    entry_id: UUID,
    reason: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Mark a gradebook entry as excused"""
    user_id = current_user["id"]

    result = supabase.table("gradebook_entries").update({
        "is_excused": True,
        "is_missing": False,
        "notes": reason,
        "modified_by": user_id,
        "modified_at": datetime.utcnow().isoformat()
    }).eq("id", str(entry_id)).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Entry not found")

    return {"success": True, "entry": result.data[0]}


@router.post("/entry/{entry_id}/unexcuse")
async def unexcuse_gradebook_entry(
    entry_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Remove excused status from a gradebook entry"""
    user_id = current_user["id"]

    result = supabase.table("gradebook_entries").update({
        "is_excused": False,
        "modified_by": user_id,
        "modified_at": datetime.utcnow().isoformat()
    }).eq("id", str(entry_id)).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Entry not found")

    return {"success": True, "entry": result.data[0]}
