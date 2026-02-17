"""
EduCore Backend - Principal Analytics API
Advanced analytics and reporting for school leadership
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
# ACADEMIC ANALYTICS
# ============================================================

@router.get("/academic/overview")
async def get_academic_overview(
    academic_year_id: Optional[UUID] = None,
    term_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get comprehensive academic overview"""
    school_id = current_user.get("school_id")

    # Get grade distributions
    grades_query = supabase.table("grades").select(
        "score, subject_id, class_id"
    ).eq("school_id", school_id)

    if academic_year_id:
        grades_query = grades_query.eq("academic_year_id", str(academic_year_id))
    if term_id:
        grades_query = grades_query.eq("term_id", str(term_id))

    grades_result = grades_query.execute()
    grades = grades_result.data or []

    # Calculate statistics
    if grades:
        scores = [g["score"] for g in grades if g.get("score") is not None]
        avg_score = sum(scores) / len(scores) if scores else 0

        # Grade distribution
        distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        for score in scores:
            if score >= 90:
                distribution["A"] += 1
            elif score >= 80:
                distribution["B"] += 1
            elif score >= 70:
                distribution["C"] += 1
            elif score >= 60:
                distribution["D"] += 1
            else:
                distribution["F"] += 1

        # By subject
        by_subject = defaultdict(list)
        for g in grades:
            if g.get("score") is not None:
                by_subject[g.get("subject_id")].append(g["score"])

        subject_averages = {
            sid: sum(scores) / len(scores)
            for sid, scores in by_subject.items()
        }
    else:
        avg_score = 0
        distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        subject_averages = {}

    # Get pass/fail rates
    total_grades = len(grades)
    passing = sum(1 for g in grades if g.get("score", 0) >= 60)

    return {
        "total_grades_recorded": total_grades,
        "average_score": round(avg_score, 2),
        "passing_rate": round((passing / total_grades) * 100, 2) if total_grades > 0 else 0,
        "grade_distribution": distribution,
        "subject_averages": subject_averages,
        "students_above_average": sum(1 for g in grades if g.get("score", 0) >= avg_score),
        "students_below_average": sum(1 for g in grades if g.get("score", 0) < avg_score)
    }


@router.get("/academic/trends")
async def get_academic_trends(
    subject_id: Optional[UUID] = None,
    grade_id: Optional[UUID] = None,
    periods: int = 6,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get academic performance trends over time"""
    school_id = current_user.get("school_id")

    # Get terms for trend analysis
    terms_result = supabase.table("terms").select(
        "id, name, start_date"
    ).eq("school_id", school_id).order("start_date", desc=True).limit(periods).execute()

    terms = terms_result.data or []
    trends = []

    for term in reversed(terms):
        query = supabase.table("grades").select("score").eq(
            "school_id", school_id
        ).eq("term_id", term["id"])

        if subject_id:
            query = query.eq("subject_id", str(subject_id))
        if grade_id:
            query = query.eq("grade_id", str(grade_id))

        result = query.execute()
        scores = [g["score"] for g in (result.data or []) if g.get("score") is not None]

        trends.append({
            "term_id": term["id"],
            "term_name": term["name"],
            "average_score": round(sum(scores) / len(scores), 2) if scores else 0,
            "total_grades": len(scores),
            "passing_rate": round(sum(1 for s in scores if s >= 60) / len(scores) * 100, 2) if scores else 0
        })

    return {"trends": trends}


@router.get("/academic/class-comparison")
async def compare_class_performance(
    subject_id: Optional[UUID] = None,
    term_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Compare performance across classes"""
    school_id = current_user.get("school_id")

    query = supabase.table("grades").select(
        "score, class_id, classes(name)"
    ).eq("school_id", school_id)

    if subject_id:
        query = query.eq("subject_id", str(subject_id))
    if term_id:
        query = query.eq("term_id", str(term_id))

    result = query.execute()
    grades = result.data or []

    # Group by class
    by_class = defaultdict(list)
    class_names = {}
    for g in grades:
        if g.get("score") is not None:
            class_id = g.get("class_id")
            by_class[class_id].append(g["score"])
            if g.get("classes"):
                class_names[class_id] = g["classes"]["name"]

    comparisons = []
    for class_id, scores in by_class.items():
        comparisons.append({
            "class_id": class_id,
            "class_name": class_names.get(class_id, "Unknown"),
            "student_count": len(scores),
            "average_score": round(sum(scores) / len(scores), 2),
            "highest_score": max(scores),
            "lowest_score": min(scores),
            "passing_rate": round(sum(1 for s in scores if s >= 60) / len(scores) * 100, 2)
        })

    comparisons.sort(key=lambda x: x["average_score"], reverse=True)

    return {"comparisons": comparisons}


@router.get("/academic/teacher-effectiveness")
async def get_teacher_effectiveness(
    subject_id: Optional[UUID] = None,
    academic_year_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Analyze teacher effectiveness metrics"""
    school_id = current_user.get("school_id")

    # Get class assignments
    assignments = supabase.table("class_subjects").select(
        "teacher_id, class_id, subject_id, teachers(first_name, last_name)"
    ).eq("school_id", school_id).execute()

    teacher_classes = defaultdict(list)
    teacher_names = {}
    for a in (assignments.data or []):
        teacher_id = a.get("teacher_id")
        if teacher_id:
            teacher_classes[teacher_id].append({
                "class_id": a["class_id"],
                "subject_id": a["subject_id"]
            })
            if a.get("teachers"):
                teacher_names[teacher_id] = f"{a['teachers']['first_name']} {a['teachers']['last_name']}"

    # Get grades for each teacher's classes
    effectiveness = []
    for teacher_id, classes in teacher_classes.items():
        all_scores = []
        for cls in classes:
            query = supabase.table("grades").select("score").eq(
                "class_id", cls["class_id"]
            ).eq("subject_id", cls["subject_id"])

            if academic_year_id:
                query = query.eq("academic_year_id", str(academic_year_id))

            result = query.execute()
            scores = [g["score"] for g in (result.data or []) if g.get("score") is not None]
            all_scores.extend(scores)

        if all_scores:
            effectiveness.append({
                "teacher_id": teacher_id,
                "teacher_name": teacher_names.get(teacher_id, "Unknown"),
                "classes_taught": len(classes),
                "students_graded": len(all_scores),
                "average_score": round(sum(all_scores) / len(all_scores), 2),
                "passing_rate": round(sum(1 for s in all_scores if s >= 60) / len(all_scores) * 100, 2),
                "grade_a_rate": round(sum(1 for s in all_scores if s >= 90) / len(all_scores) * 100, 2)
            })

    effectiveness.sort(key=lambda x: x["average_score"], reverse=True)

    return {"teacher_effectiveness": effectiveness}


# ============================================================
# ATTENDANCE ANALYTICS
# ============================================================

@router.get("/attendance/overview")
async def get_attendance_overview(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get attendance overview statistics"""
    school_id = current_user.get("school_id")

    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()

    result = supabase.table("attendance").select(
        "status, date, student_id"
    ).eq("school_id", school_id).gte(
        "date", start_date.isoformat()
    ).lte("date", end_date.isoformat()).execute()

    records = result.data or []

    # Calculate statistics
    total = len(records)
    by_status = defaultdict(int)
    for r in records:
        by_status[r.get("status", "unknown")] += 1

    # Unique students
    unique_students = len(set(r["student_id"] for r in records))

    # Daily breakdown
    by_date = defaultdict(lambda: {"present": 0, "absent": 0, "late": 0, "excused": 0})
    for r in records:
        d = r.get("date")
        status = r.get("status", "unknown")
        if status in by_date[d]:
            by_date[d][status] += 1

    daily_rates = []
    for d, counts in sorted(by_date.items()):
        day_total = sum(counts.values())
        daily_rates.append({
            "date": d,
            "attendance_rate": round(counts["present"] / day_total * 100, 2) if day_total > 0 else 0,
            **counts
        })

    present = by_status.get("present", 0)
    attendance_rate = round((present / total) * 100, 2) if total > 0 else 0

    return {
        "total_records": total,
        "unique_students": unique_students,
        "overall_attendance_rate": attendance_rate,
        "by_status": dict(by_status),
        "chronic_absence_threshold": 10,  # 10% or more
        "daily_breakdown": daily_rates[-14:]  # Last 14 days
    }


@router.get("/attendance/chronic-absence")
async def get_chronic_absentees(
    threshold_percent: float = 10.0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get students with chronic absenteeism"""
    school_id = current_user.get("school_id")

    # Get attendance for current term/year
    result = supabase.table("attendance").select(
        "student_id, status, students(first_name, last_name, class_id)"
    ).eq("school_id", school_id).execute()

    records = result.data or []

    # Calculate per student
    student_attendance = defaultdict(lambda: {"present": 0, "absent": 0, "total": 0, "info": None})
    for r in records:
        sid = r.get("student_id")
        student_attendance[sid]["total"] += 1
        if r.get("status") == "present":
            student_attendance[sid]["present"] += 1
        elif r.get("status") in ["absent", "unexcused"]:
            student_attendance[sid]["absent"] += 1
        if r.get("students") and not student_attendance[sid]["info"]:
            student_attendance[sid]["info"] = r["students"]

    chronic = []
    for sid, data in student_attendance.items():
        if data["total"] > 0:
            absence_rate = (data["absent"] / data["total"]) * 100
            if absence_rate >= threshold_percent:
                chronic.append({
                    "student_id": sid,
                    "student_name": f"{data['info']['first_name']} {data['info']['last_name']}" if data["info"] else "Unknown",
                    "class_id": data["info"]["class_id"] if data["info"] else None,
                    "total_days": data["total"],
                    "days_absent": data["absent"],
                    "absence_rate": round(absence_rate, 2)
                })

    chronic.sort(key=lambda x: x["absence_rate"], reverse=True)

    return {
        "threshold_percent": threshold_percent,
        "chronic_absentees": chronic,
        "total_identified": len(chronic)
    }


@router.get("/attendance/by-class")
async def get_attendance_by_class(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get attendance rates by class"""
    school_id = current_user.get("school_id")

    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()

    result = supabase.table("attendance").select(
        "status, students(class_id, classes(name))"
    ).eq("school_id", school_id).gte(
        "date", start_date.isoformat()
    ).lte("date", end_date.isoformat()).execute()

    records = result.data or []

    by_class = defaultdict(lambda: {"present": 0, "total": 0, "name": ""})
    for r in records:
        if r.get("students") and r["students"].get("class_id"):
            class_id = r["students"]["class_id"]
            by_class[class_id]["total"] += 1
            if r.get("status") == "present":
                by_class[class_id]["present"] += 1
            if r["students"].get("classes"):
                by_class[class_id]["name"] = r["students"]["classes"]["name"]

    class_rates = []
    for class_id, data in by_class.items():
        class_rates.append({
            "class_id": class_id,
            "class_name": data["name"],
            "total_records": data["total"],
            "attendance_rate": round(data["present"] / data["total"] * 100, 2) if data["total"] > 0 else 0
        })

    class_rates.sort(key=lambda x: x["attendance_rate"], reverse=True)

    return {"class_attendance": class_rates}


# ============================================================
# ENROLLMENT ANALYTICS
# ============================================================

@router.get("/enrollment/overview")
async def get_enrollment_overview(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get enrollment overview"""
    school_id = current_user.get("school_id")

    # Current enrollment
    students = supabase.table("students").select(
        "id, status, grade_id, gender, enrollment_date, grades(name)"
    ).eq("school_id", school_id).execute()

    all_students = students.data or []
    active_students = [s for s in all_students if s.get("status") == "active"]

    # By grade
    by_grade = defaultdict(int)
    grade_names = {}
    for s in active_students:
        grade_id = s.get("grade_id")
        by_grade[grade_id] += 1
        if s.get("grades"):
            grade_names[grade_id] = s["grades"]["name"]

    # By gender
    by_gender = defaultdict(int)
    for s in active_students:
        by_gender[s.get("gender", "unknown")] += 1

    # New enrollments this month
    first_of_month = date.today().replace(day=1)
    new_this_month = sum(
        1 for s in all_students
        if s.get("enrollment_date") and s["enrollment_date"] >= first_of_month.isoformat()
    )

    return {
        "total_active": len(active_students),
        "total_all_statuses": len(all_students),
        "by_grade": [
            {"grade_id": gid, "grade_name": grade_names.get(gid, "Unknown"), "count": count}
            for gid, count in sorted(by_grade.items(), key=lambda x: x[1], reverse=True)
        ],
        "by_gender": dict(by_gender),
        "new_this_month": new_this_month
    }


@router.get("/enrollment/trends")
async def get_enrollment_trends(
    years: int = 5,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get enrollment trends over years"""
    school_id = current_user.get("school_id")

    result = supabase.table("students").select(
        "enrollment_date, status"
    ).eq("school_id", school_id).execute()

    students = result.data or []

    # Group by year
    current_year = date.today().year
    by_year = defaultdict(lambda: {"enrolled": 0, "active": 0})

    for s in students:
        if s.get("enrollment_date"):
            year = int(s["enrollment_date"][:4])
            if year >= current_year - years:
                by_year[year]["enrolled"] += 1

    # Calculate cumulative active
    trends = []
    for year in range(current_year - years + 1, current_year + 1):
        trends.append({
            "year": year,
            "new_enrollments": by_year[year]["enrolled"],
            "total_enrolled": sum(by_year[y]["enrolled"] for y in range(current_year - years + 1, year + 1))
        })

    return {"trends": trends}


# ============================================================
# FINANCIAL ANALYTICS
# ============================================================

@router.get("/financial/overview")
async def get_financial_overview(
    academic_year_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get financial overview"""
    school_id = current_user.get("school_id")

    # Get fee records
    fees_query = supabase.table("fee_records").select(
        "amount, amount_paid, status"
    ).eq("school_id", school_id)

    if academic_year_id:
        fees_query = fees_query.eq("academic_year_id", str(academic_year_id))

    fees_result = fees_query.execute()
    fees = fees_result.data or []

    total_billed = sum(f.get("amount", 0) for f in fees)
    total_collected = sum(f.get("amount_paid", 0) for f in fees)
    outstanding = total_billed - total_collected

    by_status = defaultdict(lambda: {"count": 0, "amount": 0})
    for f in fees:
        status = f.get("status", "unknown")
        by_status[status]["count"] += 1
        by_status[status]["amount"] += f.get("amount", 0)

    return {
        "total_billed": total_billed,
        "total_collected": total_collected,
        "outstanding_balance": outstanding,
        "collection_rate": round((total_collected / total_billed) * 100, 2) if total_billed > 0 else 0,
        "by_status": dict(by_status),
        "total_fee_records": len(fees)
    }


@router.get("/financial/collection-trends")
async def get_collection_trends(
    months: int = 12,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get fee collection trends"""
    school_id = current_user.get("school_id")

    start_date = date.today() - timedelta(days=months * 30)

    result = supabase.table("payments").select(
        "amount, payment_date"
    ).eq("school_id", school_id).gte(
        "payment_date", start_date.isoformat()
    ).execute()

    payments = result.data or []

    # Group by month
    by_month = defaultdict(float)
    for p in payments:
        if p.get("payment_date"):
            month_key = p["payment_date"][:7]  # YYYY-MM
            by_month[month_key] += p.get("amount", 0)

    trends = [
        {"month": month, "collected": amount}
        for month, amount in sorted(by_month.items())
    ]

    return {"trends": trends}


# ============================================================
# DASHBOARD WIDGETS
# ============================================================

@router.get("/dashboard/quick-stats")
async def get_quick_stats(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get quick stats for principal dashboard"""
    school_id = current_user.get("school_id")
    today = date.today()

    # Active students
    students = supabase.table("students").select(
        "id", count="exact"
    ).eq("school_id", school_id).eq("status", "active").execute()

    # Teachers
    teachers = supabase.table("teachers").select(
        "id", count="exact"
    ).eq("school_id", school_id).eq("is_active", True).execute()

    # Today's attendance
    attendance = supabase.table("attendance").select(
        "status"
    ).eq("school_id", school_id).eq("date", today.isoformat()).execute()

    attendance_records = attendance.data or []
    present_count = sum(1 for a in attendance_records if a.get("status") == "present")
    attendance_rate = round((present_count / len(attendance_records)) * 100, 1) if attendance_records else 0

    # Pending approvals
    pending_leaves = supabase.table("leave_requests").select(
        "id", count="exact"
    ).eq("school_id", school_id).eq("status", "pending").execute()

    return {
        "active_students": students.count or 0,
        "active_teachers": teachers.count or 0,
        "today_attendance_rate": attendance_rate,
        "pending_approvals": pending_leaves.count or 0,
        "date": today.isoformat()
    }


@router.get("/dashboard/alerts")
async def get_dashboard_alerts(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get alerts for principal dashboard"""
    school_id = current_user.get("school_id")
    alerts = []

    # Low attendance alert
    today = date.today()
    attendance = supabase.table("attendance").select(
        "status"
    ).eq("school_id", school_id).eq("date", today.isoformat()).execute()

    if attendance.data:
        present = sum(1 for a in attendance.data if a.get("status") == "present")
        rate = (present / len(attendance.data)) * 100
        if rate < 90:
            alerts.append({
                "type": "warning",
                "category": "attendance",
                "message": f"Today's attendance rate is {rate:.1f}%, below 90% threshold",
                "priority": "high" if rate < 85 else "medium"
            })

    # Overdue fees
    overdue = supabase.table("fee_records").select(
        "id", count="exact"
    ).eq("school_id", school_id).eq("status", "overdue").execute()

    if overdue.count and overdue.count > 0:
        alerts.append({
            "type": "warning",
            "category": "finance",
            "message": f"{overdue.count} fee records are overdue",
            "priority": "high" if overdue.count > 50 else "medium"
        })

    # Pending evaluations
    pending_evals = supabase.table("staff_evaluations").select(
        "id", count="exact"
    ).eq("school_id", school_id).eq("status", "draft").execute()

    if pending_evals.count and pending_evals.count > 0:
        alerts.append({
            "type": "info",
            "category": "staff",
            "message": f"{pending_evals.count} staff evaluations are pending completion",
            "priority": "low"
        })

    return {"alerts": alerts}
