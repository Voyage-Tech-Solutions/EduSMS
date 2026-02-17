"""
EduCore Backend - Timetables API
Class timetable management
"""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import date

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# MODELS
# ============================================================

class TimetableEntryCreate(BaseModel):
    """Create a timetable entry"""
    class_id: UUID
    subject_id: UUID
    teacher_id: UUID
    room_id: Optional[UUID] = None
    day_of_week: int  # 1-7 (Monday-Sunday)
    period: int
    academic_year_id: Optional[UUID] = None


class TimetableEntryUpdate(BaseModel):
    """Update a timetable entry"""
    subject_id: Optional[UUID] = None
    teacher_id: Optional[UUID] = None
    room_id: Optional[UUID] = None


class BulkTimetableCreate(BaseModel):
    """Create multiple timetable entries"""
    class_id: UUID
    entries: List[TimetableEntryCreate]


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/class/{class_id}")
async def get_class_timetable(
    class_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get timetable for a class"""
    result = supabase.table("timetable_entries").select(
        "*, subjects(name, code), teachers:teacher_id(first_name, last_name), rooms(name, room_number)"
    ).eq("class_id", str(class_id)).order("day_of_week").order("period").execute()

    # Group by day
    timetable = {i: [] for i in range(1, 8)}  # 1-7 for days
    for entry in (result.data or []):
        day = entry.get("day_of_week", 1)
        if day in timetable:
            timetable[day].append(entry)

    return {
        "class_id": str(class_id),
        "timetable_by_day": timetable
    }


@router.get("/teacher/{teacher_id}")
async def get_teacher_timetable(
    teacher_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get timetable for a teacher"""
    result = supabase.table("timetable_entries").select(
        "*, subjects(name, code), classes(name), rooms(name, room_number)"
    ).eq("teacher_id", str(teacher_id)).order("day_of_week").order("period").execute()

    # Group by day
    timetable = {i: [] for i in range(1, 8)}
    for entry in (result.data or []):
        day = entry.get("day_of_week", 1)
        if day in timetable:
            timetable[day].append(entry)

    # Calculate workload
    total_periods = len(result.data) if result.data else 0
    unique_classes = len(set(e.get("class_id") for e in (result.data or [])))
    unique_subjects = len(set(e.get("subject_id") for e in (result.data or [])))

    return {
        "teacher_id": str(teacher_id),
        "timetable_by_day": timetable,
        "workload": {
            "total_periods_per_week": total_periods,
            "classes_taught": unique_classes,
            "subjects_taught": unique_subjects
        }
    }


@router.get("/room/{room_id}")
async def get_room_timetable(
    room_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get timetable for a room"""
    result = supabase.table("timetable_entries").select(
        "*, subjects(name), classes(name), teachers:teacher_id(first_name, last_name)"
    ).eq("room_id", str(room_id)).order("day_of_week").order("period").execute()

    # Group by day
    timetable = {i: [] for i in range(1, 8)}
    for entry in (result.data or []):
        day = entry.get("day_of_week", 1)
        if day in timetable:
            timetable[day].append(entry)

    return {
        "room_id": str(room_id),
        "timetable_by_day": timetable
    }


@router.get("/entry/{entry_id}")
async def get_timetable_entry(
    entry_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get a specific timetable entry"""
    result = supabase.table("timetable_entries").select(
        "*, subjects(name, code), classes(name), teachers:teacher_id(first_name, last_name), rooms(name, room_number)"
    ).eq("id", str(entry_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Timetable entry not found")

    return result.data


@router.post("/entry")
async def create_timetable_entry(
    entry: TimetableEntryCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a single timetable entry"""
    school_id = current_user.get("school_id")

    # Check for conflicts
    conflicts = await _check_conflicts(
        supabase,
        str(entry.class_id),
        str(entry.teacher_id),
        str(entry.room_id) if entry.room_id else None,
        entry.day_of_week,
        entry.period
    )

    if conflicts:
        raise HTTPException(
            status_code=400,
            detail=f"Scheduling conflict: {conflicts}"
        )

    entry_data = {
        "school_id": school_id,
        "class_id": str(entry.class_id),
        "subject_id": str(entry.subject_id),
        "teacher_id": str(entry.teacher_id),
        "room_id": str(entry.room_id) if entry.room_id else None,
        "day_of_week": entry.day_of_week,
        "period": entry.period,
        "academic_year_id": str(entry.academic_year_id) if entry.academic_year_id else None
    }

    result = supabase.table("timetable_entries").insert(entry_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create entry")

    return result.data[0]


@router.post("/bulk")
async def create_bulk_timetable(
    bulk: BulkTimetableCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create multiple timetable entries at once"""
    school_id = current_user.get("school_id")

    created = []
    conflicts = []

    for entry in bulk.entries:
        # Check for conflicts
        conflict = await _check_conflicts(
            supabase,
            str(entry.class_id),
            str(entry.teacher_id),
            str(entry.room_id) if entry.room_id else None,
            entry.day_of_week,
            entry.period
        )

        if conflict:
            conflicts.append({
                "day": entry.day_of_week,
                "period": entry.period,
                "conflict": conflict
            })
            continue

        entry_data = {
            "school_id": school_id,
            "class_id": str(entry.class_id),
            "subject_id": str(entry.subject_id),
            "teacher_id": str(entry.teacher_id),
            "room_id": str(entry.room_id) if entry.room_id else None,
            "day_of_week": entry.day_of_week,
            "period": entry.period,
            "academic_year_id": str(entry.academic_year_id) if entry.academic_year_id else None
        }

        result = supabase.table("timetable_entries").insert(entry_data).execute()
        if result.data:
            created.append(result.data[0])

    return {
        "created_count": len(created),
        "conflict_count": len(conflicts),
        "conflicts": conflicts
    }


@router.put("/entry/{entry_id}")
async def update_timetable_entry(
    entry_id: UUID,
    update: TimetableEntryUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update a timetable entry"""
    existing = supabase.table("timetable_entries").select(
        "class_id, day_of_week, period"
    ).eq("id", str(entry_id)).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Entry not found")

    # Check for conflicts if teacher or room changed
    if update.teacher_id or update.room_id:
        teacher_id = str(update.teacher_id) if update.teacher_id else None
        room_id = str(update.room_id) if update.room_id else None

        conflicts = await _check_conflicts(
            supabase,
            existing.data["class_id"],
            teacher_id,
            room_id,
            existing.data["day_of_week"],
            existing.data["period"],
            exclude_entry_id=str(entry_id)
        )

        if conflicts:
            raise HTTPException(
                status_code=400,
                detail=f"Scheduling conflict: {conflicts}"
            )

    update_data = {}
    if update.subject_id is not None:
        update_data["subject_id"] = str(update.subject_id)
    if update.teacher_id is not None:
        update_data["teacher_id"] = str(update.teacher_id)
    if update.room_id is not None:
        update_data["room_id"] = str(update.room_id)

    result = supabase.table("timetable_entries").update(update_data).eq(
        "id", str(entry_id)
    ).execute()

    return result.data[0] if result.data else None


@router.delete("/entry/{entry_id}")
async def delete_timetable_entry(
    entry_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a timetable entry"""
    supabase.table("timetable_entries").delete().eq("id", str(entry_id)).execute()
    return {"success": True}


@router.delete("/class/{class_id}/clear")
async def clear_class_timetable(
    class_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Clear all timetable entries for a class"""
    result = supabase.table("timetable_entries").delete().eq(
        "class_id", str(class_id)
    ).execute()

    return {"success": True, "deleted_count": len(result.data) if result.data else 0}


@router.post("/class/{class_id}/copy-from/{source_class_id}")
async def copy_timetable(
    class_id: UUID,
    source_class_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Copy timetable from one class to another"""
    school_id = current_user.get("school_id")

    # Get source timetable
    source = supabase.table("timetable_entries").select("*").eq(
        "class_id", str(source_class_id)
    ).execute()

    if not source.data:
        raise HTTPException(status_code=404, detail="Source timetable not found")

    created = 0
    for entry in source.data:
        new_entry = {
            "school_id": school_id,
            "class_id": str(class_id),
            "subject_id": entry["subject_id"],
            "teacher_id": entry["teacher_id"],
            "room_id": entry.get("room_id"),
            "day_of_week": entry["day_of_week"],
            "period": entry["period"],
            "academic_year_id": entry.get("academic_year_id")
        }

        result = supabase.table("timetable_entries").insert(new_entry).execute()
        if result.data:
            created += 1

    return {"success": True, "entries_copied": created}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

async def _check_conflicts(
    supabase,
    class_id: str,
    teacher_id: Optional[str],
    room_id: Optional[str],
    day_of_week: int,
    period: int,
    exclude_entry_id: Optional[str] = None
) -> Optional[str]:
    """Check for scheduling conflicts"""
    conflicts = []

    # Check class conflict
    class_query = supabase.table("timetable_entries").select("id").eq(
        "class_id", class_id
    ).eq("day_of_week", day_of_week).eq("period", period)

    if exclude_entry_id:
        class_query = class_query.neq("id", exclude_entry_id)

    class_conflict = class_query.execute()
    if class_conflict.data:
        conflicts.append("Class already has a lesson at this time")

    # Check teacher conflict
    if teacher_id:
        teacher_query = supabase.table("timetable_entries").select(
            "classes(name)"
        ).eq("teacher_id", teacher_id).eq("day_of_week", day_of_week).eq("period", period)

        if exclude_entry_id:
            teacher_query = teacher_query.neq("id", exclude_entry_id)

        teacher_conflict = teacher_query.execute()
        if teacher_conflict.data:
            other_class = teacher_conflict.data[0].get("classes", {}).get("name", "another class")
            conflicts.append(f"Teacher is teaching {other_class} at this time")

    # Check room conflict
    if room_id:
        room_query = supabase.table("timetable_entries").select(
            "classes(name)"
        ).eq("room_id", room_id).eq("day_of_week", day_of_week).eq("period", period)

        if exclude_entry_id:
            room_query = room_query.neq("id", exclude_entry_id)

        room_conflict = room_query.execute()
        if room_conflict.data:
            other_class = room_conflict.data[0].get("classes", {}).get("name", "another class")
            conflicts.append(f"Room is used by {other_class} at this time")

    return "; ".join(conflicts) if conflicts else None
