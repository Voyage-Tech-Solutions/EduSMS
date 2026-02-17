"""
EduCore Backend - Staff Evaluations API
Teacher and staff performance evaluations
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

class EvaluationCriterion(BaseModel):
    """Evaluation criterion score"""
    criterion_id: str
    criterion_name: str
    score: int  # 1-5
    comments: Optional[str] = None


class EvaluationCreate(BaseModel):
    """Create a staff evaluation"""
    staff_id: UUID
    evaluation_type: str  # annual, mid_year, probation, special
    evaluation_period_start: date
    evaluation_period_end: date
    criteria_scores: List[EvaluationCriterion]
    overall_rating: int  # 1-5
    strengths: List[str] = []
    areas_for_improvement: List[str] = []
    goals_for_next_period: List[str] = []
    recommendations: Optional[str] = None
    employee_comments: Optional[str] = None


class EvaluationUpdate(BaseModel):
    """Update an evaluation"""
    criteria_scores: Optional[List[EvaluationCriterion]] = None
    overall_rating: Optional[int] = None
    strengths: Optional[List[str]] = None
    areas_for_improvement: Optional[List[str]] = None
    goals_for_next_period: Optional[List[str]] = None
    recommendations: Optional[str] = None
    status: Optional[str] = None  # draft, submitted, acknowledged, finalized


# ============================================================
# EVALUATION CRITERIA TEMPLATES
# ============================================================

TEACHER_EVALUATION_CRITERIA = [
    {"id": "instruction", "name": "Quality of Instruction", "weight": 1.5, "description": "Planning, delivery, and effectiveness of lessons"},
    {"id": "assessment", "name": "Assessment & Feedback", "weight": 1.0, "description": "Use of assessments and quality of feedback"},
    {"id": "classroom_mgmt", "name": "Classroom Management", "weight": 1.0, "description": "Creating a positive learning environment"},
    {"id": "student_relations", "name": "Student Relations", "weight": 1.0, "description": "Building rapport and supporting students"},
    {"id": "professionalism", "name": "Professionalism", "weight": 1.0, "description": "Reliability, ethics, and professional conduct"},
    {"id": "collaboration", "name": "Collaboration", "weight": 0.75, "description": "Working with colleagues, parents, and administration"},
    {"id": "growth", "name": "Professional Growth", "weight": 0.75, "description": "Commitment to continuous improvement"}
]

STAFF_EVALUATION_CRITERIA = [
    {"id": "job_knowledge", "name": "Job Knowledge", "weight": 1.0, "description": "Understanding of role and responsibilities"},
    {"id": "quality", "name": "Quality of Work", "weight": 1.5, "description": "Accuracy and thoroughness of work"},
    {"id": "productivity", "name": "Productivity", "weight": 1.0, "description": "Efficiency and output"},
    {"id": "reliability", "name": "Reliability", "weight": 1.0, "description": "Attendance, punctuality, and dependability"},
    {"id": "communication", "name": "Communication", "weight": 1.0, "description": "Written and verbal communication skills"},
    {"id": "teamwork", "name": "Teamwork", "weight": 1.0, "description": "Collaboration and interpersonal skills"},
    {"id": "initiative", "name": "Initiative", "weight": 0.75, "description": "Self-motivation and problem-solving"}
]


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/criteria")
async def get_evaluation_criteria(
    staff_type: str = "teacher",  # teacher, staff
    current_user: dict = Depends(get_current_user)
):
    """Get evaluation criteria templates"""
    if staff_type == "teacher":
        return {"criteria": TEACHER_EVALUATION_CRITERIA}
    return {"criteria": STAFF_EVALUATION_CRITERIA}


@router.get("")
async def list_evaluations(
    staff_id: Optional[UUID] = None,
    evaluation_type: Optional[str] = None,
    status: Optional[str] = None,
    academic_year_id: Optional[UUID] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List staff evaluations"""
    school_id = current_user.get("school_id")

    query = supabase.table("staff_evaluations").select(
        "*, staff:staff_id(first_name, last_name, position)"
    ).eq("school_id", school_id)

    if staff_id:
        query = query.eq("staff_id", str(staff_id))
    if evaluation_type:
        query = query.eq("evaluation_type", evaluation_type)
    if status:
        query = query.eq("status", status)
    if academic_year_id:
        query = query.eq("academic_year_id", str(academic_year_id))

    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

    result = query.execute()

    return {
        "evaluations": result.data or [],
        "total": len(result.data) if result.data else 0,
        "limit": limit,
        "offset": offset
    }


@router.get("/summary")
async def get_evaluations_summary(
    academic_year_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get evaluations summary statistics"""
    school_id = current_user.get("school_id")

    query = supabase.table("staff_evaluations").select(
        "overall_rating, status, evaluation_type"
    ).eq("school_id", school_id)

    if academic_year_id:
        query = query.eq("academic_year_id", str(academic_year_id))

    result = query.execute()

    evaluations = result.data or []

    summary = {
        "total_evaluations": len(evaluations),
        "by_status": {},
        "by_type": {},
        "by_rating": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
        "average_rating": 0
    }

    total_rating = 0
    for eval in evaluations:
        status = eval.get("status", "draft")
        summary["by_status"][status] = summary["by_status"].get(status, 0) + 1

        eval_type = eval.get("evaluation_type", "annual")
        summary["by_type"][eval_type] = summary["by_type"].get(eval_type, 0) + 1

        rating = eval.get("overall_rating", 0)
        if rating in summary["by_rating"]:
            summary["by_rating"][rating] += 1
        total_rating += rating

    summary["average_rating"] = round(total_rating / len(evaluations), 2) if evaluations else 0

    return summary


@router.get("/pending")
async def get_pending_evaluations(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get staff members pending evaluation"""
    school_id = current_user.get("school_id")

    # Get all active staff
    staff = supabase.table("teachers").select(
        "id, first_name, last_name, position, hire_date"
    ).eq("school_id", school_id).eq("is_active", True).execute()

    # Get recent evaluations
    recent_evals = supabase.table("staff_evaluations").select(
        "staff_id, created_at"
    ).eq("school_id", school_id).order("created_at", desc=True).execute()

    # Find last evaluation date for each staff
    last_eval = {}
    for eval in (recent_evals.data or []):
        if eval["staff_id"] not in last_eval:
            last_eval[eval["staff_id"]] = eval["created_at"]

    # Identify pending
    today = date.today()
    pending = []
    for s in (staff.data or []):
        last = last_eval.get(s["id"])
        months_since = 12  # Default to needing evaluation

        if last:
            last_date = datetime.fromisoformat(last.replace("Z", "")).date()
            months_since = (today.year - last_date.year) * 12 + today.month - last_date.month

        if months_since >= 12:  # Annual evaluation needed
            pending.append({
                "staff_id": s["id"],
                "name": f"{s['first_name']} {s['last_name']}",
                "position": s.get("position"),
                "last_evaluation": last,
                "months_since_evaluation": months_since
            })

    pending.sort(key=lambda x: x["months_since_evaluation"], reverse=True)

    return {"pending_evaluations": pending}


@router.get("/{evaluation_id}")
async def get_evaluation(
    evaluation_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get evaluation details"""
    result = supabase.table("staff_evaluations").select(
        "*, staff:staff_id(first_name, last_name, email, position), evaluator:evaluator_id(first_name, last_name)"
    ).eq("id", str(evaluation_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    return result.data


@router.post("")
async def create_evaluation(
    evaluation: EvaluationCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a staff evaluation"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    # Calculate weighted average
    total_weight = 0
    weighted_sum = 0
    for criterion in evaluation.criteria_scores:
        # Find weight from template
        weight = 1.0
        for tc in TEACHER_EVALUATION_CRITERIA + STAFF_EVALUATION_CRITERIA:
            if tc["id"] == criterion.criterion_id:
                weight = tc.get("weight", 1.0)
                break
        weighted_sum += criterion.score * weight
        total_weight += weight

    weighted_average = weighted_sum / total_weight if total_weight > 0 else 0

    eval_data = {
        "school_id": school_id,
        "staff_id": str(evaluation.staff_id),
        "evaluator_id": user_id,
        "evaluation_type": evaluation.evaluation_type,
        "evaluation_period_start": evaluation.evaluation_period_start.isoformat(),
        "evaluation_period_end": evaluation.evaluation_period_end.isoformat(),
        "criteria_scores": [c.dict() for c in evaluation.criteria_scores],
        "overall_rating": evaluation.overall_rating,
        "weighted_average": round(weighted_average, 2),
        "strengths": evaluation.strengths,
        "areas_for_improvement": evaluation.areas_for_improvement,
        "goals_for_next_period": evaluation.goals_for_next_period,
        "recommendations": evaluation.recommendations,
        "employee_comments": evaluation.employee_comments,
        "status": "draft"
    }

    result = supabase.table("staff_evaluations").insert(eval_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create evaluation")

    return result.data[0]


@router.put("/{evaluation_id}")
async def update_evaluation(
    evaluation_id: UUID,
    update: EvaluationUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update an evaluation"""
    existing = supabase.table("staff_evaluations").select("status").eq(
        "id", str(evaluation_id)
    ).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    if existing.data.get("status") == "finalized":
        raise HTTPException(status_code=400, detail="Cannot edit finalized evaluation")

    update_data = {}
    if update.criteria_scores is not None:
        update_data["criteria_scores"] = [c.dict() for c in update.criteria_scores]
    if update.overall_rating is not None:
        update_data["overall_rating"] = update.overall_rating
    if update.strengths is not None:
        update_data["strengths"] = update.strengths
    if update.areas_for_improvement is not None:
        update_data["areas_for_improvement"] = update.areas_for_improvement
    if update.goals_for_next_period is not None:
        update_data["goals_for_next_period"] = update.goals_for_next_period
    if update.recommendations is not None:
        update_data["recommendations"] = update.recommendations
    if update.status is not None:
        update_data["status"] = update.status

    result = supabase.table("staff_evaluations").update(update_data).eq(
        "id", str(evaluation_id)
    ).execute()

    return result.data[0] if result.data else None


@router.post("/{evaluation_id}/submit")
async def submit_evaluation(
    evaluation_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Submit evaluation for acknowledgment"""
    supabase.table("staff_evaluations").update({
        "status": "submitted",
        "submitted_at": datetime.utcnow().isoformat()
    }).eq("id", str(evaluation_id)).execute()

    return {"success": True, "status": "submitted"}


@router.post("/{evaluation_id}/acknowledge")
async def acknowledge_evaluation(
    evaluation_id: UUID,
    comments: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Staff member acknowledges evaluation"""
    update_data = {
        "status": "acknowledged",
        "acknowledged_at": datetime.utcnow().isoformat()
    }

    if comments:
        update_data["employee_comments"] = comments

    supabase.table("staff_evaluations").update(update_data).eq(
        "id", str(evaluation_id)
    ).execute()

    return {"success": True, "status": "acknowledged"}


@router.post("/{evaluation_id}/finalize")
async def finalize_evaluation(
    evaluation_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Finalize evaluation (no more edits)"""
    supabase.table("staff_evaluations").update({
        "status": "finalized",
        "finalized_at": datetime.utcnow().isoformat()
    }).eq("id", str(evaluation_id)).execute()

    return {"success": True, "status": "finalized"}


@router.delete("/{evaluation_id}")
async def delete_evaluation(
    evaluation_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a draft evaluation"""
    existing = supabase.table("staff_evaluations").select("status").eq(
        "id", str(evaluation_id)
    ).single().execute()

    if existing.data and existing.data.get("status") != "draft":
        raise HTTPException(status_code=400, detail="Can only delete draft evaluations")

    supabase.table("staff_evaluations").delete().eq("id", str(evaluation_id)).execute()

    return {"success": True}
