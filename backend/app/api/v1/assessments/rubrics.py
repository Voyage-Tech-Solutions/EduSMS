"""
EduCore Backend - Rubrics API
Create and manage rubrics for grading assignments and assessments
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

class RubricLevel(BaseModel):
    """Single level/score point in a rubric criterion"""
    score: float
    label: str  # e.g., "Excellent", "Proficient", "Developing", "Beginning"
    description: str


class RubricCriterion(BaseModel):
    """Single criterion in a rubric"""
    id: str
    name: str  # e.g., "Content", "Organization", "Grammar"
    description: Optional[str] = None
    weight: float = 1.0  # Relative weight for weighted scoring
    levels: List[RubricLevel]


class RubricCreate(BaseModel):
    """Create a new rubric"""
    title: str
    description: Optional[str] = None
    subject_id: Optional[UUID] = None
    criteria: List[RubricCriterion]
    max_score: Optional[float] = None  # If null, calculated from criteria
    is_template: bool = False
    is_shared: bool = False


class RubricUpdate(BaseModel):
    """Update rubric details"""
    title: Optional[str] = None
    description: Optional[str] = None
    criteria: Optional[List[RubricCriterion]] = None
    max_score: Optional[float] = None
    is_shared: Optional[bool] = None
    is_active: Optional[bool] = None


class RubricScoreEntry(BaseModel):
    """Score for a single criterion"""
    criterion_id: str
    score: float
    feedback: Optional[str] = None


class RubricGradeRequest(BaseModel):
    """Grade submission using rubric"""
    student_id: UUID
    assessment_id: Optional[UUID] = None
    assignment_id: Optional[UUID] = None
    scores: List[RubricScoreEntry]
    overall_feedback: Optional[str] = None


# ============================================================
# RUBRIC TEMPLATES
# ============================================================

RUBRIC_TEMPLATES = {
    "essay_4point": {
        "title": "Essay Rubric (4-Point Scale)",
        "description": "Standard 4-point rubric for essay assignments",
        "criteria": [
            {
                "id": "content",
                "name": "Content & Ideas",
                "description": "Quality and depth of ideas presented",
                "weight": 1.0,
                "levels": [
                    {"score": 4, "label": "Excellent", "description": "Ideas are exceptionally clear, focused, and engaging. Strong evidence and examples support the thesis."},
                    {"score": 3, "label": "Proficient", "description": "Ideas are clear and focused. Good evidence and examples support the thesis."},
                    {"score": 2, "label": "Developing", "description": "Ideas are somewhat clear but may lack focus. Limited evidence or examples."},
                    {"score": 1, "label": "Beginning", "description": "Ideas are unclear or unfocused. Little to no evidence or examples."}
                ]
            },
            {
                "id": "organization",
                "name": "Organization",
                "description": "Structure and flow of the essay",
                "weight": 1.0,
                "levels": [
                    {"score": 4, "label": "Excellent", "description": "Exceptionally clear organization with smooth transitions. Introduction and conclusion are compelling."},
                    {"score": 3, "label": "Proficient", "description": "Clear organization with good transitions. Effective introduction and conclusion."},
                    {"score": 2, "label": "Developing", "description": "Some organization present but may be unclear. Transitions may be weak."},
                    {"score": 1, "label": "Beginning", "description": "Little or no clear organization. Missing or weak introduction/conclusion."}
                ]
            },
            {
                "id": "language",
                "name": "Language Use",
                "description": "Word choice, sentence structure, and voice",
                "weight": 1.0,
                "levels": [
                    {"score": 4, "label": "Excellent", "description": "Sophisticated word choice. Varied sentence structure. Strong, consistent voice."},
                    {"score": 3, "label": "Proficient", "description": "Appropriate word choice. Good sentence variety. Clear voice."},
                    {"score": 2, "label": "Developing", "description": "Basic word choice. Some sentence variety. Voice may be inconsistent."},
                    {"score": 1, "label": "Beginning", "description": "Limited vocabulary. Simple or repetitive sentences. No clear voice."}
                ]
            },
            {
                "id": "conventions",
                "name": "Conventions",
                "description": "Grammar, spelling, punctuation, and formatting",
                "weight": 1.0,
                "levels": [
                    {"score": 4, "label": "Excellent", "description": "Few to no errors in grammar, spelling, or punctuation. Proper formatting throughout."},
                    {"score": 3, "label": "Proficient", "description": "Minor errors that don't impede understanding. Generally proper formatting."},
                    {"score": 2, "label": "Developing", "description": "Some errors that may affect readability. Inconsistent formatting."},
                    {"score": 1, "label": "Beginning", "description": "Frequent errors that significantly impede understanding. Poor formatting."}
                ]
            }
        ]
    },
    "presentation": {
        "title": "Presentation Rubric",
        "description": "Rubric for evaluating oral presentations",
        "criteria": [
            {
                "id": "content",
                "name": "Content Knowledge",
                "weight": 1.5,
                "levels": [
                    {"score": 4, "label": "Excellent", "description": "Demonstrates exceptional understanding. Answers questions confidently and accurately."},
                    {"score": 3, "label": "Proficient", "description": "Demonstrates good understanding. Answers most questions accurately."},
                    {"score": 2, "label": "Developing", "description": "Demonstrates basic understanding. May struggle with some questions."},
                    {"score": 1, "label": "Beginning", "description": "Shows limited understanding of the topic."}
                ]
            },
            {
                "id": "delivery",
                "name": "Delivery & Presence",
                "weight": 1.0,
                "levels": [
                    {"score": 4, "label": "Excellent", "description": "Confident delivery. Excellent eye contact. Engaging presence."},
                    {"score": 3, "label": "Proficient", "description": "Good delivery. Consistent eye contact. Appropriate presence."},
                    {"score": 2, "label": "Developing", "description": "Somewhat hesitant. Inconsistent eye contact."},
                    {"score": 1, "label": "Beginning", "description": "Reads from notes. Little eye contact. Appears uncomfortable."}
                ]
            },
            {
                "id": "visuals",
                "name": "Visual Aids",
                "weight": 1.0,
                "levels": [
                    {"score": 4, "label": "Excellent", "description": "Visuals enhance understanding. Professional quality. Well-integrated."},
                    {"score": 3, "label": "Proficient", "description": "Visuals support content. Good quality. Generally well-used."},
                    {"score": 2, "label": "Developing", "description": "Visuals present but basic. May not fully support content."},
                    {"score": 1, "label": "Beginning", "description": "Visuals missing, poor quality, or distracting."}
                ]
            },
            {
                "id": "time",
                "name": "Time Management",
                "weight": 0.5,
                "levels": [
                    {"score": 4, "label": "Excellent", "description": "Perfect timing. Well-paced throughout."},
                    {"score": 3, "label": "Proficient", "description": "Within time limits. Generally good pacing."},
                    {"score": 2, "label": "Developing", "description": "Slightly over/under time. Some pacing issues."},
                    {"score": 1, "label": "Beginning", "description": "Significantly over/under time. Poor pacing."}
                ]
            }
        ]
    },
    "project_based": {
        "title": "Project Rubric",
        "description": "Rubric for project-based assessments",
        "criteria": [
            {
                "id": "planning",
                "name": "Planning & Process",
                "weight": 1.0,
                "levels": [
                    {"score": 4, "label": "Excellent", "description": "Thorough planning evident. Excellent time management. Process well-documented."},
                    {"score": 3, "label": "Proficient", "description": "Good planning. Met deadlines. Process documented."},
                    {"score": 2, "label": "Developing", "description": "Some planning evident. May have missed some deadlines."},
                    {"score": 1, "label": "Beginning", "description": "Little evidence of planning. Significant deadline issues."}
                ]
            },
            {
                "id": "research",
                "name": "Research & Sources",
                "weight": 1.0,
                "levels": [
                    {"score": 4, "label": "Excellent", "description": "Extensive, high-quality research. Diverse, credible sources. Proper citations."},
                    {"score": 3, "label": "Proficient", "description": "Good research. Multiple credible sources. Mostly proper citations."},
                    {"score": 2, "label": "Developing", "description": "Basic research. Limited sources. Some citation errors."},
                    {"score": 1, "label": "Beginning", "description": "Minimal research. Few or unreliable sources."}
                ]
            },
            {
                "id": "creativity",
                "name": "Creativity & Innovation",
                "weight": 1.0,
                "levels": [
                    {"score": 4, "label": "Excellent", "description": "Highly creative approach. Original ideas. Innovative solutions."},
                    {"score": 3, "label": "Proficient", "description": "Creative approach. Some original elements."},
                    {"score": 2, "label": "Developing", "description": "Some creativity shown. Mostly conventional approach."},
                    {"score": 1, "label": "Beginning", "description": "Little creativity. Generic approach."}
                ]
            },
            {
                "id": "quality",
                "name": "Final Product Quality",
                "weight": 1.5,
                "levels": [
                    {"score": 4, "label": "Excellent", "description": "Exceptional quality. Exceeds all requirements. Professional level work."},
                    {"score": 3, "label": "Proficient", "description": "Good quality. Meets all requirements."},
                    {"score": 2, "label": "Developing", "description": "Acceptable quality. Meets most requirements."},
                    {"score": 1, "label": "Beginning", "description": "Poor quality. Missing key requirements."}
                ]
            },
            {
                "id": "collaboration",
                "name": "Collaboration (if group)",
                "weight": 1.0,
                "levels": [
                    {"score": 4, "label": "Excellent", "description": "Outstanding teamwork. Equal contribution. Effective communication."},
                    {"score": 3, "label": "Proficient", "description": "Good teamwork. Most members contributed. Good communication."},
                    {"score": 2, "label": "Developing", "description": "Some collaboration issues. Uneven contributions."},
                    {"score": 1, "label": "Beginning", "description": "Poor collaboration. Significant contribution imbalance."}
                ]
            }
        ]
    },
    "standards_based": {
        "title": "Standards-Based Rubric (1-4 Scale)",
        "description": "Simple 4-point standards-based grading rubric",
        "criteria": [
            {
                "id": "standard_mastery",
                "name": "Standard Mastery",
                "weight": 1.0,
                "levels": [
                    {"score": 4, "label": "Exceeds Standard", "description": "Demonstrates mastery and can apply/extend learning to new situations"},
                    {"score": 3, "label": "Meets Standard", "description": "Demonstrates proficient understanding of the standard"},
                    {"score": 2, "label": "Approaching Standard", "description": "Demonstrates partial understanding; needs additional support"},
                    {"score": 1, "label": "Below Standard", "description": "Does not yet demonstrate understanding of the standard"}
                ]
            }
        ]
    }
}


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("")
async def list_rubrics(
    subject_id: Optional[UUID] = None,
    include_templates: bool = True,
    include_shared: bool = True,
    search: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List rubrics with filters"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    # Build query
    query = supabase.table("rubrics").select(
        "*, subjects(name)"
    ).eq("school_id", school_id).eq("is_active", True)

    # Filter: own rubrics, templates, or shared
    conditions = [f"teacher_id.eq.{user_id}"]
    if include_templates:
        conditions.append("is_template.eq.true")
    if include_shared:
        conditions.append("is_shared.eq.true")

    query = query.or_(",".join(conditions))

    if subject_id:
        query = query.eq("subject_id", str(subject_id))
    if search:
        query = query.ilike("title", f"%{search}%")

    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

    result = query.execute()

    return {
        "rubrics": result.data or [],
        "total": len(result.data) if result.data else 0,
        "limit": limit,
        "offset": offset
    }


@router.get("/templates")
async def get_rubric_templates(
    current_user: dict = Depends(get_current_user)
):
    """Get available rubric templates"""
    templates = []
    for key, template in RUBRIC_TEMPLATES.items():
        templates.append({
            "id": key,
            "title": template["title"],
            "description": template["description"],
            "criteria_count": len(template["criteria"]),
            "max_score": sum(
                max(level["score"] for level in c["levels"]) * c.get("weight", 1.0)
                for c in template["criteria"]
            )
        })
    return {"templates": templates}


@router.get("/templates/{template_id}")
async def get_rubric_template(
    template_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific rubric template with full details"""
    if template_id not in RUBRIC_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")

    return RUBRIC_TEMPLATES[template_id]


@router.get("/{rubric_id}")
async def get_rubric(
    rubric_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get a specific rubric"""
    result = supabase.table("rubrics").select(
        "*, subjects(name)"
    ).eq("id", str(rubric_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Rubric not found")

    return result.data


@router.post("")
async def create_rubric(
    rubric: RubricCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a new rubric"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    # Calculate max score if not provided
    max_score = rubric.max_score
    if max_score is None:
        max_score = sum(
            max(level.score for level in c.levels) * c.weight
            for c in rubric.criteria
        )

    rubric_data = {
        "school_id": school_id,
        "teacher_id": user_id,
        "title": rubric.title,
        "description": rubric.description,
        "subject_id": str(rubric.subject_id) if rubric.subject_id else None,
        "criteria": [c.dict() for c in rubric.criteria],
        "max_score": max_score,
        "is_template": rubric.is_template,
        "is_shared": rubric.is_shared,
        "is_active": True
    }

    result = supabase.table("rubrics").insert(rubric_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create rubric")

    return result.data[0]


@router.post("/from-template/{template_id}")
async def create_from_template(
    template_id: str,
    title: Optional[str] = None,
    subject_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a rubric from a template"""
    if template_id not in RUBRIC_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")

    template = RUBRIC_TEMPLATES[template_id]
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    max_score = sum(
        max(level["score"] for level in c["levels"]) * c.get("weight", 1.0)
        for c in template["criteria"]
    )

    rubric_data = {
        "school_id": school_id,
        "teacher_id": user_id,
        "title": title or template["title"],
        "description": template["description"],
        "subject_id": str(subject_id) if subject_id else None,
        "criteria": template["criteria"],
        "max_score": max_score,
        "is_template": False,
        "is_shared": False,
        "is_active": True
    }

    result = supabase.table("rubrics").insert(rubric_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create rubric")

    return result.data[0]


@router.put("/{rubric_id}")
async def update_rubric(
    rubric_id: UUID,
    update: RubricUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update a rubric"""
    user_id = current_user["id"]

    # Check ownership
    existing = supabase.table("rubrics").select(
        "teacher_id"
    ).eq("id", str(rubric_id)).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Rubric not found")

    if existing.data["teacher_id"] != user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own rubrics")

    update_data = {}
    if update.title is not None:
        update_data["title"] = update.title
    if update.description is not None:
        update_data["description"] = update.description
    if update.criteria is not None:
        update_data["criteria"] = [c.dict() for c in update.criteria]
        # Recalculate max score
        update_data["max_score"] = sum(
            max(level.score for level in c.levels) * c.weight
            for c in update.criteria
        )
    if update.max_score is not None:
        update_data["max_score"] = update.max_score
    if update.is_shared is not None:
        update_data["is_shared"] = update.is_shared
    if update.is_active is not None:
        update_data["is_active"] = update.is_active

    result = supabase.table("rubrics").update(update_data).eq("id", str(rubric_id)).execute()

    return result.data[0] if result.data else None


@router.delete("/{rubric_id}")
async def delete_rubric(
    rubric_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a rubric (soft delete)"""
    user_id = current_user["id"]

    # Check ownership
    existing = supabase.table("rubrics").select(
        "teacher_id"
    ).eq("id", str(rubric_id)).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Rubric not found")

    if existing.data["teacher_id"] != user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own rubrics")

    supabase.table("rubrics").update({
        "is_active": False
    }).eq("id", str(rubric_id)).execute()

    return {"success": True}


@router.post("/{rubric_id}/duplicate")
async def duplicate_rubric(
    rubric_id: UUID,
    new_title: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a copy of a rubric"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    # Get original
    original = supabase.table("rubrics").select("*").eq(
        "id", str(rubric_id)
    ).single().execute()

    if not original.data:
        raise HTTPException(status_code=404, detail="Rubric not found")

    # Create copy
    new_rubric = {**original.data}
    del new_rubric["id"]
    del new_rubric["created_at"]
    del new_rubric["updated_at"]
    new_rubric["teacher_id"] = user_id
    new_rubric["school_id"] = school_id
    new_rubric["title"] = new_title or f"(Copy) {new_rubric['title']}"
    new_rubric["is_template"] = False

    result = supabase.table("rubrics").insert(new_rubric).execute()

    return result.data[0] if result.data else None


# ============================================================
# GRADING WITH RUBRICS
# ============================================================

@router.post("/{rubric_id}/grade")
async def grade_with_rubric(
    rubric_id: UUID,
    grade_request: RubricGradeRequest,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Grade a student submission using a rubric"""
    user_id = current_user["id"]
    school_id = current_user.get("school_id")

    # Get rubric
    rubric = supabase.table("rubrics").select("*").eq(
        "id", str(rubric_id)
    ).single().execute()

    if not rubric.data:
        raise HTTPException(status_code=404, detail="Rubric not found")

    criteria = rubric.data.get("criteria", [])

    # Calculate scores
    criterion_scores = {}
    weighted_total = 0
    total_weight = 0

    for score_entry in grade_request.scores:
        criterion = next(
            (c for c in criteria if c["id"] == score_entry.criterion_id),
            None
        )
        if not criterion:
            raise HTTPException(
                status_code=400,
                detail=f"Criterion {score_entry.criterion_id} not found in rubric"
            )

        # Validate score is within levels
        valid_scores = [level["score"] for level in criterion["levels"]]
        if score_entry.score not in valid_scores:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid score {score_entry.score} for criterion {criterion['name']}"
            )

        weight = criterion.get("weight", 1.0)
        weighted_total += score_entry.score * weight
        total_weight += weight

        criterion_scores[score_entry.criterion_id] = {
            "score": score_entry.score,
            "max_score": max(level["score"] for level in criterion["levels"]),
            "weight": weight,
            "feedback": score_entry.feedback,
            "criterion_name": criterion["name"]
        }

    # Calculate final score as percentage of max
    max_weighted_total = sum(
        max(level["score"] for level in c["levels"]) * c.get("weight", 1.0)
        for c in criteria
    )

    final_percentage = (weighted_total / max_weighted_total * 100) if max_weighted_total > 0 else 0

    # Store the rubric grade
    grade_data = {
        "school_id": school_id,
        "rubric_id": str(rubric_id),
        "student_id": str(grade_request.student_id),
        "assessment_id": str(grade_request.assessment_id) if grade_request.assessment_id else None,
        "graded_by": user_id,
        "criterion_scores": criterion_scores,
        "weighted_total": weighted_total,
        "max_weighted_total": max_weighted_total,
        "percentage": final_percentage,
        "overall_feedback": grade_request.overall_feedback
    }

    result = supabase.table("rubric_grades").insert(grade_data).execute()

    return {
        "success": True,
        "grade": {
            "id": result.data[0]["id"] if result.data else None,
            "weighted_total": round(weighted_total, 2),
            "max_weighted_total": round(max_weighted_total, 2),
            "percentage": round(final_percentage, 1),
            "criterion_scores": criterion_scores
        }
    }


@router.get("/{rubric_id}/grades/{student_id}")
async def get_student_rubric_grades(
    rubric_id: UUID,
    student_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get all rubric grades for a student"""
    result = supabase.table("rubric_grades").select(
        "*, rubrics(title)"
    ).eq("rubric_id", str(rubric_id)).eq(
        "student_id", str(student_id)
    ).order("created_at", desc=True).execute()

    return {"grades": result.data or []}


@router.get("/{rubric_id}/usage-stats")
async def get_rubric_usage_stats(
    rubric_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get statistics on rubric usage"""
    user_id = current_user["id"]

    # Check ownership
    rubric = supabase.table("rubrics").select(
        "teacher_id, criteria"
    ).eq("id", str(rubric_id)).single().execute()

    if not rubric.data:
        raise HTTPException(status_code=404, detail="Rubric not found")

    if rubric.data["teacher_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get all grades using this rubric
    grades = supabase.table("rubric_grades").select(
        "criterion_scores, percentage"
    ).eq("rubric_id", str(rubric_id)).execute()

    if not grades.data:
        return {
            "total_uses": 0,
            "average_percentage": 0,
            "criterion_averages": {}
        }

    # Calculate averages
    percentages = [g["percentage"] for g in grades.data]
    criteria = rubric.data.get("criteria", [])

    criterion_stats = {}
    for c in criteria:
        cid = c["id"]
        scores = []
        for g in grades.data:
            cs = g.get("criterion_scores", {})
            if cid in cs:
                scores.append(cs[cid]["score"])

        if scores:
            max_score = max(level["score"] for level in c["levels"])
            criterion_stats[cid] = {
                "name": c["name"],
                "average_score": round(sum(scores) / len(scores), 2),
                "max_score": max_score,
                "average_percentage": round(sum(scores) / len(scores) / max_score * 100, 1)
            }

    return {
        "total_uses": len(grades.data),
        "average_percentage": round(sum(percentages) / len(percentages), 1),
        "highest_percentage": max(percentages),
        "lowest_percentage": min(percentages),
        "criterion_averages": criterion_stats
    }
