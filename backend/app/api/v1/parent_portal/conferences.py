"""
EduCore Backend - Parent-Teacher Conference API
Book and manage parent-teacher conferences
"""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import date, time, datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# MODELS
# ============================================================

class ConferenceBookingCreate(BaseModel):
    """Book a conference slot"""
    slot_id: UUID
    student_id: UUID
    topics: List[str] = []
    notes: Optional[str] = None


class ConferenceBookingUpdate(BaseModel):
    """Update a booking"""
    topics: Optional[List[str]] = None
    notes: Optional[str] = None


# ============================================================
# AVAILABLE SLOTS
# ============================================================

@router.get("/available-slots")
async def get_available_slots(
    teacher_id: Optional[UUID] = None,
    student_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get available conference slots for booking"""
    school_id = current_user.get("school_id")
    parent_id = current_user.get("id")

    if not start_date:
        start_date = date.today()
    if not end_date:
        end_date = start_date + timedelta(days=30)

    # If student provided, get their teachers
    teacher_ids = []
    if student_id:
        # Get student's class assignments
        student = supabase.table("students").select("class_id").eq(
            "id", str(student_id)
        ).single().execute()

        if student.data:
            class_subjects = supabase.table("class_subjects").select(
                "teacher_id"
            ).eq("class_id", student.data["class_id"]).execute()

            teacher_ids = list(set(cs["teacher_id"] for cs in (class_subjects.data or [])))

    # Get available slots
    query = supabase.table("conference_slots").select(
        "*, teacher:teacher_id(first_name, last_name, subjects(name))"
    ).eq("school_id", school_id).eq("is_available", True).gte(
        "date", start_date.isoformat()
    ).lte("date", end_date.isoformat())

    if teacher_id:
        query = query.eq("teacher_id", str(teacher_id))
    elif teacher_ids:
        query = query.in_("teacher_id", teacher_ids)

    result = query.order("date").order("start_time").execute()

    # Filter out already booked slots
    slots = result.data or []
    available = []

    for slot in slots:
        # Check if slot is booked
        booking = supabase.table("conference_bookings").select("id").eq(
            "slot_id", slot["id"]
        ).eq("status", "confirmed").execute()

        if not booking.data:
            available.append(slot)

    return {"available_slots": available}


@router.get("/my-bookings")
async def get_my_bookings(
    status: Optional[str] = None,
    upcoming_only: bool = True,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get parent's conference bookings"""
    parent_id = current_user.get("id")

    query = supabase.table("conference_bookings").select(
        "*, slot:slot_id(date, start_time, end_time, location, is_virtual, meeting_link, teacher:teacher_id(first_name, last_name)), student:student_id(first_name, last_name)"
    ).eq("parent_id", parent_id)

    if status:
        query = query.eq("status", status)

    if upcoming_only:
        today = date.today()
        # Filter by slot date - we'll filter in Python since it's a nested relation
        query = query.order("created_at", desc=True)

    result = query.execute()

    bookings = result.data or []

    # Filter upcoming if needed
    if upcoming_only:
        today_str = date.today().isoformat()
        bookings = [
            b for b in bookings
            if b.get("slot") and b["slot"].get("date", "") >= today_str
        ]

    return {"bookings": bookings}


@router.post("/book")
async def book_conference(
    booking: ConferenceBookingCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Book a conference slot"""
    parent_id = current_user.get("id")
    school_id = current_user.get("school_id")

    # Check slot availability
    slot = supabase.table("conference_slots").select("*").eq(
        "id", str(booking.slot_id)
    ).single().execute()

    if not slot.data:
        raise HTTPException(status_code=404, detail="Conference slot not found")

    if not slot.data.get("is_available"):
        raise HTTPException(status_code=400, detail="Slot is not available")

    # Check if slot is already booked
    existing = supabase.table("conference_bookings").select("id").eq(
        "slot_id", str(booking.slot_id)
    ).eq("status", "confirmed").execute()

    if existing.data:
        raise HTTPException(status_code=400, detail="Slot is already booked")

    # Check if parent owns the student
    parent_students = supabase.table("parent_student_relations").select("student_id").eq(
        "parent_id", parent_id
    ).execute()

    student_ids = [ps["student_id"] for ps in (parent_students.data or [])]
    if str(booking.student_id) not in student_ids:
        raise HTTPException(status_code=403, detail="You can only book conferences for your own children")

    # Create booking
    booking_data = {
        "school_id": school_id,
        "slot_id": str(booking.slot_id),
        "parent_id": parent_id,
        "student_id": str(booking.student_id),
        "topics": booking.topics,
        "notes": booking.notes,
        "status": "confirmed"
    }

    result = supabase.table("conference_bookings").insert(booking_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to book conference")

    return result.data[0]


@router.put("/{booking_id}")
async def update_booking(
    booking_id: UUID,
    update: ConferenceBookingUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update a conference booking"""
    parent_id = current_user.get("id")

    existing = supabase.table("conference_bookings").select("parent_id, status").eq(
        "id", str(booking_id)
    ).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Booking not found")

    if existing.data["parent_id"] != parent_id:
        raise HTTPException(status_code=403, detail="You can only update your own bookings")

    if existing.data["status"] == "cancelled":
        raise HTTPException(status_code=400, detail="Cannot update cancelled booking")

    update_data = {}
    if update.topics is not None:
        update_data["topics"] = update.topics
    if update.notes is not None:
        update_data["notes"] = update.notes

    result = supabase.table("conference_bookings").update(update_data).eq(
        "id", str(booking_id)
    ).execute()

    return result.data[0] if result.data else None


@router.post("/{booking_id}/cancel")
async def cancel_booking(
    booking_id: UUID,
    reason: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Cancel a conference booking"""
    parent_id = current_user.get("id")

    existing = supabase.table("conference_bookings").select(
        "parent_id, status, slot:slot_id(date)"
    ).eq("id", str(booking_id)).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Booking not found")

    if existing.data["parent_id"] != parent_id:
        raise HTTPException(status_code=403, detail="You can only cancel your own bookings")

    if existing.data["status"] == "cancelled":
        raise HTTPException(status_code=400, detail="Booking is already cancelled")

    # Check if it's at least 24 hours before
    if existing.data.get("slot"):
        slot_date = existing.data["slot"].get("date")
        if slot_date:
            conf_date = datetime.fromisoformat(slot_date).date()
            if conf_date <= date.today():
                raise HTTPException(
                    status_code=400,
                    detail="Cannot cancel conferences less than 24 hours in advance"
                )

    supabase.table("conference_bookings").update({
        "status": "cancelled",
        "cancelled_at": datetime.utcnow().isoformat(),
        "cancelled_reason": reason
    }).eq("id", str(booking_id)).execute()

    return {"success": True, "status": "cancelled"}


@router.get("/teachers")
async def get_available_teachers(
    student_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get teachers available for conferences"""
    school_id = current_user.get("school_id")
    parent_id = current_user.get("id")

    # Get parent's children
    if not student_id:
        parent_students = supabase.table("parent_student_relations").select(
            "student_id"
        ).eq("parent_id", parent_id).execute()

        student_ids = [ps["student_id"] for ps in (parent_students.data or [])]
    else:
        student_ids = [str(student_id)]

    if not student_ids:
        return {"teachers": []}

    # Get students' classes
    students = supabase.table("students").select("class_id").in_(
        "id", student_ids
    ).execute()

    class_ids = list(set(s["class_id"] for s in (students.data or []) if s.get("class_id")))

    if not class_ids:
        return {"teachers": []}

    # Get teachers teaching these classes
    class_subjects = supabase.table("class_subjects").select(
        "teacher_id, teachers(id, first_name, last_name, email), subjects(name)"
    ).in_("class_id", class_ids).execute()

    teachers = {}
    for cs in (class_subjects.data or []):
        if cs.get("teachers"):
            teacher = cs["teachers"]
            tid = teacher["id"]
            if tid not in teachers:
                teachers[tid] = {
                    "id": tid,
                    "name": f"{teacher['first_name']} {teacher['last_name']}",
                    "email": teacher.get("email"),
                    "subjects": []
                }
            if cs.get("subjects"):
                teachers[tid]["subjects"].append(cs["subjects"]["name"])

    return {"teachers": list(teachers.values())}


@router.get("/upcoming-conferences")
async def get_upcoming_conferences(
    days: int = 30,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get upcoming conference opportunities"""
    school_id = current_user.get("school_id")

    today = date.today()
    end_date = today + timedelta(days=days)

    # Get conference events/periods
    events = supabase.table("school_events").select("*").eq(
        "school_id", school_id
    ).eq("event_type", "conference").gte(
        "start_date", today.isoformat()
    ).lte("start_date", end_date.isoformat()).execute()

    return {"upcoming_conference_events": events.data or []}
