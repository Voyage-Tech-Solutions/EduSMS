"""
EduCore Backend - Admission Interviews API
Schedule and manage admission interviews
"""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# MODELS
# ============================================================

class InterviewSlotCreate(BaseModel):
    """Create interview slots"""
    date: date
    start_time: str  # HH:MM format
    end_time: str
    duration_minutes: int = 30
    interviewer_id: Optional[UUID] = None
    location: Optional[str] = None
    notes: Optional[str] = None


class InterviewSchedule(BaseModel):
    """Schedule an interview"""
    application_id: UUID
    slot_id: UUID


class InterviewResult(BaseModel):
    """Record interview result"""
    rating: int  # 1-5
    strengths: List[str] = []
    areas_of_concern: List[str] = []
    notes: Optional[str] = None
    recommendation: str  # accept, reject, waitlist, additional_review


class BulkSlotCreate(BaseModel):
    """Create multiple interview slots"""
    start_date: date
    end_date: date
    days_of_week: List[int] = [1, 2, 3, 4, 5]  # 0=Sunday, 1=Monday, etc.
    start_time: str
    end_time: str
    slot_duration_minutes: int = 30
    break_duration_minutes: int = 10
    interviewer_id: Optional[UUID] = None
    location: Optional[str] = None


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/slots")
async def list_interview_slots(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    interviewer_id: Optional[UUID] = None,
    available_only: bool = True,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List available interview slots"""
    school_id = current_user.get("school_id")

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    query = supabase.table("interview_slots").select(
        "*, user_profiles(first_name, last_name)"
    ).eq("school_id", school_id)

    if date_from:
        query = query.gte("date", date_from.isoformat())
    if date_to:
        query = query.lte("date", date_to.isoformat())
    if interviewer_id:
        query = query.eq("interviewer_id", str(interviewer_id))
    if available_only:
        query = query.eq("is_booked", False)

    query = query.order("date").order("start_time")

    result = query.execute()

    return {"slots": result.data or []}


@router.get("/slots/{slot_id}")
async def get_slot(
    slot_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get a specific interview slot"""
    result = supabase.table("interview_slots").select(
        "*, user_profiles(first_name, last_name)"
    ).eq("id", str(slot_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Slot not found")

    return result.data


@router.post("/slots")
async def create_slot(
    slot: InterviewSlotCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create an interview slot"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    slot_data = {
        "school_id": school_id,
        "created_by": user_id,
        "date": slot.date.isoformat(),
        "start_time": slot.start_time,
        "end_time": slot.end_time,
        "duration_minutes": slot.duration_minutes,
        "interviewer_id": str(slot.interviewer_id) if slot.interviewer_id else user_id,
        "location": slot.location,
        "notes": slot.notes,
        "is_booked": False
    }

    result = supabase.table("interview_slots").insert(slot_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create slot")

    return result.data[0]


@router.post("/slots/bulk")
async def create_bulk_slots(
    bulk: BulkSlotCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create multiple interview slots at once"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    # Parse times
    start_hour, start_min = map(int, bulk.start_time.split(":"))
    end_hour, end_min = map(int, bulk.end_time.split(":"))

    slots_to_create = []
    current_date = bulk.start_date

    while current_date <= bulk.end_date:
        # Check if day is in selected days
        if current_date.weekday() + 1 in bulk.days_of_week or current_date.weekday() == 6 and 0 in bulk.days_of_week:
            # Create slots for this day
            current_time = datetime.combine(current_date, datetime.min.time().replace(
                hour=start_hour, minute=start_min
            ))
            end_time = datetime.combine(current_date, datetime.min.time().replace(
                hour=end_hour, minute=end_min
            ))

            while current_time + timedelta(minutes=bulk.slot_duration_minutes) <= end_time:
                slot_end = current_time + timedelta(minutes=bulk.slot_duration_minutes)

                slots_to_create.append({
                    "school_id": school_id,
                    "created_by": user_id,
                    "date": current_date.isoformat(),
                    "start_time": current_time.strftime("%H:%M"),
                    "end_time": slot_end.strftime("%H:%M"),
                    "duration_minutes": bulk.slot_duration_minutes,
                    "interviewer_id": str(bulk.interviewer_id) if bulk.interviewer_id else user_id,
                    "location": bulk.location,
                    "is_booked": False
                })

                current_time = slot_end + timedelta(minutes=bulk.break_duration_minutes)

        current_date += timedelta(days=1)

    if slots_to_create:
        result = supabase.table("interview_slots").insert(slots_to_create).execute()
        return {
            "success": True,
            "created_count": len(result.data) if result.data else 0
        }

    return {"success": True, "created_count": 0}


@router.delete("/slots/{slot_id}")
async def delete_slot(
    slot_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete an interview slot"""
    existing = supabase.table("interview_slots").select("is_booked").eq(
        "id", str(slot_id)
    ).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Slot not found")

    if existing.data.get("is_booked"):
        raise HTTPException(status_code=400, detail="Cannot delete a booked slot")

    supabase.table("interview_slots").delete().eq("id", str(slot_id)).execute()

    return {"success": True}


# ============================================================
# INTERVIEW MANAGEMENT
# ============================================================

@router.get("")
async def list_interviews(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    status: Optional[str] = None,
    interviewer_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List scheduled interviews"""
    school_id = current_user.get("school_id")

    query = supabase.table("admission_interviews").select(
        "*, interview_slots(date, start_time, location), admission_applications(form_data, tracking_code)"
    ).eq("school_id", school_id)

    if status:
        query = query.eq("status", status)
    if interviewer_id:
        query = query.eq("interviewer_id", str(interviewer_id))

    query = query.order("created_at", desc=True)

    result = query.execute()

    interviews = result.data or []

    # Filter by date if needed
    if date_from or date_to:
        filtered = []
        for interview in interviews:
            slot_date = interview.get("interview_slots", {}).get("date")
            if slot_date:
                d = date.fromisoformat(slot_date)
                if date_from and d < date_from:
                    continue
                if date_to and d > date_to:
                    continue
            filtered.append(interview)
        interviews = filtered

    return {"interviews": interviews}


@router.post("/schedule")
async def schedule_interview(
    schedule: InterviewSchedule,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Schedule an interview for an application"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    # Check slot availability
    slot = supabase.table("interview_slots").select(
        "id, is_booked, interviewer_id"
    ).eq("id", str(schedule.slot_id)).single().execute()

    if not slot.data:
        raise HTTPException(status_code=404, detail="Interview slot not found")

    if slot.data.get("is_booked"):
        raise HTTPException(status_code=400, detail="Slot is already booked")

    # Check application
    application = supabase.table("admission_applications").select(
        "id, status"
    ).eq("id", str(schedule.application_id)).single().execute()

    if not application.data:
        raise HTTPException(status_code=404, detail="Application not found")

    # Create interview record
    interview_data = {
        "school_id": school_id,
        "application_id": str(schedule.application_id),
        "slot_id": str(schedule.slot_id),
        "interviewer_id": slot.data.get("interviewer_id"),
        "scheduled_by": user_id,
        "status": "scheduled"
    }

    result = supabase.table("admission_interviews").insert(interview_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to schedule interview")

    # Mark slot as booked
    supabase.table("interview_slots").update({
        "is_booked": True
    }).eq("id", str(schedule.slot_id)).execute()

    # Update application status
    supabase.table("admission_applications").update({
        "status": "interview_scheduled"
    }).eq("id", str(schedule.application_id)).execute()

    return result.data[0]


@router.get("/{interview_id}")
async def get_interview(
    interview_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get interview details"""
    result = supabase.table("admission_interviews").select(
        "*, interview_slots(*), admission_applications(form_data, tracking_code, grade_applying)"
    ).eq("id", str(interview_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Interview not found")

    return result.data


@router.post("/{interview_id}/complete")
async def complete_interview(
    interview_id: UUID,
    result: InterviewResult,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Record interview completion and results"""
    user_id = current_user["id"]

    interview = supabase.table("admission_interviews").select(
        "id, application_id, status"
    ).eq("id", str(interview_id)).single().execute()

    if not interview.data:
        raise HTTPException(status_code=404, detail="Interview not found")

    if interview.data.get("status") == "completed":
        raise HTTPException(status_code=400, detail="Interview already completed")

    # Update interview
    supabase.table("admission_interviews").update({
        "status": "completed",
        "completed_at": datetime.utcnow().isoformat(),
        "rating": result.rating,
        "strengths": result.strengths,
        "areas_of_concern": result.areas_of_concern,
        "notes": result.notes,
        "recommendation": result.recommendation
    }).eq("id", str(interview_id)).execute()

    # Update application status based on recommendation
    new_status = "under_review"
    if result.recommendation == "accept":
        new_status = "accepted"
    elif result.recommendation == "reject":
        new_status = "rejected"
    elif result.recommendation == "waitlist":
        new_status = "waitlisted"

    supabase.table("admission_applications").update({
        "status": new_status
    }).eq("id", interview.data["application_id"]).execute()

    return {"success": True, "recommendation": result.recommendation}


@router.post("/{interview_id}/cancel")
async def cancel_interview(
    interview_id: UUID,
    reason: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Cancel a scheduled interview"""
    interview = supabase.table("admission_interviews").select(
        "id, slot_id, application_id, status"
    ).eq("id", str(interview_id)).single().execute()

    if not interview.data:
        raise HTTPException(status_code=404, detail="Interview not found")

    if interview.data.get("status") in ["completed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Interview cannot be cancelled")

    # Update interview
    supabase.table("admission_interviews").update({
        "status": "cancelled",
        "cancellation_reason": reason
    }).eq("id", str(interview_id)).execute()

    # Free up the slot
    supabase.table("interview_slots").update({
        "is_booked": False
    }).eq("id", interview.data["slot_id"]).execute()

    # Revert application status
    supabase.table("admission_applications").update({
        "status": "under_review"
    }).eq("id", interview.data["application_id"]).execute()

    return {"success": True}


@router.post("/{interview_id}/reschedule")
async def reschedule_interview(
    interview_id: UUID,
    new_slot_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Reschedule an interview to a different slot"""
    interview = supabase.table("admission_interviews").select(
        "id, slot_id, status"
    ).eq("id", str(interview_id)).single().execute()

    if not interview.data:
        raise HTTPException(status_code=404, detail="Interview not found")

    if interview.data.get("status") != "scheduled":
        raise HTTPException(status_code=400, detail="Only scheduled interviews can be rescheduled")

    # Check new slot
    new_slot = supabase.table("interview_slots").select(
        "id, is_booked, interviewer_id"
    ).eq("id", str(new_slot_id)).single().execute()

    if not new_slot.data:
        raise HTTPException(status_code=404, detail="New slot not found")

    if new_slot.data.get("is_booked"):
        raise HTTPException(status_code=400, detail="New slot is already booked")

    old_slot_id = interview.data["slot_id"]

    # Update interview
    supabase.table("admission_interviews").update({
        "slot_id": str(new_slot_id),
        "interviewer_id": new_slot.data.get("interviewer_id")
    }).eq("id", str(interview_id)).execute()

    # Free old slot
    supabase.table("interview_slots").update({
        "is_booked": False
    }).eq("id", old_slot_id).execute()

    # Book new slot
    supabase.table("interview_slots").update({
        "is_booked": True
    }).eq("id", str(new_slot_id)).execute()

    return {"success": True}
