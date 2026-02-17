"""
EduCore Backend - Substitutions API
Manage teacher substitutions
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

class SubstitutionCreate(BaseModel):
    """Create a substitution"""
    original_teacher_id: UUID
    substitute_teacher_id: UUID
    substitution_date: date
    period: Optional[int] = None  # None means all day
    class_id: Optional[UUID] = None  # If None, all classes
    reason: str
    notes: Optional[str] = None


class SubstitutionUpdate(BaseModel):
    """Update a substitution"""
    substitute_teacher_id: Optional[UUID] = None
    status: Optional[str] = None  # pending, confirmed, completed, cancelled
    notes: Optional[str] = None


class TeacherAbsence(BaseModel):
    """Record teacher absence"""
    teacher_id: UUID
    absence_date: date
    end_date: Optional[date] = None  # For multi-day absences
    reason: str
    notes: Optional[str] = None
    auto_assign_substitutes: bool = True


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("")
async def list_substitutions(
    substitution_date: Optional[date] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    original_teacher_id: Optional[UUID] = None,
    substitute_teacher_id: Optional[UUID] = None,
    status: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List substitutions with filters"""
    school_id = current_user.get("school_id")

    query = supabase.table("substitutions").select(
        "*, original:original_teacher_id(first_name, last_name), substitute:substitute_teacher_id(first_name, last_name), classes(name)"
    ).eq("school_id", school_id)

    if substitution_date:
        query = query.eq("substitution_date", substitution_date.isoformat())
    if date_from:
        query = query.gte("substitution_date", date_from.isoformat())
    if date_to:
        query = query.lte("substitution_date", date_to.isoformat())
    if original_teacher_id:
        query = query.eq("original_teacher_id", str(original_teacher_id))
    if substitute_teacher_id:
        query = query.eq("substitute_teacher_id", str(substitute_teacher_id))
    if status:
        query = query.eq("status", status)

    query = query.order("substitution_date", desc=True).order("period").range(offset, offset + limit - 1)

    result = query.execute()

    return {
        "substitutions": result.data or [],
        "total": len(result.data) if result.data else 0,
        "limit": limit,
        "offset": offset
    }


@router.get("/today")
async def get_today_substitutions(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get today's substitutions"""
    school_id = current_user.get("school_id")
    today = date.today()

    result = supabase.table("substitutions").select(
        "*, original:original_teacher_id(first_name, last_name), substitute:substitute_teacher_id(first_name, last_name), classes(name)"
    ).eq("school_id", school_id).eq("substitution_date", today.isoformat()).order("period").execute()

    # Group by period
    by_period = {}
    for sub in (result.data or []):
        period = sub.get("period") or "all_day"
        if period not in by_period:
            by_period[period] = []
        by_period[period].append(sub)

    return {
        "date": today.isoformat(),
        "substitutions": result.data or [],
        "by_period": by_period,
        "total": len(result.data) if result.data else 0
    }


@router.get("/teacher/{teacher_id}")
async def get_teacher_substitutions(
    teacher_id: UUID,
    role: str = "substitute",  # original, substitute
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get substitutions for a teacher"""
    field = "substitute_teacher_id" if role == "substitute" else "original_teacher_id"

    query = supabase.table("substitutions").select(
        "*, original:original_teacher_id(first_name, last_name), substitute:substitute_teacher_id(first_name, last_name), classes(name)"
    ).eq(field, str(teacher_id))

    if date_from:
        query = query.gte("substitution_date", date_from.isoformat())
    if date_to:
        query = query.lte("substitution_date", date_to.isoformat())

    query = query.order("substitution_date", desc=True)

    result = query.execute()

    return {
        "teacher_id": str(teacher_id),
        "role": role,
        "substitutions": result.data or []
    }


@router.get("/{substitution_id}")
async def get_substitution(
    substitution_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get substitution details"""
    result = supabase.table("substitutions").select(
        "*, original:original_teacher_id(first_name, last_name, email), substitute:substitute_teacher_id(first_name, last_name, email), classes(name)"
    ).eq("id", str(substitution_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Substitution not found")

    return result.data


@router.post("")
async def create_substitution(
    substitution: SubstitutionCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a substitution"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    # Check if substitute is available
    if substitution.period:
        # Check for specific period
        conflict = supabase.table("timetable_entries").select("id").eq(
            "teacher_id", str(substitution.substitute_teacher_id)
        ).eq("day_of_week", substitution.substitution_date.isoweekday()).eq(
            "period", substitution.period
        ).execute()

        if conflict.data:
            raise HTTPException(
                status_code=400,
                detail="Substitute teacher has a class at this time"
            )

    sub_data = {
        "school_id": school_id,
        "original_teacher_id": str(substitution.original_teacher_id),
        "substitute_teacher_id": str(substitution.substitute_teacher_id),
        "substitution_date": substitution.substitution_date.isoformat(),
        "period": substitution.period,
        "class_id": str(substitution.class_id) if substitution.class_id else None,
        "reason": substitution.reason,
        "notes": substitution.notes,
        "created_by": user_id,
        "status": "pending"
    }

    result = supabase.table("substitutions").insert(sub_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create substitution")

    return result.data[0]


@router.post("/absence")
async def record_absence(
    absence: TeacherAbsence,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Record teacher absence and optionally auto-assign substitutes"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    # Record absence
    absence_data = {
        "school_id": school_id,
        "teacher_id": str(absence.teacher_id),
        "start_date": absence.absence_date.isoformat(),
        "end_date": (absence.end_date or absence.absence_date).isoformat(),
        "reason": absence.reason,
        "notes": absence.notes,
        "recorded_by": user_id,
        "recorded_at": datetime.utcnow().isoformat()
    }

    supabase.table("teacher_absences").insert(absence_data).execute()

    substitutions_created = []

    if absence.auto_assign_substitutes:
        # Get teacher's timetable for the date(s)
        current_date = absence.absence_date
        end_date = absence.end_date or absence.absence_date

        while current_date <= end_date:
            dow = current_date.isoweekday()

            # Get classes for this day
            classes = supabase.table("timetable_entries").select(
                "period, class_id, subject_id"
            ).eq("teacher_id", str(absence.teacher_id)).eq("day_of_week", dow).execute()

            for entry in (classes.data or []):
                # Find available substitute
                available = await _find_available_substitute(
                    supabase,
                    school_id,
                    str(absence.teacher_id),
                    current_date,
                    entry["period"],
                    entry.get("subject_id")
                )

                if available:
                    sub_data = {
                        "school_id": school_id,
                        "original_teacher_id": str(absence.teacher_id),
                        "substitute_teacher_id": available,
                        "substitution_date": current_date.isoformat(),
                        "period": entry["period"],
                        "class_id": entry["class_id"],
                        "reason": absence.reason,
                        "created_by": user_id,
                        "status": "pending",
                        "auto_assigned": True
                    }

                    result = supabase.table("substitutions").insert(sub_data).execute()
                    if result.data:
                        substitutions_created.append(result.data[0])

            current_date = current_date + timedelta(days=1)

    return {
        "success": True,
        "absence_recorded": True,
        "substitutions_created": len(substitutions_created),
        "substitutions": substitutions_created
    }


@router.put("/{substitution_id}")
async def update_substitution(
    substitution_id: UUID,
    update: SubstitutionUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update a substitution"""
    existing = supabase.table("substitutions").select("id").eq(
        "id", str(substitution_id)
    ).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Substitution not found")

    update_data = {}
    if update.substitute_teacher_id is not None:
        update_data["substitute_teacher_id"] = str(update.substitute_teacher_id)
    if update.status is not None:
        update_data["status"] = update.status
    if update.notes is not None:
        update_data["notes"] = update.notes

    result = supabase.table("substitutions").update(update_data).eq(
        "id", str(substitution_id)
    ).execute()

    return result.data[0] if result.data else None


@router.post("/{substitution_id}/confirm")
async def confirm_substitution(
    substitution_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Confirm a substitution"""
    supabase.table("substitutions").update({
        "status": "confirmed",
        "confirmed_at": datetime.utcnow().isoformat()
    }).eq("id", str(substitution_id)).execute()

    return {"success": True, "status": "confirmed"}


@router.post("/{substitution_id}/cancel")
async def cancel_substitution(
    substitution_id: UUID,
    reason: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Cancel a substitution"""
    supabase.table("substitutions").update({
        "status": "cancelled",
        "cancellation_reason": reason,
        "cancelled_at": datetime.utcnow().isoformat()
    }).eq("id", str(substitution_id)).execute()

    return {"success": True, "status": "cancelled"}


@router.delete("/{substitution_id}")
async def delete_substitution(
    substitution_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a substitution"""
    supabase.table("substitutions").delete().eq("id", str(substitution_id)).execute()
    return {"success": True}


@router.get("/available-teachers")
async def get_available_teachers(
    substitution_date: date,
    period: int,
    subject_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get teachers available for substitution"""
    school_id = current_user.get("school_id")
    dow = substitution_date.isoweekday()

    # Get all teachers
    teachers = supabase.table("teachers").select(
        "id, first_name, last_name, subjects_taught"
    ).eq("school_id", school_id).eq("is_active", True).execute()

    available = []

    for teacher in (teachers.data or []):
        # Check if teacher has a class at this time
        has_class = supabase.table("timetable_entries").select("id").eq(
            "teacher_id", teacher["id"]
        ).eq("day_of_week", dow).eq("period", period).execute()

        if has_class.data:
            continue

        # Check if already assigned as substitute
        has_sub = supabase.table("substitutions").select("id").eq(
            "substitute_teacher_id", teacher["id"]
        ).eq("substitution_date", substitution_date.isoformat()).eq(
            "period", period
        ).not_.eq("status", "cancelled").execute()

        if has_sub.data:
            continue

        teacher_info = {
            "id": teacher["id"],
            "name": f"{teacher['first_name']} {teacher['last_name']}",
            "subjects": teacher.get("subjects_taught", [])
        }

        # Mark if teacher teaches the needed subject
        if subject_id and subject_id in (teacher.get("subjects_taught") or []):
            teacher_info["teaches_subject"] = True

        available.append(teacher_info)

    # Sort - teachers who teach the subject first
    if subject_id:
        available.sort(key=lambda x: not x.get("teaches_subject", False))

    return {"available_teachers": available}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

from datetime import timedelta

async def _find_available_substitute(
    supabase,
    school_id: str,
    absent_teacher_id: str,
    sub_date: date,
    period: int,
    subject_id: Optional[str] = None
) -> Optional[str]:
    """Find an available substitute teacher"""
    dow = sub_date.isoweekday()

    # Get all teachers except the absent one
    teachers = supabase.table("teachers").select(
        "id, subjects_taught"
    ).eq("school_id", school_id).eq("is_active", True).neq(
        "id", absent_teacher_id
    ).execute()

    for teacher in (teachers.data or []):
        # Check if free at this time
        has_class = supabase.table("timetable_entries").select("id").eq(
            "teacher_id", teacher["id"]
        ).eq("day_of_week", dow).eq("period", period).execute()

        if has_class.data:
            continue

        # Check if already assigned
        has_sub = supabase.table("substitutions").select("id").eq(
            "substitute_teacher_id", teacher["id"]
        ).eq("substitution_date", sub_date.isoformat()).eq(
            "period", period
        ).not_.eq("status", "cancelled").execute()

        if has_sub.data:
            continue

        # Prefer teachers who teach the same subject
        if subject_id and subject_id in (teacher.get("subjects_taught") or []):
            return teacher["id"]

    # If no subject match, return first available
    for teacher in (teachers.data or []):
        has_class = supabase.table("timetable_entries").select("id").eq(
            "teacher_id", teacher["id"]
        ).eq("day_of_week", dow).eq("period", period).execute()

        if not has_class.data:
            return teacher["id"]

    return None
