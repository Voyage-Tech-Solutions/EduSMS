"""
EduCore Backend - Student Portfolios API
Digital portfolio management for student work artifacts
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

class ArtifactCreate(BaseModel):
    """Create a portfolio artifact"""
    student_id: UUID
    title: str
    description: Optional[str] = None
    artifact_type: str  # assignment, project, artwork, writing, assessment, certificate, other
    subject_id: Optional[UUID] = None
    file_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    external_url: Optional[str] = None
    date_created: Optional[date] = None
    tags: List[str] = []
    standard_ids: Optional[List[UUID]] = None
    reflection: Optional[str] = None
    is_featured: bool = False
    visibility: str = "private"  # private, teachers, parents, public


class ArtifactUpdate(BaseModel):
    """Update a portfolio artifact"""
    title: Optional[str] = None
    description: Optional[str] = None
    file_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    tags: Optional[List[str]] = None
    standard_ids: Optional[List[UUID]] = None
    reflection: Optional[str] = None
    is_featured: Optional[bool] = None
    visibility: Optional[str] = None


class ArtifactComment(BaseModel):
    """Comment on a portfolio artifact"""
    comment: str
    commenter_type: str = "teacher"  # teacher, parent, student


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/student/{student_id}")
async def get_student_portfolio(
    student_id: UUID,
    artifact_type: Optional[str] = None,
    subject_id: Optional[UUID] = None,
    tag: Optional[str] = None,
    featured_only: bool = False,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get a student's portfolio with their artifacts"""
    # Get student info
    student = supabase.table("students").select(
        "id, first_name, last_name, student_number, class_id, classes(name)"
    ).eq("id", str(student_id)).single().execute()

    if not student.data:
        raise HTTPException(status_code=404, detail="Student not found")

    # Get artifacts
    query = supabase.table("portfolio_artifacts").select(
        "*, subjects(name)"
    ).eq("student_id", str(student_id)).eq("is_active", True)

    if artifact_type:
        query = query.eq("artifact_type", artifact_type)
    if subject_id:
        query = query.eq("subject_id", str(subject_id))
    if tag:
        query = query.contains("tags", [tag])
    if featured_only:
        query = query.eq("is_featured", True)

    query = query.order("date_created", desc=True).range(offset, offset + limit - 1)

    artifacts = query.execute()

    # Get portfolio stats
    all_artifacts = supabase.table("portfolio_artifacts").select(
        "artifact_type, is_featured"
    ).eq("student_id", str(student_id)).eq("is_active", True).execute()

    type_counts = {}
    featured_count = 0
    for a in (all_artifacts.data or []):
        atype = a.get("artifact_type", "other")
        type_counts[atype] = type_counts.get(atype, 0) + 1
        if a.get("is_featured"):
            featured_count += 1

    return {
        "student": student.data,
        "artifacts": artifacts.data or [],
        "stats": {
            "total_artifacts": len(all_artifacts.data) if all_artifacts.data else 0,
            "featured_count": featured_count,
            "by_type": type_counts
        },
        "limit": limit,
        "offset": offset
    }


@router.get("/artifact/{artifact_id}")
async def get_artifact(
    artifact_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get a specific artifact with full details"""
    result = supabase.table("portfolio_artifacts").select(
        "*, students(first_name, last_name), subjects(name)"
    ).eq("id", str(artifact_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Artifact not found")

    artifact = result.data

    # Get standards if present
    if artifact.get("standard_ids"):
        standards = supabase.table("learning_standards").select(
            "id, code, description"
        ).in_("id", artifact["standard_ids"]).execute()
        artifact["standards"] = standards.data or []

    return artifact


@router.post("")
async def create_artifact(
    artifact: ArtifactCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a new portfolio artifact"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    artifact_data = {
        "school_id": school_id,
        "student_id": str(artifact.student_id),
        "created_by": user_id,
        "title": artifact.title,
        "description": artifact.description,
        "artifact_type": artifact.artifact_type,
        "subject_id": str(artifact.subject_id) if artifact.subject_id else None,
        "file_url": artifact.file_url,
        "thumbnail_url": artifact.thumbnail_url,
        "external_url": artifact.external_url,
        "date_created": artifact.date_created.isoformat() if artifact.date_created else date.today().isoformat(),
        "tags": artifact.tags,
        "standard_ids": [str(s) for s in artifact.standard_ids] if artifact.standard_ids else None,
        "reflection": artifact.reflection,
        "is_featured": artifact.is_featured,
        "visibility": artifact.visibility,
        "comments": [],
        "is_active": True
    }

    result = supabase.table("portfolio_artifacts").insert(artifact_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create artifact")

    return result.data[0]


@router.put("/artifact/{artifact_id}")
async def update_artifact(
    artifact_id: UUID,
    update: ArtifactUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update a portfolio artifact"""
    existing = supabase.table("portfolio_artifacts").select("id").eq(
        "id", str(artifact_id)
    ).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Artifact not found")

    update_data = {}
    if update.title is not None:
        update_data["title"] = update.title
    if update.description is not None:
        update_data["description"] = update.description
    if update.file_url is not None:
        update_data["file_url"] = update.file_url
    if update.thumbnail_url is not None:
        update_data["thumbnail_url"] = update.thumbnail_url
    if update.tags is not None:
        update_data["tags"] = update.tags
    if update.standard_ids is not None:
        update_data["standard_ids"] = [str(s) for s in update.standard_ids]
    if update.reflection is not None:
        update_data["reflection"] = update.reflection
    if update.is_featured is not None:
        update_data["is_featured"] = update.is_featured
    if update.visibility is not None:
        update_data["visibility"] = update.visibility

    result = supabase.table("portfolio_artifacts").update(update_data).eq(
        "id", str(artifact_id)
    ).execute()

    return result.data[0] if result.data else None


@router.delete("/artifact/{artifact_id}")
async def delete_artifact(
    artifact_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a portfolio artifact (soft delete)"""
    existing = supabase.table("portfolio_artifacts").select("id").eq(
        "id", str(artifact_id)
    ).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Artifact not found")

    supabase.table("portfolio_artifacts").update({
        "is_active": False
    }).eq("id", str(artifact_id)).execute()

    return {"success": True}


@router.post("/artifact/{artifact_id}/comment")
async def add_comment(
    artifact_id: UUID,
    comment: ArtifactComment,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Add a comment to a portfolio artifact"""
    user_id = current_user["id"]

    artifact = supabase.table("portfolio_artifacts").select(
        "comments"
    ).eq("id", str(artifact_id)).single().execute()

    if not artifact.data:
        raise HTTPException(status_code=404, detail="Artifact not found")

    comments = artifact.data.get("comments") or []
    comment_data = {
        "id": str(UUID()),
        "comment": comment.comment,
        "commenter_id": user_id,
        "commenter_type": comment.commenter_type,
        "created_at": datetime.utcnow().isoformat()
    }
    comments.append(comment_data)

    supabase.table("portfolio_artifacts").update({
        "comments": comments
    }).eq("id", str(artifact_id)).execute()

    return {"success": True, "comment": comment_data}


@router.post("/artifact/{artifact_id}/feature")
async def toggle_featured(
    artifact_id: UUID,
    is_featured: bool,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Toggle featured status of an artifact"""
    existing = supabase.table("portfolio_artifacts").select("id").eq(
        "id", str(artifact_id)
    ).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Artifact not found")

    supabase.table("portfolio_artifacts").update({
        "is_featured": is_featured
    }).eq("id", str(artifact_id)).execute()

    return {"success": True, "is_featured": is_featured}


@router.get("/class/{class_id}/showcase")
async def get_class_showcase(
    class_id: UUID,
    artifact_type: Optional[str] = None,
    limit: int = Query(default=20, le=50),
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get featured artifacts from a class for showcase"""
    # Get students in class
    students = supabase.table("students").select("id").eq(
        "class_id", str(class_id)
    ).execute()

    student_ids = [s["id"] for s in (students.data or [])]

    if not student_ids:
        return {"artifacts": [], "total": 0}

    # Get featured artifacts
    query = supabase.table("portfolio_artifacts").select(
        "*, students(first_name, last_name), subjects(name)"
    ).in_("student_id", student_ids).eq("is_active", True).eq("is_featured", True)

    if artifact_type:
        query = query.eq("artifact_type", artifact_type)

    # Only get public or teacher-visible artifacts
    query = query.in_("visibility", ["public", "teachers"])

    query = query.order("date_created", desc=True).limit(limit)

    result = query.execute()

    return {
        "artifacts": result.data or [],
        "total": len(result.data) if result.data else 0
    }


@router.get("/student/{student_id}/tags")
async def get_student_tags(
    student_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get all unique tags used by a student"""
    result = supabase.table("portfolio_artifacts").select("tags").eq(
        "student_id", str(student_id)
    ).eq("is_active", True).execute()

    all_tags = set()
    for artifact in (result.data or []):
        tags = artifact.get("tags") or []
        all_tags.update(tags)

    return {"tags": sorted(list(all_tags))}
