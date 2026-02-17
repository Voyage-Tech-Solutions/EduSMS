"""
EduCore Backend - Professional Development API
Track staff professional development activities and certifications
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

class PDActivityCreate(BaseModel):
    """Create a professional development activity"""
    staff_id: UUID
    title: str
    description: Optional[str] = None
    provider: Optional[str] = None
    category: str  # workshop, conference, course, certification, webinar, mentoring
    start_date: date
    end_date: Optional[date] = None
    hours: float
    credits: Optional[float] = None
    cost: Optional[float] = None
    paid_by_school: bool = False
    certificate_url: Optional[str] = None
    notes: Optional[str] = None


class PDActivityUpdate(BaseModel):
    """Update a PD activity"""
    title: Optional[str] = None
    description: Optional[str] = None
    provider: Optional[str] = None
    category: Optional[str] = None
    end_date: Optional[date] = None
    hours: Optional[float] = None
    credits: Optional[float] = None
    status: Optional[str] = None  # planned, in_progress, completed, cancelled
    certificate_url: Optional[str] = None
    notes: Optional[str] = None


class PDRequirementCreate(BaseModel):
    """Create a PD requirement"""
    name: str
    description: Optional[str] = None
    required_hours: float
    required_credits: Optional[float] = None
    categories: List[str] = []  # which categories count
    period_type: str = "annual"  # annual, biennial, certification_cycle
    applies_to: str = "all"  # all, teachers, staff, specific_roles
    role_ids: List[UUID] = []


class PDGoalCreate(BaseModel):
    """Create a PD goal for a staff member"""
    staff_id: UUID
    goal_type: str  # certification, skill, leadership, content_area
    title: str
    description: Optional[str] = None
    target_date: Optional[date] = None
    success_criteria: Optional[str] = None


# ============================================================
# PD ACTIVITY ENDPOINTS
# ============================================================

@router.get("")
async def list_pd_activities(
    staff_id: Optional[UUID] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    academic_year_id: Optional[UUID] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List professional development activities"""
    school_id = current_user.get("school_id")

    query = supabase.table("professional_development").select(
        "*, staff:staff_id(first_name, last_name, position)"
    ).eq("school_id", school_id)

    if staff_id:
        query = query.eq("staff_id", str(staff_id))
    if category:
        query = query.eq("category", category)
    if status:
        query = query.eq("status", status)
    if start_date:
        query = query.gte("start_date", start_date.isoformat())
    if end_date:
        query = query.lte("start_date", end_date.isoformat())
    if academic_year_id:
        query = query.eq("academic_year_id", str(academic_year_id))

    query = query.order("start_date", desc=True).range(offset, offset + limit - 1)

    result = query.execute()

    return {
        "activities": result.data or [],
        "total": len(result.data) if result.data else 0,
        "limit": limit,
        "offset": offset
    }


@router.get("/summary")
async def get_pd_summary(
    academic_year_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get PD summary statistics"""
    school_id = current_user.get("school_id")

    query = supabase.table("professional_development").select(
        "staff_id, category, hours, credits, cost, status, paid_by_school"
    ).eq("school_id", school_id).eq("status", "completed")

    if academic_year_id:
        query = query.eq("academic_year_id", str(academic_year_id))

    result = query.execute()

    activities = result.data or []

    summary = {
        "total_activities": len(activities),
        "total_hours": 0,
        "total_credits": 0,
        "total_cost": 0,
        "school_paid_cost": 0,
        "by_category": {},
        "staff_participation": {}
    }

    for act in activities:
        summary["total_hours"] += act.get("hours", 0) or 0
        summary["total_credits"] += act.get("credits", 0) or 0

        cost = act.get("cost", 0) or 0
        summary["total_cost"] += cost
        if act.get("paid_by_school"):
            summary["school_paid_cost"] += cost

        cat = act.get("category", "other")
        if cat not in summary["by_category"]:
            summary["by_category"][cat] = {"count": 0, "hours": 0}
        summary["by_category"][cat]["count"] += 1
        summary["by_category"][cat]["hours"] += act.get("hours", 0) or 0

        staff_id = act.get("staff_id")
        if staff_id not in summary["staff_participation"]:
            summary["staff_participation"][staff_id] = {"activities": 0, "hours": 0}
        summary["staff_participation"][staff_id]["activities"] += 1
        summary["staff_participation"][staff_id]["hours"] += act.get("hours", 0) or 0

    summary["unique_participants"] = len(summary["staff_participation"])

    return summary


@router.get("/staff/{staff_id}/progress")
async def get_staff_pd_progress(
    staff_id: UUID,
    academic_year_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get a staff member's PD progress against requirements"""
    school_id = current_user.get("school_id")

    # Get completed activities
    activities_query = supabase.table("professional_development").select(
        "category, hours, credits"
    ).eq("school_id", school_id).eq("staff_id", str(staff_id)).eq("status", "completed")

    if academic_year_id:
        activities_query = activities_query.eq("academic_year_id", str(academic_year_id))

    activities_result = activities_query.execute()
    activities = activities_result.data or []

    # Get requirements
    requirements_result = supabase.table("pd_requirements").select("*").eq(
        "school_id", school_id
    ).eq("is_active", True).execute()

    requirements = requirements_result.data or []

    # Calculate progress
    total_hours = sum(a.get("hours", 0) or 0 for a in activities)
    total_credits = sum(a.get("credits", 0) or 0 for a in activities)

    hours_by_category = {}
    for act in activities:
        cat = act.get("category", "other")
        hours_by_category[cat] = hours_by_category.get(cat, 0) + (act.get("hours", 0) or 0)

    progress = []
    for req in requirements:
        req_hours = req.get("required_hours", 0)
        categories = req.get("categories", [])

        if categories:
            earned_hours = sum(hours_by_category.get(c, 0) for c in categories)
        else:
            earned_hours = total_hours

        progress.append({
            "requirement_id": req["id"],
            "requirement_name": req["name"],
            "required_hours": req_hours,
            "earned_hours": earned_hours,
            "progress_percent": min(100, round((earned_hours / req_hours) * 100, 1)) if req_hours > 0 else 0,
            "completed": earned_hours >= req_hours
        })

    return {
        "staff_id": str(staff_id),
        "total_hours": total_hours,
        "total_credits": total_credits,
        "hours_by_category": hours_by_category,
        "activities_count": len(activities),
        "requirements_progress": progress
    }


@router.get("/{activity_id}")
async def get_pd_activity(
    activity_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get PD activity details"""
    result = supabase.table("professional_development").select(
        "*, staff:staff_id(first_name, last_name, email, position)"
    ).eq("id", str(activity_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Activity not found")

    return result.data


@router.post("")
async def create_pd_activity(
    activity: PDActivityCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a PD activity record"""
    school_id = current_user.get("school_id")

    activity_data = {
        "school_id": school_id,
        "staff_id": str(activity.staff_id),
        "title": activity.title,
        "description": activity.description,
        "provider": activity.provider,
        "category": activity.category,
        "start_date": activity.start_date.isoformat(),
        "end_date": activity.end_date.isoformat() if activity.end_date else None,
        "hours": activity.hours,
        "credits": activity.credits,
        "cost": activity.cost,
        "paid_by_school": activity.paid_by_school,
        "certificate_url": activity.certificate_url,
        "notes": activity.notes,
        "status": "completed" if activity.end_date and activity.end_date <= date.today() else "planned"
    }

    result = supabase.table("professional_development").insert(activity_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create activity")

    return result.data[0]


@router.put("/{activity_id}")
async def update_pd_activity(
    activity_id: UUID,
    update: PDActivityUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update a PD activity"""
    existing = supabase.table("professional_development").select("id").eq(
        "id", str(activity_id)
    ).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Activity not found")

    update_data = {}
    if update.title is not None:
        update_data["title"] = update.title
    if update.description is not None:
        update_data["description"] = update.description
    if update.provider is not None:
        update_data["provider"] = update.provider
    if update.category is not None:
        update_data["category"] = update.category
    if update.end_date is not None:
        update_data["end_date"] = update.end_date.isoformat()
    if update.hours is not None:
        update_data["hours"] = update.hours
    if update.credits is not None:
        update_data["credits"] = update.credits
    if update.status is not None:
        update_data["status"] = update.status
    if update.certificate_url is not None:
        update_data["certificate_url"] = update.certificate_url
    if update.notes is not None:
        update_data["notes"] = update.notes

    result = supabase.table("professional_development").update(update_data).eq(
        "id", str(activity_id)
    ).execute()

    return result.data[0] if result.data else None


@router.delete("/{activity_id}")
async def delete_pd_activity(
    activity_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a PD activity"""
    supabase.table("professional_development").delete().eq("id", str(activity_id)).execute()
    return {"success": True}


# ============================================================
# PD REQUIREMENTS ENDPOINTS
# ============================================================

@router.get("/requirements")
async def list_pd_requirements(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List PD requirements"""
    school_id = current_user.get("school_id")

    result = supabase.table("pd_requirements").select("*").eq(
        "school_id", school_id
    ).eq("is_active", True).execute()

    return {"requirements": result.data or []}


@router.post("/requirements")
async def create_pd_requirement(
    requirement: PDRequirementCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a PD requirement"""
    school_id = current_user.get("school_id")

    req_data = {
        "school_id": school_id,
        "name": requirement.name,
        "description": requirement.description,
        "required_hours": requirement.required_hours,
        "required_credits": requirement.required_credits,
        "categories": requirement.categories,
        "period_type": requirement.period_type,
        "applies_to": requirement.applies_to,
        "role_ids": [str(r) for r in requirement.role_ids],
        "is_active": True
    }

    result = supabase.table("pd_requirements").insert(req_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create requirement")

    return result.data[0]


@router.put("/requirements/{requirement_id}")
async def update_pd_requirement(
    requirement_id: UUID,
    update: dict,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update a PD requirement"""
    result = supabase.table("pd_requirements").update(update).eq(
        "id", str(requirement_id)
    ).execute()

    return result.data[0] if result.data else None


@router.delete("/requirements/{requirement_id}")
async def delete_pd_requirement(
    requirement_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Soft delete a PD requirement"""
    supabase.table("pd_requirements").update({
        "is_active": False
    }).eq("id", str(requirement_id)).execute()

    return {"success": True}


# ============================================================
# PD GOALS ENDPOINTS
# ============================================================

@router.get("/goals")
async def list_pd_goals(
    staff_id: Optional[UUID] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List PD goals"""
    school_id = current_user.get("school_id")

    query = supabase.table("pd_goals").select(
        "*, staff:staff_id(first_name, last_name)"
    ).eq("school_id", school_id)

    if staff_id:
        query = query.eq("staff_id", str(staff_id))
    if status:
        query = query.eq("status", status)

    result = query.order("created_at", desc=True).execute()

    return {"goals": result.data or []}


@router.post("/goals")
async def create_pd_goal(
    goal: PDGoalCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a PD goal for a staff member"""
    school_id = current_user.get("school_id")

    goal_data = {
        "school_id": school_id,
        "staff_id": str(goal.staff_id),
        "goal_type": goal.goal_type,
        "title": goal.title,
        "description": goal.description,
        "target_date": goal.target_date.isoformat() if goal.target_date else None,
        "success_criteria": goal.success_criteria,
        "status": "active"
    }

    result = supabase.table("pd_goals").insert(goal_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create goal")

    return result.data[0]


@router.put("/goals/{goal_id}")
async def update_pd_goal(
    goal_id: UUID,
    update: dict,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update a PD goal"""
    result = supabase.table("pd_goals").update(update).eq("id", str(goal_id)).execute()
    return result.data[0] if result.data else None


@router.post("/goals/{goal_id}/complete")
async def complete_pd_goal(
    goal_id: UUID,
    reflection: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Mark a PD goal as completed"""
    update_data = {
        "status": "completed",
        "completed_at": datetime.utcnow().isoformat()
    }

    if reflection:
        update_data["reflection"] = reflection

    supabase.table("pd_goals").update(update_data).eq("id", str(goal_id)).execute()

    return {"success": True, "status": "completed"}


# ============================================================
# UPCOMING/CALENDAR ENDPOINTS
# ============================================================

@router.get("/upcoming")
async def get_upcoming_pd(
    days: int = 30,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get upcoming PD activities"""
    school_id = current_user.get("school_id")
    today = date.today()
    future_date = date(today.year, today.month + (days // 30) + 1, min(today.day, 28))

    result = supabase.table("professional_development").select(
        "*, staff:staff_id(first_name, last_name)"
    ).eq("school_id", school_id).eq("status", "planned").gte(
        "start_date", today.isoformat()
    ).lte("start_date", future_date.isoformat()).order("start_date").execute()

    return {"upcoming": result.data or []}


@router.get("/expiring-certifications")
async def get_expiring_certifications(
    days: int = 90,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get certifications expiring soon"""
    school_id = current_user.get("school_id")
    today = date.today()
    future_date = date(today.year, today.month + (days // 30) + 1, min(today.day, 28))

    result = supabase.table("staff_certifications").select(
        "*, staff:staff_id(first_name, last_name, email)"
    ).eq("school_id", school_id).gte(
        "expiration_date", today.isoformat()
    ).lte("expiration_date", future_date.isoformat()).order("expiration_date").execute()

    return {"expiring": result.data or []}
