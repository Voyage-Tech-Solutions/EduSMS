"""
EduCore Backend - Rooms Management API
Manage classrooms and facilities
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

class RoomCreate(BaseModel):
    """Create a room"""
    name: str
    room_number: str
    building: Optional[str] = None
    floor: Optional[int] = None
    room_type: str = "classroom"  # classroom, lab, library, auditorium, gym, office, other
    capacity: int = 30
    facilities: List[str] = []  # projector, whiteboard, computers, ac, etc.
    is_bookable: bool = True
    notes: Optional[str] = None


class RoomUpdate(BaseModel):
    """Update a room"""
    name: Optional[str] = None
    room_number: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[int] = None
    room_type: Optional[str] = None
    capacity: Optional[int] = None
    facilities: Optional[List[str]] = None
    is_bookable: Optional[bool] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("")
async def list_rooms(
    room_type: Optional[str] = None,
    building: Optional[str] = None,
    min_capacity: Optional[int] = None,
    is_bookable: Optional[bool] = None,
    facility: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List rooms with filters"""
    school_id = current_user.get("school_id")

    query = supabase.table("rooms").select("*").eq("school_id", school_id).eq("is_active", True)

    if room_type:
        query = query.eq("room_type", room_type)
    if building:
        query = query.eq("building", building)
    if min_capacity:
        query = query.gte("capacity", min_capacity)
    if is_bookable is not None:
        query = query.eq("is_bookable", is_bookable)
    if facility:
        query = query.contains("facilities", [facility])
    if search:
        query = query.or_(f"name.ilike.%{search}%,room_number.ilike.%{search}%")

    query = query.order("building").order("floor").order("room_number")

    result = query.execute()

    return {"rooms": result.data or []}


@router.get("/buildings")
async def get_buildings(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get list of buildings"""
    school_id = current_user.get("school_id")

    result = supabase.table("rooms").select("building").eq(
        "school_id", school_id
    ).eq("is_active", True).execute()

    buildings = list(set(r.get("building") for r in (result.data or []) if r.get("building")))

    return {"buildings": sorted(buildings)}


@router.get("/types")
async def get_room_types(
    current_user: dict = Depends(get_current_user)
):
    """Get available room types"""
    return {
        "types": [
            {"id": "classroom", "name": "Classroom"},
            {"id": "lab", "name": "Laboratory"},
            {"id": "computer_lab", "name": "Computer Lab"},
            {"id": "library", "name": "Library"},
            {"id": "auditorium", "name": "Auditorium"},
            {"id": "gym", "name": "Gymnasium"},
            {"id": "cafeteria", "name": "Cafeteria"},
            {"id": "office", "name": "Office"},
            {"id": "meeting_room", "name": "Meeting Room"},
            {"id": "storage", "name": "Storage"},
            {"id": "other", "name": "Other"}
        ]
    }


@router.get("/{room_id}")
async def get_room(
    room_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get room details"""
    result = supabase.table("rooms").select("*").eq(
        "id", str(room_id)
    ).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Room not found")

    return result.data


@router.post("")
async def create_room(
    room: RoomCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a new room"""
    school_id = current_user.get("school_id")

    # Check for duplicate room number
    existing = supabase.table("rooms").select("id").eq(
        "school_id", school_id
    ).eq("room_number", room.room_number).execute()

    if existing.data:
        raise HTTPException(status_code=400, detail="Room number already exists")

    room_data = {
        "school_id": school_id,
        "name": room.name,
        "room_number": room.room_number,
        "building": room.building,
        "floor": room.floor,
        "room_type": room.room_type,
        "capacity": room.capacity,
        "facilities": room.facilities,
        "is_bookable": room.is_bookable,
        "notes": room.notes,
        "is_active": True
    }

    result = supabase.table("rooms").insert(room_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create room")

    return result.data[0]


@router.put("/{room_id}")
async def update_room(
    room_id: UUID,
    update: RoomUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update a room"""
    existing = supabase.table("rooms").select("id").eq(
        "id", str(room_id)
    ).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Room not found")

    update_data = {}
    if update.name is not None:
        update_data["name"] = update.name
    if update.room_number is not None:
        update_data["room_number"] = update.room_number
    if update.building is not None:
        update_data["building"] = update.building
    if update.floor is not None:
        update_data["floor"] = update.floor
    if update.room_type is not None:
        update_data["room_type"] = update.room_type
    if update.capacity is not None:
        update_data["capacity"] = update.capacity
    if update.facilities is not None:
        update_data["facilities"] = update.facilities
    if update.is_bookable is not None:
        update_data["is_bookable"] = update.is_bookable
    if update.is_active is not None:
        update_data["is_active"] = update.is_active
    if update.notes is not None:
        update_data["notes"] = update.notes

    result = supabase.table("rooms").update(update_data).eq("id", str(room_id)).execute()

    return result.data[0] if result.data else None


@router.delete("/{room_id}")
async def delete_room(
    room_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a room (soft delete)"""
    supabase.table("rooms").update({
        "is_active": False
    }).eq("id", str(room_id)).execute()

    return {"success": True}


@router.get("/{room_id}/schedule")
async def get_room_schedule(
    room_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get schedule for a room"""
    # Get timetable entries for this room
    result = supabase.table("timetable_entries").select(
        "*, subjects(name), classes(name), teachers:teacher_id(first_name, last_name)"
    ).eq("room_id", str(room_id)).order("day_of_week").order("period").execute()

    # Group by day
    schedule = {i: [] for i in range(7)}  # 0-6 for days
    for entry in (result.data or []):
        day = entry.get("day_of_week", 0)
        if day in schedule:
            schedule[day].append(entry)

    return {
        "room_id": str(room_id),
        "schedule_by_day": schedule
    }
