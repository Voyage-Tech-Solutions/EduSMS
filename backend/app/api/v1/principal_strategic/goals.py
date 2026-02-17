"""
EduCore Backend - School Goals API
Strategic goal setting and tracking
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

class MilestoneCreate(BaseModel):
    """Goal milestone"""
    title: str
    description: Optional[str] = None
    target_date: date
    is_completed: bool = False


class GoalCreate(BaseModel):
    """Create a school goal"""
    title: str
    description: Optional[str] = None
    category: str  # academic, financial, enrollment, culture, infrastructure, other
    priority: str = "medium"  # high, medium, low
    academic_year_id: Optional[UUID] = None
    start_date: date
    target_date: date
    success_criteria: Optional[str] = None
    metrics: Optional[List[dict]] = None  # [{name, target_value, current_value, unit}]
    milestones: List[MilestoneCreate] = []
    assigned_to: Optional[List[UUID]] = None
    is_public: bool = False


class GoalUpdate(BaseModel):
    """Update a school goal"""
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    target_date: Optional[date] = None
    success_criteria: Optional[str] = None
    metrics: Optional[List[dict]] = None
    status: Optional[str] = None  # not_started, in_progress, on_track, at_risk, completed, cancelled
    progress_percentage: Optional[int] = None
    notes: Optional[str] = None


class ProgressUpdate(BaseModel):
    """Update goal progress"""
    progress_percentage: int
    notes: Optional[str] = None
    metric_updates: Optional[List[dict]] = None


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("")
async def list_goals(
    academic_year_id: Optional[UUID] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List school goals"""
    school_id = current_user.get("school_id")

    query = supabase.table("school_goals").select(
        "*, academic_years(name)"
    ).eq("school_id", school_id)

    if academic_year_id:
        query = query.eq("academic_year_id", str(academic_year_id))
    if category:
        query = query.eq("category", category)
    if status:
        query = query.eq("status", status)
    if priority:
        query = query.eq("priority", priority)

    query = query.order("priority").order("target_date")

    result = query.execute()

    return {"goals": result.data or []}


@router.get("/dashboard")
async def get_goals_dashboard(
    academic_year_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get goals dashboard summary"""
    school_id = current_user.get("school_id")

    query = supabase.table("school_goals").select(
        "id, title, category, status, priority, progress_percentage, target_date"
    ).eq("school_id", school_id)

    if academic_year_id:
        query = query.eq("academic_year_id", str(academic_year_id))

    result = query.execute()

    goals = result.data or []

    # Calculate summary
    summary = {
        "total": len(goals),
        "by_status": {},
        "by_category": {},
        "by_priority": {},
        "average_progress": 0,
        "on_track": 0,
        "at_risk": 0,
        "overdue": 0
    }

    today = date.today()
    total_progress = 0

    for goal in goals:
        # By status
        status = goal.get("status", "not_started")
        summary["by_status"][status] = summary["by_status"].get(status, 0) + 1

        # By category
        category = goal.get("category", "other")
        summary["by_category"][category] = summary["by_category"].get(category, 0) + 1

        # By priority
        priority = goal.get("priority", "medium")
        summary["by_priority"][priority] = summary["by_priority"].get(priority, 0) + 1

        # Progress
        total_progress += goal.get("progress_percentage") or 0

        # On track/at risk
        if status == "on_track":
            summary["on_track"] += 1
        elif status == "at_risk":
            summary["at_risk"] += 1

        # Overdue
        target = goal.get("target_date")
        if target and status not in ["completed", "cancelled"]:
            if date.fromisoformat(target) < today:
                summary["overdue"] += 1

    summary["average_progress"] = round(total_progress / len(goals), 1) if goals else 0

    return {
        "summary": summary,
        "recent_goals": goals[:5]
    }


@router.get("/{goal_id}")
async def get_goal(
    goal_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get goal with full details"""
    result = supabase.table("school_goals").select(
        "*, academic_years(name)"
    ).eq("id", str(goal_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Goal not found")

    goal = result.data

    # Get progress history
    history = supabase.table("goal_progress_history").select(
        "progress_percentage, notes, updated_at, user_profiles(first_name, last_name)"
    ).eq("goal_id", str(goal_id)).order("updated_at", desc=True).limit(10).execute()

    goal["progress_history"] = history.data or []

    return goal


@router.post("")
async def create_goal(
    goal: GoalCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a school goal"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    goal_data = {
        "school_id": school_id,
        "created_by": user_id,
        "title": goal.title,
        "description": goal.description,
        "category": goal.category,
        "priority": goal.priority,
        "academic_year_id": str(goal.academic_year_id) if goal.academic_year_id else None,
        "start_date": goal.start_date.isoformat(),
        "target_date": goal.target_date.isoformat(),
        "success_criteria": goal.success_criteria,
        "metrics": goal.metrics,
        "milestones": [m.dict() for m in goal.milestones],
        "assigned_to": [str(a) for a in goal.assigned_to] if goal.assigned_to else None,
        "is_public": goal.is_public,
        "status": "not_started",
        "progress_percentage": 0
    }

    result = supabase.table("school_goals").insert(goal_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create goal")

    return result.data[0]


@router.put("/{goal_id}")
async def update_goal(
    goal_id: UUID,
    update: GoalUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update a school goal"""
    existing = supabase.table("school_goals").select("id").eq(
        "id", str(goal_id)
    ).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Goal not found")

    update_data = {}
    if update.title is not None:
        update_data["title"] = update.title
    if update.description is not None:
        update_data["description"] = update.description
    if update.category is not None:
        update_data["category"] = update.category
    if update.priority is not None:
        update_data["priority"] = update.priority
    if update.target_date is not None:
        update_data["target_date"] = update.target_date.isoformat()
    if update.success_criteria is not None:
        update_data["success_criteria"] = update.success_criteria
    if update.metrics is not None:
        update_data["metrics"] = update.metrics
    if update.status is not None:
        update_data["status"] = update.status
    if update.progress_percentage is not None:
        update_data["progress_percentage"] = update.progress_percentage
    if update.notes is not None:
        update_data["notes"] = update.notes

    result = supabase.table("school_goals").update(update_data).eq(
        "id", str(goal_id)
    ).execute()

    return result.data[0] if result.data else None


@router.post("/{goal_id}/progress")
async def update_progress(
    goal_id: UUID,
    progress: ProgressUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update goal progress"""
    user_id = current_user["id"]

    goal = supabase.table("school_goals").select(
        "progress_percentage, metrics"
    ).eq("id", str(goal_id)).single().execute()

    if not goal.data:
        raise HTTPException(status_code=404, detail="Goal not found")

    # Record history
    history_data = {
        "goal_id": str(goal_id),
        "progress_percentage": progress.progress_percentage,
        "notes": progress.notes,
        "updated_by": user_id,
        "updated_at": datetime.utcnow().isoformat()
    }
    supabase.table("goal_progress_history").insert(history_data).execute()

    # Update goal
    update_data = {
        "progress_percentage": progress.progress_percentage
    }

    # Update metrics if provided
    if progress.metric_updates and goal.data.get("metrics"):
        metrics = goal.data["metrics"]
        for metric_update in progress.metric_updates:
            for metric in metrics:
                if metric.get("name") == metric_update.get("name"):
                    metric["current_value"] = metric_update.get("current_value")
        update_data["metrics"] = metrics

    # Auto-update status
    if progress.progress_percentage >= 100:
        update_data["status"] = "completed"
    elif progress.progress_percentage > 0:
        update_data["status"] = "in_progress"

    supabase.table("school_goals").update(update_data).eq("id", str(goal_id)).execute()

    return {"success": True, "progress_percentage": progress.progress_percentage}


@router.post("/{goal_id}/milestone/{milestone_index}/complete")
async def complete_milestone(
    goal_id: UUID,
    milestone_index: int,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Mark a milestone as complete"""
    goal = supabase.table("school_goals").select("milestones").eq(
        "id", str(goal_id)
    ).single().execute()

    if not goal.data:
        raise HTTPException(status_code=404, detail="Goal not found")

    milestones = goal.data.get("milestones") or []
    if milestone_index >= len(milestones):
        raise HTTPException(status_code=404, detail="Milestone not found")

    milestones[milestone_index]["is_completed"] = True
    milestones[milestone_index]["completed_at"] = datetime.utcnow().isoformat()

    supabase.table("school_goals").update({
        "milestones": milestones
    }).eq("id", str(goal_id)).execute()

    return {"success": True}


@router.delete("/{goal_id}")
async def delete_goal(
    goal_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a school goal"""
    supabase.table("school_goals").delete().eq("id", str(goal_id)).execute()
    return {"success": True}
