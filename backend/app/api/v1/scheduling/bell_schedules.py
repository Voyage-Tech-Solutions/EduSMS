"""
EduCore Backend - Bell Schedules API
Manage school bell schedules and periods
"""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import time

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# MODELS
# ============================================================

class PeriodDefinition(BaseModel):
    """Definition of a single period"""
    period_number: int
    name: str
    start_time: str  # HH:MM format
    end_time: str
    period_type: str = "class"  # class, break, lunch, assembly, homeroom


class BellScheduleCreate(BaseModel):
    """Create a bell schedule"""
    name: str
    description: Optional[str] = None
    schedule_type: str = "regular"  # regular, half_day, exam, special
    applies_to_days: List[int] = [1, 2, 3, 4, 5]  # Days of week (1=Monday)
    periods: List[PeriodDefinition] = []
    is_default: bool = False


class BellScheduleUpdate(BaseModel):
    """Update a bell schedule"""
    name: Optional[str] = None
    description: Optional[str] = None
    schedule_type: Optional[str] = None
    applies_to_days: Optional[List[int]] = None
    periods: Optional[List[PeriodDefinition]] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


# ============================================================
# DEFAULT SCHEDULES
# ============================================================

DEFAULT_REGULAR_SCHEDULE = {
    "name": "Regular Day Schedule",
    "schedule_type": "regular",
    "applies_to_days": [1, 2, 3, 4, 5],
    "periods": [
        {"period_number": 0, "name": "Homeroom", "start_time": "08:00", "end_time": "08:15", "period_type": "homeroom"},
        {"period_number": 1, "name": "Period 1", "start_time": "08:15", "end_time": "09:00", "period_type": "class"},
        {"period_number": 2, "name": "Period 2", "start_time": "09:05", "end_time": "09:50", "period_type": "class"},
        {"period_number": 3, "name": "Period 3", "start_time": "09:55", "end_time": "10:40", "period_type": "class"},
        {"period_number": -1, "name": "Break", "start_time": "10:40", "end_time": "11:00", "period_type": "break"},
        {"period_number": 4, "name": "Period 4", "start_time": "11:00", "end_time": "11:45", "period_type": "class"},
        {"period_number": 5, "name": "Period 5", "start_time": "11:50", "end_time": "12:35", "period_type": "class"},
        {"period_number": -2, "name": "Lunch", "start_time": "12:35", "end_time": "13:15", "period_type": "lunch"},
        {"period_number": 6, "name": "Period 6", "start_time": "13:15", "end_time": "14:00", "period_type": "class"},
        {"period_number": 7, "name": "Period 7", "start_time": "14:05", "end_time": "14:50", "period_type": "class"},
        {"period_number": 8, "name": "Period 8", "start_time": "14:55", "end_time": "15:40", "period_type": "class"}
    ]
}

DEFAULT_HALF_DAY_SCHEDULE = {
    "name": "Half Day Schedule",
    "schedule_type": "half_day",
    "applies_to_days": [],
    "periods": [
        {"period_number": 0, "name": "Homeroom", "start_time": "08:00", "end_time": "08:10", "period_type": "homeroom"},
        {"period_number": 1, "name": "Period 1", "start_time": "08:10", "end_time": "08:40", "period_type": "class"},
        {"period_number": 2, "name": "Period 2", "start_time": "08:45", "end_time": "09:15", "period_type": "class"},
        {"period_number": 3, "name": "Period 3", "start_time": "09:20", "end_time": "09:50", "period_type": "class"},
        {"period_number": 4, "name": "Period 4", "start_time": "09:55", "end_time": "10:25", "period_type": "class"},
        {"period_number": -1, "name": "Break", "start_time": "10:25", "end_time": "10:40", "period_type": "break"},
        {"period_number": 5, "name": "Period 5", "start_time": "10:40", "end_time": "11:10", "period_type": "class"},
        {"period_number": 6, "name": "Period 6", "start_time": "11:15", "end_time": "11:45", "period_type": "class"},
        {"period_number": 7, "name": "Period 7", "start_time": "11:50", "end_time": "12:20", "period_type": "class"},
        {"period_number": 8, "name": "Period 8", "start_time": "12:25", "end_time": "12:55", "period_type": "class"}
    ]
}


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("")
async def list_bell_schedules(
    schedule_type: Optional[str] = None,
    active_only: bool = True,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List bell schedules"""
    school_id = current_user.get("school_id")

    query = supabase.table("bell_schedules").select("*").eq("school_id", school_id)

    if schedule_type:
        query = query.eq("schedule_type", schedule_type)
    if active_only:
        query = query.eq("is_active", True)

    query = query.order("is_default", desc=True).order("name")

    result = query.execute()

    return {"schedules": result.data or []}


@router.get("/current")
async def get_current_schedule(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get the current active schedule for today"""
    school_id = current_user.get("school_id")
    from datetime import datetime
    today_dow = datetime.now().isoweekday()

    # Check for special schedule override
    override = supabase.table("schedule_overrides").select(
        "bell_schedule_id"
    ).eq("school_id", school_id).eq(
        "override_date", datetime.now().date().isoformat()
    ).single().execute()

    if override.data:
        result = supabase.table("bell_schedules").select("*").eq(
            "id", override.data["bell_schedule_id"]
        ).single().execute()
        if result.data:
            result.data["is_override"] = True
            return result.data

    # Get schedule that applies to today
    result = supabase.table("bell_schedules").select("*").eq(
        "school_id", school_id
    ).eq("is_active", True).contains("applies_to_days", [today_dow]).execute()

    if result.data:
        return result.data[0]

    # Fall back to default schedule
    default = supabase.table("bell_schedules").select("*").eq(
        "school_id", school_id
    ).eq("is_default", True).single().execute()

    return default.data


@router.get("/current-period")
async def get_current_period(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get the current period based on time"""
    schedule = await get_current_schedule(current_user, supabase)

    if not schedule:
        return {"current_period": None, "message": "No schedule configured"}

    from datetime import datetime
    now = datetime.now().strftime("%H:%M")

    periods = schedule.get("periods", [])
    current_period = None
    next_period = None

    for i, period in enumerate(periods):
        if period["start_time"] <= now <= period["end_time"]:
            current_period = period
            if i + 1 < len(periods):
                next_period = periods[i + 1]
            break
        elif period["start_time"] > now and next_period is None:
            next_period = period

    return {
        "current_time": now,
        "current_period": current_period,
        "next_period": next_period,
        "schedule_name": schedule.get("name")
    }


@router.get("/{schedule_id}")
async def get_bell_schedule(
    schedule_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get a specific bell schedule"""
    result = supabase.table("bell_schedules").select("*").eq(
        "id", str(schedule_id)
    ).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Schedule not found")

    return result.data


@router.post("")
async def create_bell_schedule(
    schedule: BellScheduleCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a new bell schedule"""
    school_id = current_user.get("school_id")

    # If setting as default, unset other defaults
    if schedule.is_default:
        supabase.table("bell_schedules").update({
            "is_default": False
        }).eq("school_id", school_id).execute()

    schedule_data = {
        "school_id": school_id,
        "name": schedule.name,
        "description": schedule.description,
        "schedule_type": schedule.schedule_type,
        "applies_to_days": schedule.applies_to_days,
        "periods": [p.dict() for p in schedule.periods],
        "is_default": schedule.is_default,
        "is_active": True
    }

    result = supabase.table("bell_schedules").insert(schedule_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create schedule")

    return result.data[0]


@router.post("/from-default/{template}")
async def create_from_default(
    template: str,  # regular, half_day
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a schedule from default templates"""
    school_id = current_user.get("school_id")

    if template == "regular":
        template_data = DEFAULT_REGULAR_SCHEDULE
    elif template == "half_day":
        template_data = DEFAULT_HALF_DAY_SCHEDULE
    else:
        raise HTTPException(status_code=400, detail="Invalid template")

    schedule_data = {
        "school_id": school_id,
        "name": template_data["name"],
        "schedule_type": template_data["schedule_type"],
        "applies_to_days": template_data["applies_to_days"],
        "periods": template_data["periods"],
        "is_default": template == "regular",
        "is_active": True
    }

    result = supabase.table("bell_schedules").insert(schedule_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create schedule")

    return result.data[0]


@router.put("/{schedule_id}")
async def update_bell_schedule(
    schedule_id: UUID,
    update: BellScheduleUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update a bell schedule"""
    school_id = current_user.get("school_id")

    existing = supabase.table("bell_schedules").select("id").eq(
        "id", str(schedule_id)
    ).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Schedule not found")

    # If setting as default, unset other defaults
    if update.is_default:
        supabase.table("bell_schedules").update({
            "is_default": False
        }).eq("school_id", school_id).execute()

    update_data = {}
    if update.name is not None:
        update_data["name"] = update.name
    if update.description is not None:
        update_data["description"] = update.description
    if update.schedule_type is not None:
        update_data["schedule_type"] = update.schedule_type
    if update.applies_to_days is not None:
        update_data["applies_to_days"] = update.applies_to_days
    if update.periods is not None:
        update_data["periods"] = [p.dict() for p in update.periods]
    if update.is_default is not None:
        update_data["is_default"] = update.is_default
    if update.is_active is not None:
        update_data["is_active"] = update.is_active

    result = supabase.table("bell_schedules").update(update_data).eq(
        "id", str(schedule_id)
    ).execute()

    return result.data[0] if result.data else None


@router.delete("/{schedule_id}")
async def delete_bell_schedule(
    schedule_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a bell schedule"""
    supabase.table("bell_schedules").update({
        "is_active": False
    }).eq("id", str(schedule_id)).execute()

    return {"success": True}


@router.post("/{schedule_id}/set-default")
async def set_default_schedule(
    schedule_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Set a schedule as the default"""
    school_id = current_user.get("school_id")

    # Unset all defaults
    supabase.table("bell_schedules").update({
        "is_default": False
    }).eq("school_id", school_id).execute()

    # Set new default
    supabase.table("bell_schedules").update({
        "is_default": True
    }).eq("id", str(schedule_id)).execute()

    return {"success": True}
