"""
EduCore Backend - Parent Calendar API
Unified calendar view with school events, assignments, and attendance
"""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime, timedelta
from collections import defaultdict

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# CALENDAR EVENTS
# ============================================================

@router.get("/events")
async def get_calendar_events(
    start_date: date,
    end_date: date,
    student_id: Optional[UUID] = None,
    event_types: Optional[str] = None,  # comma-separated: school,assignment,attendance,fee,conference
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get all calendar events for date range"""
    parent_id = current_user.get("id")
    school_id = current_user.get("school_id")

    # Get parent's children
    relations = supabase.table("parent_student_relations").select(
        "student_id, students(id, first_name, last_name, class_id)"
    ).eq("parent_id", parent_id).execute()

    children = []
    student_ids = []
    class_ids = []

    for rel in (relations.data or []):
        if rel.get("students"):
            student = rel["students"]
            children.append(student)
            student_ids.append(student["id"])
            if student.get("class_id"):
                class_ids.append(student["class_id"])

    if student_id:
        if str(student_id) not in student_ids:
            raise HTTPException(status_code=403, detail="Access denied")
        student_ids = [str(student_id)]
        # Filter class_ids too
        class_ids = [c["class_id"] for c in children if c["id"] == str(student_id) and c.get("class_id")]

    # Parse event types filter
    types = event_types.split(",") if event_types else ["school", "assignment", "attendance", "fee", "conference"]

    events = []

    # School events
    if "school" in types:
        school_events = supabase.table("school_events").select("*").eq(
            "school_id", school_id
        ).gte("start_date", start_date.isoformat()).lte(
            "start_date", end_date.isoformat()
        ).execute()

        for event in (school_events.data or []):
            events.append({
                "id": event["id"],
                "type": "school_event",
                "title": event["title"],
                "description": event.get("description"),
                "date": event["start_date"],
                "end_date": event.get("end_date"),
                "all_day": event.get("all_day", True),
                "location": event.get("location"),
                "color": "#4CAF50",  # Green for school events
                "student_id": None
            })

    # Assignments
    if "assignment" in types and class_ids:
        assignments = supabase.table("assignments").select(
            "*, subjects(name)"
        ).in_("class_id", class_ids).gte(
            "due_date", start_date.isoformat()
        ).lte("due_date", end_date.isoformat()).execute()

        for assignment in (assignments.data or []):
            events.append({
                "id": assignment["id"],
                "type": "assignment",
                "title": f"Due: {assignment['title']}",
                "description": assignment.get("description"),
                "date": assignment["due_date"],
                "subject": assignment["subjects"]["name"] if assignment.get("subjects") else None,
                "color": "#FF9800",  # Orange for assignments
                "student_id": None  # Applies to class
            })

    # Attendance (absences/tardies)
    if "attendance" in types and student_ids:
        attendance = supabase.table("attendance").select(
            "*, students(first_name, last_name)"
        ).in_("student_id", student_ids).gte(
            "date", start_date.isoformat()
        ).lte("date", end_date.isoformat()).neq("status", "present").execute()

        for att in (attendance.data or []):
            student_name = f"{att['students']['first_name']} {att['students']['last_name']}" if att.get("students") else "Unknown"
            status_label = att["status"].replace("_", " ").title()
            events.append({
                "id": att["id"],
                "type": "attendance",
                "title": f"{student_name}: {status_label}",
                "date": att["date"],
                "status": att["status"],
                "color": "#F44336" if att["status"] == "absent" else "#FFC107",  # Red/Yellow
                "student_id": att["student_id"]
            })

    # Fee due dates
    if "fee" in types and student_ids:
        fees = supabase.table("fee_records").select(
            "*, students(first_name, last_name), fee_types(name)"
        ).in_("student_id", student_ids).gte(
            "due_date", start_date.isoformat()
        ).lte("due_date", end_date.isoformat()).neq("status", "paid").execute()

        for fee in (fees.data or []):
            student_name = f"{fee['students']['first_name']}" if fee.get("students") else ""
            fee_name = fee["fee_types"]["name"] if fee.get("fee_types") else "Fee"
            remaining = fee["amount"] - (fee.get("amount_paid") or 0)
            events.append({
                "id": fee["id"],
                "type": "fee_due",
                "title": f"{fee_name} Due - ${remaining:.2f}",
                "description": f"For {student_name}" if student_name else None,
                "date": fee["due_date"],
                "amount": remaining,
                "color": "#E91E63",  # Pink for fees
                "student_id": fee["student_id"]
            })

    # Conferences
    if "conference" in types:
        conferences = supabase.table("conference_bookings").select(
            "*, slot:slot_id(date, start_time, end_time, teacher:teacher_id(first_name, last_name)), student:student_id(first_name, last_name)"
        ).eq("parent_id", parent_id).eq("status", "confirmed").execute()

        for conf in (conferences.data or []):
            if conf.get("slot"):
                slot = conf["slot"]
                if slot.get("date") and start_date.isoformat() <= slot["date"] <= end_date.isoformat():
                    teacher_name = f"{slot['teacher']['first_name']} {slot['teacher']['last_name']}" if slot.get("teacher") else "Teacher"
                    student_name = f"{conf['student']['first_name']}" if conf.get("student") else ""
                    events.append({
                        "id": conf["id"],
                        "type": "conference",
                        "title": f"Conference: {teacher_name}",
                        "description": f"For {student_name}" if student_name else None,
                        "date": slot["date"],
                        "start_time": slot.get("start_time"),
                        "end_time": slot.get("end_time"),
                        "color": "#9C27B0",  # Purple for conferences
                        "student_id": conf.get("student_id")
                    })

    # Sort by date
    events.sort(key=lambda x: (x["date"], x.get("start_time", "00:00")))

    return {
        "events": events,
        "children": children,
        "date_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        }
    }


@router.get("/today")
async def get_today_events(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get today's events"""
    today = date.today()
    return await get_calendar_events(
        start_date=today,
        end_date=today,
        current_user=current_user,
        supabase=supabase
    )


@router.get("/week")
async def get_week_events(
    week_start: Optional[date] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get this week's events"""
    if not week_start:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())  # Monday
    week_end = week_start + timedelta(days=6)

    return await get_calendar_events(
        start_date=week_start,
        end_date=week_end,
        current_user=current_user,
        supabase=supabase
    )


@router.get("/month")
async def get_month_events(
    year: Optional[int] = None,
    month: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get month's events"""
    today = date.today()
    if not year:
        year = today.year
    if not month:
        month = today.month

    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)

    return await get_calendar_events(
        start_date=start_date,
        end_date=end_date,
        current_user=current_user,
        supabase=supabase
    )


# ============================================================
# CALENDAR SYNC (ICAL)
# ============================================================

@router.get("/sync/ical-url")
async def get_ical_url(
    student_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get iCal feed URL for calendar sync"""
    parent_id = current_user.get("id")
    school_id = current_user.get("school_id")

    # Generate or get existing sync token
    existing = supabase.table("calendar_sync_tokens").select("token").eq(
        "user_id", parent_id
    ).single().execute()

    if existing.data:
        token = existing.data["token"]
    else:
        import secrets
        token = secrets.token_urlsafe(32)
        supabase.table("calendar_sync_tokens").insert({
            "user_id": parent_id,
            "token": token,
            "student_id": str(student_id) if student_id else None
        }).execute()

    # Build iCal URL
    base_url = f"/api/v1/parent-portal/calendar/ical/{token}"
    if student_id:
        base_url += f"?student_id={student_id}"

    return {
        "ical_url": base_url,
        "instructions": {
            "google": "Go to Google Calendar > Settings > Add Calendar > From URL",
            "apple": "Go to Calendar > File > New Calendar Subscription",
            "outlook": "Go to Outlook > Add Calendar > Subscribe from web"
        }
    }


@router.get("/ical/{token}")
async def get_ical_feed(
    token: str,
    student_id: Optional[UUID] = None,
    supabase = Depends(get_supabase)
):
    """Get iCal feed (public endpoint with token auth)"""
    # Validate token
    token_record = supabase.table("calendar_sync_tokens").select(
        "user_id, student_id"
    ).eq("token", token).single().execute()

    if not token_record.data:
        raise HTTPException(status_code=401, detail="Invalid sync token")

    parent_id = token_record.data["user_id"]

    # Get events for next 90 days
    start_date = date.today()
    end_date = start_date + timedelta(days=90)

    # Get user for context
    user = supabase.table("user_profiles").select("school_id").eq(
        "id", parent_id
    ).single().execute()

    if not user.data:
        raise HTTPException(status_code=404, detail="User not found")

    # Build mock current_user for the events function
    mock_user = {
        "id": parent_id,
        "school_id": user.data["school_id"]
    }

    # Get events (simplified - in production would call the events endpoint)
    # For now, return iCal format structure
    ical_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//EduSMS//Parent Calendar//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:EduSMS School Calendar
"""

    # Get school events
    school_events = supabase.table("school_events").select("*").eq(
        "school_id", user.data["school_id"]
    ).gte("start_date", start_date.isoformat()).lte(
        "start_date", end_date.isoformat()
    ).execute()

    for event in (school_events.data or []):
        event_date = event["start_date"].replace("-", "")
        ical_content += f"""BEGIN:VEVENT
UID:{event['id']}@edusms
DTSTART;VALUE=DATE:{event_date}
SUMMARY:{event['title']}
DESCRIPTION:{event.get('description', '')}
END:VEVENT
"""

    ical_content += "END:VCALENDAR"

    from fastapi.responses import Response
    return Response(
        content=ical_content,
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=edusms-calendar.ics"}
    )


# ============================================================
# ACADEMIC CALENDAR
# ============================================================

@router.get("/academic-year")
async def get_academic_calendar(
    academic_year_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get academic year calendar with terms and holidays"""
    school_id = current_user.get("school_id")

    # Get current or specified academic year
    if academic_year_id:
        year = supabase.table("academic_years").select("*").eq(
            "id", str(academic_year_id)
        ).single().execute()
    else:
        year = supabase.table("academic_years").select("*").eq(
            "school_id", school_id
        ).eq("is_current", True).single().execute()

    if not year.data:
        return {"academic_year": None, "terms": [], "holidays": []}

    # Get terms
    terms = supabase.table("terms").select("*").eq(
        "academic_year_id", year.data["id"]
    ).order("start_date").execute()

    # Get holidays
    holidays = supabase.table("school_holidays").select("*").eq(
        "school_id", school_id
    ).gte("start_date", year.data["start_date"]).lte(
        "end_date", year.data["end_date"]
    ).order("start_date").execute()

    return {
        "academic_year": year.data,
        "terms": terms.data or [],
        "holidays": holidays.data or []
    }


# ============================================================
# UPCOMING SUMMARY
# ============================================================

@router.get("/upcoming")
async def get_upcoming_summary(
    days: int = Query(default=7, le=30),
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get summary of upcoming events for dashboard"""
    parent_id = current_user.get("id")
    school_id = current_user.get("school_id")

    start_date = date.today()
    end_date = start_date + timedelta(days=days)

    # Get parent's children
    relations = supabase.table("parent_student_relations").select(
        "student_id"
    ).eq("parent_id", parent_id).execute()

    student_ids = [r["student_id"] for r in (relations.data or [])]

    summary = {
        "assignments_due": 0,
        "fees_due": 0,
        "conferences": 0,
        "school_events": 0,
        "items": []
    }

    # Count assignments
    if student_ids:
        # Get class IDs
        students = supabase.table("students").select("class_id").in_(
            "id", student_ids
        ).execute()
        class_ids = [s["class_id"] for s in (students.data or []) if s.get("class_id")]

        if class_ids:
            assignments = supabase.table("assignments").select(
                "id, title, due_date"
            ).in_("class_id", class_ids).gte(
                "due_date", start_date.isoformat()
            ).lte("due_date", end_date.isoformat()).execute()

            summary["assignments_due"] = len(assignments.data or [])
            for a in (assignments.data or [])[:3]:
                summary["items"].append({
                    "type": "assignment",
                    "title": a["title"],
                    "date": a["due_date"]
                })

    # Count fees due
    if student_ids:
        fees = supabase.table("fee_records").select(
            "id, due_date, fee_types(name)"
        ).in_("student_id", student_ids).gte(
            "due_date", start_date.isoformat()
        ).lte("due_date", end_date.isoformat()).neq("status", "paid").execute()

        summary["fees_due"] = len(fees.data or [])
        for f in (fees.data or [])[:2]:
            summary["items"].append({
                "type": "fee",
                "title": f["fee_types"]["name"] if f.get("fee_types") else "Fee Due",
                "date": f["due_date"]
            })

    # Count conferences
    conferences = supabase.table("conference_bookings").select(
        "id, slot:slot_id(date, teacher:teacher_id(first_name, last_name))"
    ).eq("parent_id", parent_id).eq("status", "confirmed").execute()

    conf_count = 0
    for c in (conferences.data or []):
        if c.get("slot") and c["slot"].get("date"):
            if start_date.isoformat() <= c["slot"]["date"] <= end_date.isoformat():
                conf_count += 1
                teacher = c["slot"].get("teacher", {})
                summary["items"].append({
                    "type": "conference",
                    "title": f"Conference with {teacher.get('first_name', '')} {teacher.get('last_name', '')}",
                    "date": c["slot"]["date"]
                })

    summary["conferences"] = conf_count

    # Count school events
    events = supabase.table("school_events").select("id, title, start_date").eq(
        "school_id", school_id
    ).gte("start_date", start_date.isoformat()).lte(
        "start_date", end_date.isoformat()
    ).execute()

    summary["school_events"] = len(events.data or [])
    for e in (events.data or [])[:2]:
        summary["items"].append({
            "type": "event",
            "title": e["title"],
            "date": e["start_date"]
        })

    # Sort items by date
    summary["items"].sort(key=lambda x: x["date"])
    summary["items"] = summary["items"][:10]  # Limit to 10 items

    return summary
