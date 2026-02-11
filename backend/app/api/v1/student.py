from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.core.auth import get_current_user
from app.db.supabase_client import get_supabase_client

router = APIRouter()

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _get_student_record(supabase, user_id: str):
    """Get the student record linked to a user account."""
    result = supabase.table("students").select("id, class_id, first_name, last_name, school_id").eq("user_id", user_id).eq("status", "active").single().execute()
    return result.data if result.data else None


def _build_subject_map(supabase, subject_ids: list) -> dict:
    """Build a subject_id -> name mapping."""
    if not subject_ids:
        return {}
    subjects = supabase.table("subjects").select("id, name").in_("id", list(subject_ids)).execute()
    return {s["id"]: s["name"] for s in subjects.data}


def _build_teacher_map(supabase, teacher_ids: list) -> dict:
    """Build a teacher_id -> name mapping."""
    if not teacher_ids:
        return {}
    teachers = supabase.table("user_profiles").select("id, first_name, last_name").in_("id", list(teacher_ids)).execute()
    return {t["id"]: f"{t['first_name']} {t['last_name']}" for t in teachers.data}


@router.get("/schedule/today")
async def get_today_schedule(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="Student access required")

    supabase = get_supabase_client()
    student = _get_student_record(supabase, current_user["id"])
    if not student or not student.get("class_id"):
        return []

    # Get today's day of week (Monday=0)
    today_dow = datetime.now().weekday()

    slots = supabase.table("timetable_slots").select(
        "start_time, end_time, subject_id, teacher_id, room"
    ).eq("class_id", student["class_id"]).eq("day_of_week", today_dow).order("start_time").execute()

    if not slots.data:
        return []

    # Build lookup maps
    subject_ids = {s["subject_id"] for s in slots.data}
    teacher_ids = {s["teacher_id"] for s in slots.data if s.get("teacher_id")}
    subject_map = _build_subject_map(supabase, list(subject_ids))
    teacher_map = _build_teacher_map(supabase, list(teacher_ids))

    schedule = []
    for slot in slots.data:
        # Format time (handle both TIME and string formats)
        start = str(slot["start_time"])[:5]  # "08:00:00" -> "08:00"
        schedule.append({
            "time": start,
            "subject": subject_map.get(slot["subject_id"], "Unknown"),
            "teacher": teacher_map.get(slot.get("teacher_id"), "TBA"),
            "room": slot.get("room", "TBA"),
            "subject_id": slot["subject_id"]
        })

    return schedule


@router.get("/assignments/today")
async def get_today_assignments(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="Student access required")

    supabase = get_supabase_client()
    student = _get_student_record(supabase, current_user["id"])
    if not student or not student.get("class_id"):
        return []

    today = datetime.now().date().isoformat()
    # Get assignments due today or in the next 7 days that haven't been submitted
    seven_days = (datetime.now() + timedelta(days=7)).date().isoformat()

    assignments = supabase.table("assignments").select(
        "id, title, subject_id, due_date"
    ).eq("class_id", student["class_id"]).eq("status", "active").gte("due_date", today).lte("due_date", seven_days).order("due_date").execute()

    if not assignments.data:
        return []

    # Check which are already submitted
    assignment_ids = [a["id"] for a in assignments.data]
    submissions = supabase.table("assignment_submissions").select("assignment_id").eq("student_id", student["id"]).in_("assignment_id", assignment_ids).execute()
    submitted_ids = {s["assignment_id"] for s in submissions.data} if submissions.data else set()

    # Build subject map
    subject_ids = {a["subject_id"] for a in assignments.data}
    subject_map = _build_subject_map(supabase, list(subject_ids))

    tasks = []
    for a in assignments.data:
        if a["id"] in submitted_ids:
            continue

        # Format due date relative to today
        due = a["due_date"]
        if due == today:
            due_label = "Today"
        elif due == (datetime.now() + timedelta(days=1)).date().isoformat():
            due_label = "Tomorrow"
        else:
            due_label = due

        tasks.append({
            "task": a["title"],
            "subject": subject_map.get(a["subject_id"], "Unknown"),
            "due": due_label,
            "due_date": a["due_date"],
            "assignment_id": a["id"]
        })

    return tasks


@router.get("/performance/overview")
async def get_performance_overview(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="Student access required")

    supabase = get_supabase_client()
    student = _get_student_record(supabase, current_user["id"])
    if not student:
        return {"attendance_rate": 0, "overall_average": 0, "subjects_below_70": 0}

    student_record_id = student["id"]

    # Attendance rate (last 30 days)
    thirty_days_ago = (datetime.now() - timedelta(days=30)).date().isoformat()
    attendance = supabase.table("attendance_records").select("status").eq("student_id", student_record_id).gte("date", thirty_days_ago).execute()
    present = sum(1 for r in attendance.data if r["status"] in ["present", "late"])
    attendance_rate = round((present / len(attendance.data) * 100), 1) if attendance.data else 0

    # Overall average
    grades = supabase.table("grade_entries").select("score, max_score, subject_id").eq("student_id", student_record_id).execute()
    if grades.data:
        avg = sum(float(g["score"]) / float(g["max_score"]) * 100 for g in grades.data) / len(grades.data)
        overall_average = round(avg, 1)
    else:
        overall_average = 0

    # Subjects below 70% - group by subject first
    subject_scores = {}
    for g in grades.data:
        sid = g["subject_id"]
        pct = float(g["score"]) / float(g["max_score"]) * 100
        if sid not in subject_scores:
            subject_scores[sid] = []
        subject_scores[sid].append(pct)

    subjects_below_70 = sum(1 for scores in subject_scores.values() if (sum(scores) / len(scores)) < 70)

    return {
        "attendance_rate": attendance_rate,
        "overall_average": overall_average,
        "subjects_below_70": subjects_below_70
    }


@router.get("/grades/recent")
async def get_recent_grades(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="Student access required")

    supabase = get_supabase_client()
    student = _get_student_record(supabase, current_user["id"])
    if not student:
        return []

    # Recent grades
    grades = supabase.table("grade_entries").select(
        "assessment_type, score, max_score, subject_id, created_at"
    ).eq("student_id", student["id"]).order("created_at", desc=True).limit(10).execute()

    if not grades.data:
        return []

    # Build subject map
    subject_ids = {g["subject_id"] for g in grades.data}
    subject_map = _build_subject_map(supabase, list(subject_ids))

    recent = []
    for grade in grades.data:
        percentage = round(float(grade["score"]) / float(grade["max_score"]) * 100, 1)
        recent.append({
            "assignment": grade.get("assessment_type", "Assessment"),
            "subject": subject_map.get(grade["subject_id"], "Unknown"),
            "score": percentage
        })

    return recent


@router.get("/performance/subjects")
async def get_subject_performance(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="Student access required")

    supabase = get_supabase_client()
    student = _get_student_record(supabase, current_user["id"])
    if not student:
        return []

    # Get grades by subject
    grades = supabase.table("grade_entries").select("score, max_score, subject_id").eq("student_id", student["id"]).execute()
    if not grades.data:
        return []

    # Group by subject
    subject_scores = {}
    for grade in grades.data:
        subject_id = grade["subject_id"]
        percentage = float(grade["score"]) / float(grade["max_score"]) * 100
        if subject_id not in subject_scores:
            subject_scores[subject_id] = []
        subject_scores[subject_id].append(percentage)

    # Build subject map
    subject_map = _build_subject_map(supabase, list(subject_scores.keys()))

    # Calculate averages
    subject_performance = []
    for subject_id, scores in subject_scores.items():
        avg = round(sum(scores) / len(scores), 1)
        subject_performance.append({
            "subject": subject_map.get(subject_id, "Unknown"),
            "percentage": avg,
            "subject_id": subject_id
        })

    # Sort by subject name
    subject_performance.sort(key=lambda x: x["subject"])
    return subject_performance


@router.get("/alerts")
async def get_student_alerts(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="Student access required")

    supabase = get_supabase_client()
    student = _get_student_record(supabase, current_user["id"])
    if not student:
        return []

    alerts = []

    # Check for assignments due tomorrow or today
    today = datetime.now().date().isoformat()
    tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()

    if student.get("class_id"):
        urgent_assignments = supabase.table("assignments").select(
            "id, title, due_date"
        ).eq("class_id", student["class_id"]).eq("status", "active").lte("due_date", tomorrow).gte("due_date", today).execute()

        if urgent_assignments.data:
            assignment_ids = [a["id"] for a in urgent_assignments.data]
            submissions = supabase.table("assignment_submissions").select("assignment_id").eq("student_id", student["id"]).in_("assignment_id", assignment_ids).execute()
            submitted_ids = {s["assignment_id"] for s in submissions.data} if submissions.data else set()

            for a in urgent_assignments.data:
                if a["id"] not in submitted_ids:
                    due_label = "today" if a["due_date"] == today else "tomorrow"
                    alerts.append({
                        "type": "assignment",
                        "message": f"Assignment due {due_label}: {a['title']}",
                        "priority": "high" if a["due_date"] == today else "medium"
                    })

        # Check for overdue assignments
        overdue = supabase.table("assignments").select("id, title").eq("class_id", student["class_id"]).eq("status", "active").lt("due_date", today).execute()
        if overdue.data:
            overdue_ids = [a["id"] for a in overdue.data]
            submissions = supabase.table("assignment_submissions").select("assignment_id").eq("student_id", student["id"]).in_("assignment_id", overdue_ids).execute()
            submitted_ids = {s["assignment_id"] for s in submissions.data} if submissions.data else set()
            for a in overdue.data:
                if a["id"] not in submitted_ids:
                    alerts.append({
                        "type": "overdue",
                        "message": f"Overdue: {a['title']}",
                        "priority": "high"
                    })

    # Attendance warning
    thirty_days_ago = (datetime.now() - timedelta(days=30)).date().isoformat()
    attendance = supabase.table("attendance_records").select("status").eq("student_id", student["id"]).gte("date", thirty_days_ago).execute()
    if attendance.data:
        absent_count = sum(1 for r in attendance.data if r["status"] == "absent")
        total = len(attendance.data)
        rate = (total - absent_count) / total * 100 if total else 100
        if rate < 85:
            alerts.append({
                "type": "attendance",
                "message": f"Attendance warning: {round(rate, 1)}% (below 85% threshold)",
                "priority": "high"
            })

    # Check for recent announcements (last 3 days)
    three_days_ago = (datetime.now() - timedelta(days=3)).isoformat()
    school_id = student.get("school_id")
    if school_id:
        announcements = supabase.table("announcements").select("title").eq("school_id", school_id).in_("audience", ["all", "students"]).gte("published_at", three_days_ago).execute()
        for ann in announcements.data[:3]:
            alerts.append({
                "type": "announcement",
                "message": f"New: {ann['title']}",
                "priority": "low"
            })

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    alerts.sort(key=lambda a: priority_order.get(a.get("priority", "low"), 2))

    return alerts[:10]
