"""
EduCore Backend - Student Interventions API
Track academic and behavioral interventions
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

class InterventionProgress(BaseModel):
    """Progress note for an intervention"""
    date: str
    note: str
    progress_rating: Optional[int] = None  # 1-5 scale
    recorded_by: Optional[str] = None


class InterventionCreate(BaseModel):
    """Create an intervention"""
    student_id: UUID
    intervention_type: str  # academic, behavioral, attendance, social_emotional
    tier: int = 1  # RTI Tier: 1, 2, or 3
    area_of_concern: str
    goal: str
    strategy: str
    frequency: str  # daily, weekly, bi_weekly, as_needed
    duration_weeks: int = 6
    start_date: date
    end_date: Optional[date] = None
    responsible_staff: List[UUID] = []
    parent_notified: bool = False
    baseline_data: Optional[str] = None
    success_criteria: Optional[str] = None


class InterventionUpdate(BaseModel):
    """Update an intervention"""
    area_of_concern: Optional[str] = None
    goal: Optional[str] = None
    strategy: Optional[str] = None
    frequency: Optional[str] = None
    end_date: Optional[date] = None
    status: Optional[str] = None  # active, completed, discontinued, escalated
    outcome: Optional[str] = None
    outcome_notes: Optional[str] = None


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("")
async def list_interventions(
    student_id: Optional[UUID] = None,
    class_id: Optional[UUID] = None,
    intervention_type: Optional[str] = None,
    tier: Optional[int] = None,
    status: Optional[str] = None,
    staff_id: Optional[UUID] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List interventions with filters"""
    school_id = current_user.get("school_id")

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    query = supabase.table("student_interventions").select(
        "*, students(first_name, last_name, student_number, class_id)"
    ).eq("school_id", school_id)

    if student_id:
        query = query.eq("student_id", str(student_id))
    if intervention_type:
        query = query.eq("intervention_type", intervention_type)
    if tier:
        query = query.eq("tier", tier)
    if status:
        query = query.eq("status", status)
    else:
        # Default to active interventions
        query = query.eq("status", "active")
    if staff_id:
        query = query.contains("responsible_staff", [str(staff_id)])

    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

    result = query.execute()

    interventions = result.data or []

    # Filter by class if needed
    if class_id:
        interventions = [
            i for i in interventions
            if i.get("students", {}).get("class_id") == str(class_id)
        ]

    return {
        "interventions": interventions,
        "total": len(interventions),
        "limit": limit,
        "offset": offset
    }


@router.get("/student/{student_id}")
async def get_student_interventions(
    student_id: UUID,
    include_completed: bool = False,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get all interventions for a specific student"""
    query = supabase.table("student_interventions").select(
        "*"
    ).eq("student_id", str(student_id))

    if not include_completed:
        query = query.eq("status", "active")

    query = query.order("start_date", desc=True)

    result = query.execute()

    # Group by type
    interventions_by_type = {
        "academic": [],
        "behavioral": [],
        "attendance": [],
        "social_emotional": []
    }

    for intervention in (result.data or []):
        itype = intervention.get("intervention_type", "academic")
        if itype in interventions_by_type:
            interventions_by_type[itype].append(intervention)

    return {
        "student_id": str(student_id),
        "active_count": len([i for i in (result.data or []) if i.get("status") == "active"]),
        "interventions_by_type": interventions_by_type,
        "all_interventions": result.data or []
    }


@router.get("/{intervention_id}")
async def get_intervention(
    intervention_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get a specific intervention with progress history"""
    result = supabase.table("student_interventions").select(
        "*, students(first_name, last_name, student_number)"
    ).eq("id", str(intervention_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Intervention not found")

    return result.data


@router.post("")
async def create_intervention(
    intervention: InterventionCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a new intervention"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    # Calculate end date if not provided
    end_date = intervention.end_date
    if not end_date:
        from datetime import timedelta
        end_date = intervention.start_date + timedelta(weeks=intervention.duration_weeks)

    intervention_data = {
        "school_id": school_id,
        "student_id": str(intervention.student_id),
        "created_by": user_id,
        "intervention_type": intervention.intervention_type,
        "tier": intervention.tier,
        "area_of_concern": intervention.area_of_concern,
        "goal": intervention.goal,
        "strategy": intervention.strategy,
        "frequency": intervention.frequency,
        "duration_weeks": intervention.duration_weeks,
        "start_date": intervention.start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "responsible_staff": [str(s) for s in intervention.responsible_staff],
        "parent_notified": intervention.parent_notified,
        "baseline_data": intervention.baseline_data,
        "success_criteria": intervention.success_criteria,
        "progress_notes": [],
        "status": "active"
    }

    result = supabase.table("student_interventions").insert(intervention_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create intervention")

    return result.data[0]


@router.put("/{intervention_id}")
async def update_intervention(
    intervention_id: UUID,
    update: InterventionUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update an intervention"""
    existing = supabase.table("student_interventions").select("id").eq(
        "id", str(intervention_id)
    ).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Intervention not found")

    update_data = {}
    if update.area_of_concern is not None:
        update_data["area_of_concern"] = update.area_of_concern
    if update.goal is not None:
        update_data["goal"] = update.goal
    if update.strategy is not None:
        update_data["strategy"] = update.strategy
    if update.frequency is not None:
        update_data["frequency"] = update.frequency
    if update.end_date is not None:
        update_data["end_date"] = update.end_date.isoformat()
    if update.status is not None:
        update_data["status"] = update.status
    if update.outcome is not None:
        update_data["outcome"] = update.outcome
    if update.outcome_notes is not None:
        update_data["outcome_notes"] = update.outcome_notes

    result = supabase.table("student_interventions").update(update_data).eq(
        "id", str(intervention_id)
    ).execute()

    return result.data[0] if result.data else None


@router.post("/{intervention_id}/progress")
async def add_progress_note(
    intervention_id: UUID,
    progress: InterventionProgress,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Add a progress note to an intervention"""
    user_id = current_user["id"]

    intervention = supabase.table("student_interventions").select(
        "progress_notes"
    ).eq("id", str(intervention_id)).single().execute()

    if not intervention.data:
        raise HTTPException(status_code=404, detail="Intervention not found")

    notes = intervention.data.get("progress_notes") or []
    progress_dict = progress.dict()
    progress_dict["recorded_by"] = user_id
    progress_dict["recorded_at"] = datetime.utcnow().isoformat()
    notes.append(progress_dict)

    supabase.table("student_interventions").update({
        "progress_notes": notes
    }).eq("id", str(intervention_id)).execute()

    return {"success": True, "note": progress_dict}


@router.post("/{intervention_id}/complete")
async def complete_intervention(
    intervention_id: UUID,
    outcome: str,  # successful, partially_successful, unsuccessful
    outcome_notes: Optional[str] = None,
    recommend_escalation: bool = False,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Mark an intervention as complete"""
    intervention = supabase.table("student_interventions").select(
        "id, status"
    ).eq("id", str(intervention_id)).single().execute()

    if not intervention.data:
        raise HTTPException(status_code=404, detail="Intervention not found")

    if intervention.data.get("status") != "active":
        raise HTTPException(status_code=400, detail="Intervention is not active")

    status = "escalated" if recommend_escalation else "completed"

    supabase.table("student_interventions").update({
        "status": status,
        "outcome": outcome,
        "outcome_notes": outcome_notes,
        "completed_at": datetime.utcnow().isoformat()
    }).eq("id", str(intervention_id)).execute()

    return {"success": True, "status": status, "outcome": outcome}


@router.get("/stats/summary")
async def get_intervention_stats(
    class_id: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get intervention statistics"""
    school_id = current_user.get("school_id")

    query = supabase.table("student_interventions").select(
        "intervention_type, tier, status, outcome, student_id, students(class_id)"
    ).eq("school_id", school_id)

    if date_from:
        query = query.gte("start_date", date_from.isoformat())
    if date_to:
        query = query.lte("start_date", date_to.isoformat())

    result = query.execute()

    interventions = result.data or []

    # Filter by class if needed
    if class_id:
        interventions = [
            i for i in interventions
            if i.get("students", {}).get("class_id") == str(class_id)
        ]

    # Calculate stats
    stats = {
        "total_interventions": len(interventions),
        "active_interventions": len([i for i in interventions if i.get("status") == "active"]),
        "by_type": {},
        "by_tier": {1: 0, 2: 0, 3: 0},
        "by_status": {},
        "outcomes": {},
        "unique_students": len(set(i.get("student_id") for i in interventions))
    }

    for intervention in interventions:
        itype = intervention.get("intervention_type", "other")
        tier = intervention.get("tier", 1)
        status = intervention.get("status", "active")
        outcome = intervention.get("outcome")

        stats["by_type"][itype] = stats["by_type"].get(itype, 0) + 1
        if tier in stats["by_tier"]:
            stats["by_tier"][tier] += 1
        stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
        if outcome:
            stats["outcomes"][outcome] = stats["outcomes"].get(outcome, 0) + 1

    # Success rate
    completed = stats["by_status"].get("completed", 0)
    successful = stats["outcomes"].get("successful", 0)
    stats["success_rate"] = round(successful / completed * 100, 1) if completed > 0 else 0

    return stats
