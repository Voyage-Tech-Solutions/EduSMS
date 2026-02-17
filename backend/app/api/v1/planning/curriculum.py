"""
EduCore Backend - Curriculum Mapping API
Map curriculum standards to units, topics, and lessons
"""
import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# MODELS
# ============================================================

class CurriculumUnit(BaseModel):
    """A unit within a curriculum map"""
    id: str
    name: str
    description: Optional[str] = None
    duration_weeks: int = 2
    order_index: int = 0
    topics: List[str] = []
    standards: List[str] = []  # Standard IDs
    essential_questions: List[str] = []
    assessments: List[str] = []


class CurriculumMapCreate(BaseModel):
    """Create a curriculum map"""
    name: str
    description: Optional[str] = None
    subject_id: UUID
    grade_id: UUID
    academic_year_id: Optional[UUID] = None
    units: List[CurriculumUnit] = []


class CurriculumMapUpdate(BaseModel):
    """Update a curriculum map"""
    name: Optional[str] = None
    description: Optional[str] = None
    units: Optional[List[CurriculumUnit]] = None
    is_published: Optional[bool] = None


class StandardCreate(BaseModel):
    """Create a learning standard"""
    code: str
    description: str
    grade_level: Optional[str] = None
    subject: Optional[str] = None
    domain: Optional[str] = None
    parent_id: Optional[UUID] = None


class StandardUpdate(BaseModel):
    """Update a learning standard"""
    code: Optional[str] = None
    description: Optional[str] = None
    grade_level: Optional[str] = None
    subject: Optional[str] = None
    domain: Optional[str] = None


# ============================================================
# CURRICULUM MAP ENDPOINTS
# ============================================================

@router.get("/maps")
async def list_curriculum_maps(
    subject_id: Optional[UUID] = None,
    grade_id: Optional[UUID] = None,
    academic_year_id: Optional[UUID] = None,
    include_shared: bool = True,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List curriculum maps with filters"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    query = supabase.table("curriculum_maps").select(
        "*, subjects(name), grades(name), academic_years(name)"
    ).eq("school_id", school_id).eq("is_active", True)

    if not include_shared:
        query = query.eq("created_by", user_id)

    if subject_id:
        query = query.eq("subject_id", str(subject_id))
    if grade_id:
        query = query.eq("grade_id", str(grade_id))
    if academic_year_id:
        query = query.eq("academic_year_id", str(academic_year_id))

    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

    result = query.execute()

    return {
        "curriculum_maps": result.data or [],
        "total": len(result.data) if result.data else 0,
        "limit": limit,
        "offset": offset
    }


@router.get("/maps/{map_id}")
async def get_curriculum_map(
    map_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get a curriculum map with full details"""
    result = supabase.table("curriculum_maps").select(
        "*, subjects(name), grades(name), academic_years(name)"
    ).eq("id", str(map_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Curriculum map not found")

    # Get standards details for units
    curriculum_map = result.data
    units = curriculum_map.get("units") or []

    all_standard_ids = []
    for unit in units:
        all_standard_ids.extend(unit.get("standards", []))

    if all_standard_ids:
        standards_result = supabase.table("learning_standards").select(
            "id, code, description"
        ).in_("id", all_standard_ids).execute()

        standards_map = {s["id"]: s for s in (standards_result.data or [])}

        for unit in units:
            unit["standards_details"] = [
                standards_map.get(sid, {"id": sid})
                for sid in unit.get("standards", [])
            ]

    curriculum_map["units"] = units

    return curriculum_map


@router.post("/maps")
async def create_curriculum_map(
    curriculum_map: CurriculumMapCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a new curriculum map"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    map_data = {
        "school_id": school_id,
        "created_by": user_id,
        "name": curriculum_map.name,
        "description": curriculum_map.description,
        "subject_id": str(curriculum_map.subject_id),
        "grade_id": str(curriculum_map.grade_id),
        "academic_year_id": str(curriculum_map.academic_year_id) if curriculum_map.academic_year_id else None,
        "units": [u.dict() for u in curriculum_map.units],
        "is_published": False,
        "is_active": True
    }

    result = supabase.table("curriculum_maps").insert(map_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create curriculum map")

    return result.data[0]


@router.put("/maps/{map_id}")
async def update_curriculum_map(
    map_id: UUID,
    update: CurriculumMapUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update a curriculum map"""
    user_id = current_user["id"]

    existing = supabase.table("curriculum_maps").select(
        "created_by"
    ).eq("id", str(map_id)).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Curriculum map not found")

    if existing.data["created_by"] != user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own curriculum maps")

    update_data = {}
    if update.name is not None:
        update_data["name"] = update.name
    if update.description is not None:
        update_data["description"] = update.description
    if update.units is not None:
        update_data["units"] = [u.dict() for u in update.units]
    if update.is_published is not None:
        update_data["is_published"] = update.is_published

    result = supabase.table("curriculum_maps").update(update_data).eq("id", str(map_id)).execute()

    return result.data[0] if result.data else None


@router.delete("/maps/{map_id}")
async def delete_curriculum_map(
    map_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a curriculum map"""
    user_id = current_user["id"]

    existing = supabase.table("curriculum_maps").select(
        "created_by"
    ).eq("id", str(map_id)).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Curriculum map not found")

    if existing.data["created_by"] != user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own curriculum maps")

    supabase.table("curriculum_maps").update({
        "is_active": False
    }).eq("id", str(map_id)).execute()

    return {"success": True}


@router.post("/maps/{map_id}/duplicate")
async def duplicate_curriculum_map(
    map_id: UUID,
    new_name: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a copy of a curriculum map"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    original = supabase.table("curriculum_maps").select("*").eq(
        "id", str(map_id)
    ).single().execute()

    if not original.data:
        raise HTTPException(status_code=404, detail="Curriculum map not found")

    new_map = {**original.data}
    del new_map["id"]
    del new_map["created_at"]
    del new_map["updated_at"]
    new_map["created_by"] = user_id
    new_map["school_id"] = school_id
    new_map["name"] = new_name or f"(Copy) {new_map['name']}"
    new_map["is_published"] = False

    result = supabase.table("curriculum_maps").insert(new_map).execute()

    return result.data[0] if result.data else None


# ============================================================
# LEARNING STANDARDS ENDPOINTS
# ============================================================

@router.get("/standards")
async def list_standards(
    grade_level: Optional[str] = None,
    subject: Optional[str] = None,
    domain: Optional[str] = None,
    search: Optional[str] = None,
    parent_id: Optional[UUID] = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List learning standards with filters"""
    school_id = current_user.get("school_id")

    query = supabase.table("learning_standards").select("*").eq("school_id", school_id)

    if grade_level:
        query = query.eq("grade_level", grade_level)
    if subject:
        query = query.eq("subject", subject)
    if domain:
        query = query.eq("domain", domain)
    if search:
        query = query.or_(f"code.ilike.%{search}%,description.ilike.%{search}%")
    if parent_id:
        query = query.eq("parent_id", str(parent_id))
    else:
        # Get top-level standards by default
        query = query.is_("parent_id", "null")

    query = query.order("code").range(offset, offset + limit - 1)

    result = query.execute()

    # Get child counts
    standards = result.data or []
    for std in standards:
        children = supabase.table("learning_standards").select(
            "id", count="exact"
        ).eq("parent_id", std["id"]).execute()
        std["child_count"] = children.count or 0

    return {
        "standards": standards,
        "total": len(standards),
        "limit": limit,
        "offset": offset
    }


@router.get("/standards/{standard_id}")
async def get_standard(
    standard_id: UUID,
    include_children: bool = True,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get a learning standard with its children"""
    result = supabase.table("learning_standards").select("*").eq(
        "id", str(standard_id)
    ).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Standard not found")

    standard = result.data

    if include_children:
        children = supabase.table("learning_standards").select("*").eq(
            "parent_id", str(standard_id)
        ).order("code").execute()
        standard["children"] = children.data or []

    return standard


@router.post("/standards")
async def create_standard(
    standard: StandardCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a new learning standard"""
    school_id = current_user.get("school_id")

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    # Check for duplicate code
    existing = supabase.table("learning_standards").select("id").eq(
        "school_id", school_id
    ).eq("code", standard.code).execute()

    if existing.data:
        raise HTTPException(status_code=400, detail="Standard code already exists")

    standard_data = {
        "school_id": school_id,
        "code": standard.code,
        "description": standard.description,
        "grade_level": standard.grade_level,
        "subject": standard.subject,
        "domain": standard.domain,
        "parent_id": str(standard.parent_id) if standard.parent_id else None
    }

    result = supabase.table("learning_standards").insert(standard_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create standard")

    return result.data[0]


@router.put("/standards/{standard_id}")
async def update_standard(
    standard_id: UUID,
    update: StandardUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update a learning standard"""
    existing = supabase.table("learning_standards").select("id").eq(
        "id", str(standard_id)
    ).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Standard not found")

    update_data = {}
    if update.code is not None:
        update_data["code"] = update.code
    if update.description is not None:
        update_data["description"] = update.description
    if update.grade_level is not None:
        update_data["grade_level"] = update.grade_level
    if update.subject is not None:
        update_data["subject"] = update.subject
    if update.domain is not None:
        update_data["domain"] = update.domain

    result = supabase.table("learning_standards").update(update_data).eq(
        "id", str(standard_id)
    ).execute()

    return result.data[0] if result.data else None


@router.delete("/standards/{standard_id}")
async def delete_standard(
    standard_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a learning standard"""
    # Check for children
    children = supabase.table("learning_standards").select(
        "id", count="exact"
    ).eq("parent_id", str(standard_id)).execute()

    if children.count and children.count > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete standard with child standards"
        )

    supabase.table("learning_standards").delete().eq("id", str(standard_id)).execute()

    return {"success": True}


@router.post("/standards/import")
async def import_standards(
    standards: List[StandardCreate],
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Bulk import learning standards"""
    school_id = current_user.get("school_id")

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    standards_to_insert = []
    for s in standards:
        standards_to_insert.append({
            "school_id": school_id,
            "code": s.code,
            "description": s.description,
            "grade_level": s.grade_level,
            "subject": s.subject,
            "domain": s.domain,
            "parent_id": str(s.parent_id) if s.parent_id else None
        })

    result = supabase.table("learning_standards").insert(standards_to_insert).execute()

    return {
        "success": True,
        "imported": len(result.data) if result.data else 0
    }


@router.get("/standards/summary")
async def get_standards_summary(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get summary of standards by subject and grade"""
    school_id = current_user.get("school_id")

    result = supabase.table("learning_standards").select(
        "subject, grade_level"
    ).eq("school_id", school_id).execute()

    standards = result.data or []

    summary = {}
    for s in standards:
        subject = s.get("subject") or "Uncategorized"
        grade = s.get("grade_level") or "All Grades"

        if subject not in summary:
            summary[subject] = {"total": 0, "by_grade": {}}

        summary[subject]["total"] += 1

        if grade not in summary[subject]["by_grade"]:
            summary[subject]["by_grade"][grade] = 0
        summary[subject]["by_grade"][grade] += 1

    return {"summary": summary, "total_standards": len(standards)}
