from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.core.auth import get_current_user
from app.db.supabase import get_supabase_admin

router = APIRouter()


def _get_parent_student_ids(supabase, parent_id: str) -> list:
    """Helper to get student IDs linked to a parent."""
    guardians = supabase.table("guardians").select("student_id").eq("user_id", parent_id).execute()
    if not guardians.data:
        return []
    return [g["student_id"] for g in guardians.data]


def _get_subject_name(supabase, subject_id: str) -> str:
    """Helper to get subject name by ID."""
    result = supabase.table("subjects").select("name").eq("id", subject_id).single().execute()
    return result.data["name"] if result.data else "Unknown"


@router.get("/children/overview")
async def get_children_overview(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "parent":
        raise HTTPException(status_code=403, detail="Parent access required")

    supabase = get_supabase_admin()
    parent_id = current_user["id"]

    student_ids = _get_parent_student_ids(supabase, parent_id)
    if not student_ids:
        return []

    students = supabase.table("students").select("id, first_name, last_name, class_id").in_("id", student_ids).eq("status", "active").execute()

    children_data = []
    for student in students.data:
        # Get class info
        class_info = None
        if student.get("class_id"):
            class_info = supabase.table("classes").select("name, grade_id").eq("id", student["class_id"]).single().execute()

        # Attendance rate (last 30 days)
        thirty_days_ago = (datetime.now() - timedelta(days=30)).date().isoformat()
        attendance = supabase.table("attendance_records").select("status").eq("student_id", student["id"]).gte("date", thirty_days_ago).execute()
        present = sum(1 for r in attendance.data if r["status"] in ["present", "late"])
        attendance_rate = round((present / len(attendance.data) * 100), 1) if attendance.data else 0

        # Average grade
        grades = supabase.table("grade_entries").select("score, max_score").eq("student_id", student["id"]).execute()
        if grades.data:
            avg_grade = sum(float(g["score"]) / float(g["max_score"]) * 100 for g in grades.data) / len(grades.data)
            average_grade = round(avg_grade, 1)
        else:
            average_grade = 0

        # Pending assignments - real count from assignments table
        pending_assignments = 0
        if student.get("class_id"):
            today = datetime.now().date().isoformat()
            active_assignments = supabase.table("assignments").select("id").eq("class_id", student["class_id"]).eq("status", "active").gte("due_date", today).execute()
            if active_assignments.data:
                assignment_ids = [a["id"] for a in active_assignments.data]
                submissions = supabase.table("assignment_submissions").select("assignment_id").eq("student_id", student["id"]).in_("assignment_id", assignment_ids).execute()
                submitted_ids = {s["assignment_id"] for s in submissions.data} if submissions.data else set()
                pending_assignments = len(assignment_ids) - len(submitted_ids)

        # Outstanding fees
        invoices = supabase.table("invoices").select("amount, amount_paid").eq("student_id", student["id"]).in_("status", ["pending", "partial", "overdue"]).execute()
        outstanding = sum(float(i["amount"]) - float(i["amount_paid"]) for i in invoices.data)

        children_data.append({
            "name": f"{student['first_name']} {student['last_name']}",
            "class": class_info.data["name"] if class_info and class_info.data else "Unassigned",
            "attendance_rate": attendance_rate,
            "average_grade": average_grade,
            "pending_assignments": pending_assignments,
            "outstanding_fees": round(outstanding, 2),
            "student_id": student["id"]
        })

    return children_data


@router.get("/notifications")
async def get_notifications(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "parent":
        raise HTTPException(status_code=403, detail="Parent access required")

    supabase = get_supabase_admin()
    parent_id = current_user["id"]

    student_ids = _get_parent_student_ids(supabase, parent_id)
    if not student_ids:
        return []

    notifications = []

    for student_id in student_ids:
        # Get student name for context
        student = supabase.table("students").select("first_name, last_name, class_id").eq("id", student_id).single().execute()
        student_name = f"{student.data['first_name']}" if student.data else "Your child"

        # Check for overdue/upcoming fees
        invoices = supabase.table("invoices").select("amount, amount_paid, due_date, status, description").eq("student_id", student_id).in_("status", ["pending", "partial", "overdue"]).execute()
        for invoice in invoices.data:
            outstanding = float(invoice["amount"]) - float(invoice["amount_paid"])
            if outstanding > 0:
                if invoice["status"] == "overdue":
                    notifications.append({
                        "type": "fee_overdue",
                        "message": f"Overdue: {invoice.get('description', 'Fee')} for {student_name} (${outstanding:.2f})",
                        "priority": "high"
                    })
                else:
                    due_date = datetime.fromisoformat(invoice["due_date"].replace('Z', '+00:00')).date() if 'T' in str(invoice["due_date"]) else datetime.strptime(str(invoice["due_date"]), "%Y-%m-%d").date()
                    days_until = (due_date - datetime.now().date()).days
                    if days_until <= 7:
                        notifications.append({
                            "type": "fee_due",
                            "message": f"Fee due in {days_until} days for {student_name}: ${outstanding:.2f}",
                            "priority": "medium"
                        })

        # Check for overdue assignments
        if student.data and student.data.get("class_id"):
            today = datetime.now().date().isoformat()
            overdue_assignments = supabase.table("assignments").select("id, title, due_date, subject_id").eq("class_id", student.data["class_id"]).eq("status", "active").lt("due_date", today).execute()
            if overdue_assignments.data:
                assignment_ids = [a["id"] for a in overdue_assignments.data]
                submissions = supabase.table("assignment_submissions").select("assignment_id").eq("student_id", student_id).in_("assignment_id", assignment_ids).execute()
                submitted_ids = {s["assignment_id"] for s in submissions.data} if submissions.data else set()
                for assignment in overdue_assignments.data:
                    if assignment["id"] not in submitted_ids:
                        notifications.append({
                            "type": "assignment_overdue",
                            "message": f"Overdue assignment: {assignment['title']} for {student_name}",
                            "priority": "high"
                        })

        # Check for attendance issues (absent in last 7 days)
        seven_days_ago = (datetime.now() - timedelta(days=7)).date().isoformat()
        recent_absences = supabase.table("attendance_records").select("date").eq("student_id", student_id).eq("status", "absent").gte("date", seven_days_ago).execute()
        if len(recent_absences.data) >= 2:
            notifications.append({
                "type": "attendance_warning",
                "message": f"{student_name} has been absent {len(recent_absences.data)} times this week",
                "priority": "medium"
            })

        # Check for discipline incidents (unacknowledged)
        incidents = supabase.table("discipline_incidents").select("category, incident_date").eq("student_id", student_id).eq("parent_acknowledged", False).execute()
        for incident in incidents.data:
            notifications.append({
                "type": "discipline",
                "message": f"Discipline notice for {student_name}: {incident['category']}",
                "priority": "high"
            })

    # Sort by priority (high first)
    priority_order = {"high": 0, "medium": 1, "low": 2}
    notifications.sort(key=lambda n: priority_order.get(n.get("priority", "low"), 2))

    return notifications[:15]


@router.get("/fees/summary")
async def get_fees_summary(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "parent":
        raise HTTPException(status_code=403, detail="Parent access required")

    supabase = get_supabase_admin()
    parent_id = current_user["id"]

    student_ids = _get_parent_student_ids(supabase, parent_id)
    if not student_ids:
        return []

    students = supabase.table("students").select("id, first_name, last_name").in_("id", student_ids).execute()
    student_map = {s["id"]: f"{s['first_name']} {s['last_name']}" for s in students.data}

    fees_data = []
    for student_id in student_ids:
        invoices = supabase.table("invoices").select("invoice_number, amount, amount_paid, due_date, description, status").eq("student_id", student_id).in_("status", ["pending", "partial", "overdue"]).order("due_date").execute()

        for invoice in invoices.data:
            outstanding = float(invoice["amount"]) - float(invoice["amount_paid"])
            if outstanding > 0:
                fees_data.append({
                    "item": f"{invoice.get('description', 'Tuition')} - {student_map.get(student_id, 'Student')}",
                    "amount": round(outstanding, 2),
                    "due_date": invoice["due_date"],
                    "invoice_id": invoice["invoice_number"],
                    "status": invoice["status"]
                })

    return fees_data


@router.get("/academic/progress")
async def get_academic_progress(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "parent":
        raise HTTPException(status_code=403, detail="Parent access required")

    supabase = get_supabase_admin()
    parent_id = current_user["id"]

    student_ids = _get_parent_student_ids(supabase, parent_id)
    if not student_ids:
        return []

    students = supabase.table("students").select("id, first_name, last_name").in_("id", student_ids).execute()

    progress_data = []
    for student in students.data:
        # Recent grades with subject names
        grades = supabase.table("grade_entries").select("score, max_score, subject_id, assessment_type, created_at").eq("student_id", student["id"]).order("created_at", desc=True).limit(5).execute()

        # Build subject name cache
        subject_ids = list({g["subject_id"] for g in grades.data})
        subject_names = {}
        if subject_ids:
            subjects = supabase.table("subjects").select("id, name").in_("id", subject_ids).execute()
            subject_names = {s["id"]: s["name"] for s in subjects.data}

        recent_grades = []
        for grade in grades.data:
            percentage = round(float(grade["score"]) / float(grade["max_score"]) * 100, 1)
            recent_grades.append({
                "subject": subject_names.get(grade["subject_id"], "Unknown"),
                "assessment": grade.get("assessment_type", "Assessment"),
                "score": percentage
            })

        # Calculate trend: compare last 30 days avg vs previous 30 days avg
        thirty_days_ago = (datetime.now() - timedelta(days=30)).date().isoformat()
        sixty_days_ago = (datetime.now() - timedelta(days=60)).date().isoformat()

        recent_entries = supabase.table("grade_entries").select("score, max_score, created_at").eq("student_id", student["id"]).gte("created_at", thirty_days_ago).execute()
        older_entries = supabase.table("grade_entries").select("score, max_score, created_at").eq("student_id", student["id"]).gte("created_at", sixty_days_ago).lt("created_at", thirty_days_ago).execute()

        recent_avg = (sum(float(g["score"]) / float(g["max_score"]) * 100 for g in recent_entries.data) / len(recent_entries.data)) if recent_entries.data else 0
        older_avg = (sum(float(g["score"]) / float(g["max_score"]) * 100 for g in older_entries.data) / len(older_entries.data)) if older_entries.data else 0

        if not older_entries.data:
            trend = "stable"
        elif recent_avg > older_avg + 3:
            trend = "improving"
        elif recent_avg < older_avg - 3:
            trend = "declining"
        else:
            trend = "stable"

        # Attendance trend
        attendance = supabase.table("attendance_records").select("status").eq("student_id", student["id"]).gte("date", thirty_days_ago).execute()
        present = sum(1 for r in attendance.data if r["status"] in ["present", "late"])
        attendance_rate = round((present / len(attendance.data) * 100), 1) if attendance.data else 0

        progress_data.append({
            "name": f"{student['first_name']} {student['last_name']}",
            "student_id": student["id"],
            "trend": trend,
            "recent_grades": recent_grades,
            "attendance_trend": attendance_rate
        })

    return progress_data


@router.get("/announcements")
async def get_announcements(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "parent":
        raise HTTPException(status_code=403, detail="Parent access required")

    supabase = get_supabase_admin()
    school_id = current_user.get("school_id")

    now = datetime.now().isoformat()

    result = supabase.table("announcements").select("id, title, content, audience, priority, published_at").eq("school_id", school_id).in_("audience", ["all", "parents"]).lte("published_at", now).order("published_at", desc=True).limit(10).execute()

    # Filter out expired
    announcements = []
    for a in result.data:
        announcements.append({
            "id": a["id"],
            "title": a["title"],
            "content": a["content"],
            "priority": a.get("priority", "normal"),
            "date": a.get("published_at")
        })

    return announcements


def _verify_parent_owns_student(supabase, parent_id: str, student_id: str):
    """Verify that a student is linked to this parent via guardians table."""
    result = supabase.table("guardians").select("id").eq("user_id", parent_id).eq("student_id", student_id).execute()
    if not result.data:
        raise HTTPException(status_code=403, detail="This student is not linked to your account")


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


@router.get("/children/{student_id}/schedule/today")
async def get_child_schedule_today(student_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "parent":
        raise HTTPException(status_code=403, detail="Parent access required")

    supabase = get_supabase_admin()
    _verify_parent_owns_student(supabase, current_user["id"], student_id)

    student = supabase.table("students").select("id, class_id").eq("id", student_id).eq("status", "active").single().execute()
    if not student.data or not student.data.get("class_id"):
        return []

    today_dow = datetime.now().weekday()
    slots = supabase.table("timetable_slots").select(
        "start_time, end_time, subject_id, teacher_id, room"
    ).eq("class_id", student.data["class_id"]).eq("day_of_week", today_dow).order("start_time").execute()

    if not slots.data:
        return []

    subject_ids = {s["subject_id"] for s in slots.data}
    teacher_ids = {s["teacher_id"] for s in slots.data if s.get("teacher_id")}
    subject_map = _build_subject_map(supabase, list(subject_ids))
    teacher_map = _build_teacher_map(supabase, list(teacher_ids))

    schedule = []
    for slot in slots.data:
        start = str(slot["start_time"])[:5]
        schedule.append({
            "time": start,
            "subject": subject_map.get(slot["subject_id"], "Unknown"),
            "teacher": teacher_map.get(slot.get("teacher_id"), "TBA"),
            "room": slot.get("room", "TBA"),
        })

    return schedule


@router.get("/children/{student_id}/assignments")
async def get_child_assignments(student_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "parent":
        raise HTTPException(status_code=403, detail="Parent access required")

    supabase = get_supabase_admin()
    _verify_parent_owns_student(supabase, current_user["id"], student_id)

    student = supabase.table("students").select("id, class_id").eq("id", student_id).eq("status", "active").single().execute()
    if not student.data or not student.data.get("class_id"):
        return []

    today = datetime.now().date().isoformat()
    seven_days = (datetime.now() + timedelta(days=7)).date().isoformat()

    assignments = supabase.table("assignments").select(
        "id, title, subject_id, due_date"
    ).eq("class_id", student.data["class_id"]).eq("status", "active").gte("due_date", today).lte("due_date", seven_days).order("due_date").execute()

    if not assignments.data:
        return []

    assignment_ids = [a["id"] for a in assignments.data]
    submissions = supabase.table("assignment_submissions").select("assignment_id").eq("student_id", student_id).in_("assignment_id", assignment_ids).execute()
    submitted_ids = {s["assignment_id"] for s in submissions.data} if submissions.data else set()

    subject_ids = {a["subject_id"] for a in assignments.data}
    subject_map = _build_subject_map(supabase, list(subject_ids))

    tasks = []
    for a in assignments.data:
        if a["id"] in submitted_ids:
            continue
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
        })

    return tasks


@router.get("/children/{student_id}/subjects")
async def get_child_subject_performance(student_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "parent":
        raise HTTPException(status_code=403, detail="Parent access required")

    supabase = get_supabase_admin()
    _verify_parent_owns_student(supabase, current_user["id"], student_id)

    grades = supabase.table("grade_entries").select("score, max_score, subject_id").eq("student_id", student_id).execute()
    if not grades.data:
        return []

    subject_scores = {}
    for grade in grades.data:
        subject_id = grade["subject_id"]
        percentage = float(grade["score"]) / float(grade["max_score"]) * 100
        if subject_id not in subject_scores:
            subject_scores[subject_id] = []
        subject_scores[subject_id].append(percentage)

    subject_map = _build_subject_map(supabase, list(subject_scores.keys()))

    subject_performance = []
    for subject_id, scores in subject_scores.items():
        avg = round(sum(scores) / len(scores), 1)
        subject_performance.append({
            "subject": subject_map.get(subject_id, "Unknown"),
            "percentage": avg,
        })

    subject_performance.sort(key=lambda x: x["subject"])
    return subject_performance


@router.get("/children/{student_id}/grades/recent")
async def get_child_recent_grades(student_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "parent":
        raise HTTPException(status_code=403, detail="Parent access required")

    supabase = get_supabase_admin()
    _verify_parent_owns_student(supabase, current_user["id"], student_id)

    grades = supabase.table("grade_entries").select(
        "assessment_type, score, max_score, subject_id, created_at"
    ).eq("student_id", student_id).order("created_at", desc=True).limit(10).execute()

    if not grades.data:
        return []

    subject_ids = {g["subject_id"] for g in grades.data}
    subject_map = _build_subject_map(supabase, list(subject_ids))

    recent = []
    for grade in grades.data:
        percentage = round(float(grade["score"]) / float(grade["max_score"]) * 100, 1)
        recent.append({
            "assignment": grade.get("assessment_type", "Assessment"),
            "subject": subject_map.get(grade["subject_id"], "Unknown"),
            "score": percentage,
        })

    return recent
