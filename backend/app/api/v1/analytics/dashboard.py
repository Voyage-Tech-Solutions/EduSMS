"""
EduCore Backend - Analytics Dashboard API
Real-time metrics and KPIs for school management
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
# EXECUTIVE DASHBOARD
# ============================================================

@router.get("/executive-summary")
async def get_executive_summary(
    academic_year_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get executive summary for school leadership"""
    school_id = current_user.get("school_id")
    today = date.today()

    # Student metrics
    students = supabase.table("students").select(
        "id, status, gender, grade_id", count="exact"
    ).eq("school_id", school_id).execute()

    active_students = [s for s in (students.data or []) if s.get("status") == "active"]

    # Teacher metrics
    teachers = supabase.table("teachers").select(
        "id", count="exact"
    ).eq("school_id", school_id).eq("is_active", True).execute()

    # Today's attendance
    attendance = supabase.table("attendance").select("status").eq(
        "school_id", school_id
    ).eq("date", today.isoformat()).execute()

    att_records = attendance.data or []
    present = sum(1 for a in att_records if a.get("status") == "present")
    attendance_rate = round((present / len(att_records)) * 100, 1) if att_records else 0

    # Financial metrics
    fees = supabase.table("fee_records").select(
        "amount, amount_paid, status"
    ).eq("school_id", school_id).execute()

    total_fees = sum(f.get("amount", 0) for f in (fees.data or []))
    collected = sum(f.get("amount_paid", 0) for f in (fees.data or []))
    collection_rate = round((collected / total_fees) * 100, 1) if total_fees > 0 else 0

    # Academic performance (last term)
    grades = supabase.table("grades").select("score").eq(
        "school_id", school_id
    ).execute()

    scores = [g["score"] for g in (grades.data or []) if g.get("score") is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0

    return {
        "overview": {
            "total_students": len(active_students),
            "total_teachers": teachers.count or 0,
            "student_teacher_ratio": round(len(active_students) / (teachers.count or 1), 1),
            "attendance_rate_today": attendance_rate,
            "collection_rate": collection_rate,
            "average_academic_score": avg_score
        },
        "student_breakdown": {
            "by_gender": {
                "male": sum(1 for s in active_students if s.get("gender") == "male"),
                "female": sum(1 for s in active_students if s.get("gender") == "female"),
                "other": sum(1 for s in active_students if s.get("gender") not in ["male", "female"])
            }
        },
        "financial_summary": {
            "total_billed": total_fees,
            "total_collected": collected,
            "outstanding": total_fees - collected
        },
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/kpis")
async def get_key_performance_indicators(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get key performance indicators with trends"""
    school_id = current_user.get("school_id")
    today = date.today()
    last_week = today - timedelta(days=7)
    last_month = today - timedelta(days=30)

    kpis = []

    # Attendance KPI
    current_att = supabase.table("attendance").select("status").eq(
        "school_id", school_id
    ).gte("date", last_week.isoformat()).execute()

    prev_att = supabase.table("attendance").select("status").eq(
        "school_id", school_id
    ).gte("date", (last_week - timedelta(days=7)).isoformat()).lt(
        "date", last_week.isoformat()
    ).execute()

    current_rate = _calc_attendance_rate(current_att.data or [])
    prev_rate = _calc_attendance_rate(prev_att.data or [])

    kpis.append({
        "name": "Attendance Rate",
        "current_value": current_rate,
        "previous_value": prev_rate,
        "change": round(current_rate - prev_rate, 1),
        "trend": "up" if current_rate > prev_rate else "down" if current_rate < prev_rate else "stable",
        "unit": "%",
        "target": 95.0
    })

    # Collection Rate KPI
    fees = supabase.table("fee_records").select("amount, amount_paid").eq(
        "school_id", school_id
    ).execute()

    total = sum(f.get("amount", 0) for f in (fees.data or []))
    collected = sum(f.get("amount_paid", 0) for f in (fees.data or []))
    collection_rate = round((collected / total) * 100, 1) if total > 0 else 0

    kpis.append({
        "name": "Fee Collection Rate",
        "current_value": collection_rate,
        "unit": "%",
        "target": 90.0,
        "trend": "stable"
    })

    # Academic Performance KPI
    grades = supabase.table("grades").select("score").eq(
        "school_id", school_id
    ).execute()

    scores = [g["score"] for g in (grades.data or []) if g.get("score")]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    passing_rate = round(sum(1 for s in scores if s >= 60) / len(scores) * 100, 1) if scores else 0

    kpis.append({
        "name": "Pass Rate",
        "current_value": passing_rate,
        "unit": "%",
        "target": 85.0,
        "trend": "stable"
    })

    kpis.append({
        "name": "Average Score",
        "current_value": avg_score,
        "unit": "points",
        "target": 75.0,
        "trend": "stable"
    })

    return {"kpis": kpis}


def _calc_attendance_rate(records):
    if not records:
        return 0
    present = sum(1 for r in records if r.get("status") == "present")
    return round((present / len(records)) * 100, 1)


# ============================================================
# ENROLLMENT ANALYTICS
# ============================================================

@router.get("/enrollment")
async def get_enrollment_analytics(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get enrollment analytics"""
    school_id = current_user.get("school_id")

    students = supabase.table("students").select(
        "id, status, grade_id, gender, enrollment_date, grades(name)"
    ).eq("school_id", school_id).execute()

    all_students = students.data or []
    active = [s for s in all_students if s.get("status") == "active"]

    # By grade level
    by_grade = defaultdict(lambda: {"count": 0, "male": 0, "female": 0})
    for s in active:
        grade_name = s["grades"]["name"] if s.get("grades") else "Unknown"
        by_grade[grade_name]["count"] += 1
        if s.get("gender") == "male":
            by_grade[grade_name]["male"] += 1
        elif s.get("gender") == "female":
            by_grade[grade_name]["female"] += 1

    # Monthly enrollment trend
    monthly_trend = defaultdict(int)
    for s in all_students:
        if s.get("enrollment_date"):
            month = s["enrollment_date"][:7]
            monthly_trend[month] += 1

    # Capacity analysis (assuming grades have capacity)
    grades_result = supabase.table("grades").select(
        "id, name, capacity"
    ).eq("school_id", school_id).execute()

    capacity_analysis = []
    for grade in (grades_result.data or []):
        grade_count = by_grade.get(grade["name"], {}).get("count", 0)
        capacity = grade.get("capacity", 30)
        capacity_analysis.append({
            "grade": grade["name"],
            "enrolled": grade_count,
            "capacity": capacity,
            "utilization": round((grade_count / capacity) * 100, 1) if capacity > 0 else 0
        })

    return {
        "total_active": len(active),
        "total_all": len(all_students),
        "by_grade": dict(by_grade),
        "monthly_trend": dict(sorted(monthly_trend.items())[-12:]),
        "capacity_analysis": capacity_analysis,
        "gender_ratio": {
            "male": sum(1 for s in active if s.get("gender") == "male"),
            "female": sum(1 for s in active if s.get("gender") == "female")
        }
    }


# ============================================================
# ACADEMIC ANALYTICS
# ============================================================

@router.get("/academic")
async def get_academic_analytics(
    term_id: Optional[UUID] = None,
    subject_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get academic performance analytics"""
    school_id = current_user.get("school_id")

    query = supabase.table("grades").select(
        "score, grade_id, subject_id, class_id, subjects(name), grades(name)"
    ).eq("school_id", school_id)

    if term_id:
        query = query.eq("term_id", str(term_id))
    if subject_id:
        query = query.eq("subject_id", str(subject_id))

    result = query.execute()
    grades = result.data or []

    if not grades:
        return {"message": "No grade data available"}

    scores = [g["score"] for g in grades if g.get("score") is not None]

    # Distribution
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
        if g.get("score") is not None and g.get("subjects"):
            by_subject[g["subjects"]["name"]].append(g["score"])

    subject_performance = [
        {
            "subject": name,
            "average": round(sum(scores) / len(scores), 1),
            "count": len(scores),
            "passing_rate": round(sum(1 for s in scores if s >= 60) / len(scores) * 100, 1)
        }
        for name, scores in by_subject.items()
    ]
    subject_performance.sort(key=lambda x: x["average"], reverse=True)

    # By grade level
    by_grade_level = defaultdict(list)
    for g in grades:
        if g.get("score") is not None and g.get("grades"):
            by_grade_level[g["grades"]["name"]].append(g["score"])

    grade_performance = [
        {
            "grade": name,
            "average": round(sum(scores) / len(scores), 1),
            "count": len(scores)
        }
        for name, scores in by_grade_level.items()
    ]

    return {
        "overall": {
            "average": round(sum(scores) / len(scores), 1) if scores else 0,
            "median": sorted(scores)[len(scores) // 2] if scores else 0,
            "highest": max(scores) if scores else 0,
            "lowest": min(scores) if scores else 0,
            "passing_rate": round(sum(1 for s in scores if s >= 60) / len(scores) * 100, 1) if scores else 0
        },
        "distribution": distribution,
        "by_subject": subject_performance,
        "by_grade_level": grade_performance
    }


# ============================================================
# ATTENDANCE ANALYTICS
# ============================================================

@router.get("/attendance")
async def get_attendance_analytics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get attendance analytics"""
    school_id = current_user.get("school_id")

    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()

    result = supabase.table("attendance").select(
        "date, status, student_id, students(grade_id, grades(name))"
    ).eq("school_id", school_id).gte(
        "date", start_date.isoformat()
    ).lte("date", end_date.isoformat()).execute()

    records = result.data or []

    # Overall stats
    total = len(records)
    by_status = defaultdict(int)
    for r in records:
        by_status[r.get("status", "unknown")] += 1

    # Daily trend
    daily = defaultdict(lambda: {"present": 0, "absent": 0, "late": 0, "total": 0})
    for r in records:
        d = r.get("date")
        daily[d]["total"] += 1
        status = r.get("status", "unknown")
        if status in daily[d]:
            daily[d][status] += 1

    daily_trend = [
        {
            "date": d,
            "rate": round(data["present"] / data["total"] * 100, 1) if data["total"] > 0 else 0,
            **data
        }
        for d, data in sorted(daily.items())
    ]

    # By grade level
    by_grade = defaultdict(lambda: {"present": 0, "total": 0})
    for r in records:
        if r.get("students") and r["students"].get("grades"):
            grade_name = r["students"]["grades"]["name"]
            by_grade[grade_name]["total"] += 1
            if r.get("status") == "present":
                by_grade[grade_name]["present"] += 1

    grade_rates = [
        {
            "grade": name,
            "rate": round(data["present"] / data["total"] * 100, 1) if data["total"] > 0 else 0,
            "total_records": data["total"]
        }
        for name, data in by_grade.items()
    ]

    # Chronic absenteeism
    student_absences = defaultdict(int)
    student_total = defaultdict(int)
    for r in records:
        sid = r.get("student_id")
        student_total[sid] += 1
        if r.get("status") in ["absent", "unexcused"]:
            student_absences[sid] += 1

    chronic = sum(
        1 for sid, absences in student_absences.items()
        if student_total[sid] > 0 and (absences / student_total[sid]) >= 0.1
    )

    return {
        "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        "overall": {
            "total_records": total,
            "attendance_rate": round(by_status["present"] / total * 100, 1) if total > 0 else 0,
            "by_status": dict(by_status)
        },
        "daily_trend": daily_trend,
        "by_grade_level": grade_rates,
        "chronic_absenteeism": {
            "count": chronic,
            "threshold": "10%"
        }
    }


# ============================================================
# FINANCIAL ANALYTICS
# ============================================================

@router.get("/financial")
async def get_financial_analytics(
    academic_year_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get financial analytics"""
    school_id = current_user.get("school_id")

    query = supabase.table("fee_records").select(
        "amount, amount_paid, status, due_date, fee_types(name, category)"
    ).eq("school_id", school_id)

    if academic_year_id:
        query = query.eq("academic_year_id", str(academic_year_id))

    result = query.execute()
    fees = result.data or []

    total_billed = sum(f.get("amount", 0) for f in fees)
    total_collected = sum(f.get("amount_paid", 0) for f in fees)
    outstanding = total_billed - total_collected

    # By status
    by_status = defaultdict(lambda: {"count": 0, "amount": 0})
    for f in fees:
        status = f.get("status", "unknown")
        by_status[status]["count"] += 1
        by_status[status]["amount"] += f.get("amount", 0)

    # By fee type
    by_type = defaultdict(lambda: {"billed": 0, "collected": 0})
    for f in fees:
        if f.get("fee_types"):
            type_name = f["fee_types"]["name"]
            by_type[type_name]["billed"] += f.get("amount", 0)
            by_type[type_name]["collected"] += f.get("amount_paid", 0)

    fee_breakdown = [
        {
            "type": name,
            "billed": data["billed"],
            "collected": data["collected"],
            "outstanding": data["billed"] - data["collected"],
            "collection_rate": round(data["collected"] / data["billed"] * 100, 1) if data["billed"] > 0 else 0
        }
        for name, data in by_type.items()
    ]

    # Overdue analysis
    today = date.today()
    overdue_fees = [f for f in fees if f.get("due_date") and f["due_date"] < today.isoformat() and f.get("status") != "paid"]
    overdue_amount = sum(f.get("amount", 0) - f.get("amount_paid", 0) for f in overdue_fees)

    # Monthly collection trend
    payments = supabase.table("payments").select(
        "amount, payment_date"
    ).eq("school_id", school_id).execute()

    monthly_collections = defaultdict(float)
    for p in (payments.data or []):
        if p.get("payment_date"):
            month = p["payment_date"][:7]
            monthly_collections[month] += p.get("amount", 0)

    return {
        "summary": {
            "total_billed": total_billed,
            "total_collected": total_collected,
            "outstanding": outstanding,
            "collection_rate": round(total_collected / total_billed * 100, 1) if total_billed > 0 else 0
        },
        "by_status": dict(by_status),
        "by_fee_type": fee_breakdown,
        "overdue": {
            "count": len(overdue_fees),
            "amount": overdue_amount
        },
        "monthly_trend": dict(sorted(monthly_collections.items())[-12:])
    }


# ============================================================
# STAFF ANALYTICS
# ============================================================

@router.get("/staff")
async def get_staff_analytics(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get staff analytics"""
    school_id = current_user.get("school_id")

    # Teachers
    teachers = supabase.table("teachers").select(
        "id, gender, position, hire_date, is_active, subjects(name)"
    ).eq("school_id", school_id).execute()

    all_teachers = teachers.data or []
    active_teachers = [t for t in all_teachers if t.get("is_active")]

    # By experience
    today = date.today()
    experience_buckets = {"0-2 years": 0, "3-5 years": 0, "6-10 years": 0, "10+ years": 0}
    for t in active_teachers:
        if t.get("hire_date"):
            hire = datetime.fromisoformat(t["hire_date"].replace("Z", "+00:00")).date() if "T" in t["hire_date"] else date.fromisoformat(t["hire_date"])
            years = (today - hire).days // 365
            if years <= 2:
                experience_buckets["0-2 years"] += 1
            elif years <= 5:
                experience_buckets["3-5 years"] += 1
            elif years <= 10:
                experience_buckets["6-10 years"] += 1
            else:
                experience_buckets["10+ years"] += 1

    # Class assignments
    assignments = supabase.table("class_subjects").select(
        "teacher_id, class_id"
    ).eq("school_id", school_id).execute()

    teacher_loads = defaultdict(set)
    for a in (assignments.data or []):
        teacher_loads[a["teacher_id"]].add(a["class_id"])

    avg_load = sum(len(classes) for classes in teacher_loads.values()) / len(teacher_loads) if teacher_loads else 0

    return {
        "teachers": {
            "total_active": len(active_teachers),
            "total_all": len(all_teachers),
            "by_gender": {
                "male": sum(1 for t in active_teachers if t.get("gender") == "male"),
                "female": sum(1 for t in active_teachers if t.get("gender") == "female")
            },
            "by_experience": experience_buckets,
            "average_class_load": round(avg_load, 1)
        }
    }


# ============================================================
# COMPARISON ANALYTICS
# ============================================================

@router.get("/compare/terms")
async def compare_terms(
    term1_id: UUID,
    term2_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Compare metrics between two terms"""
    school_id = current_user.get("school_id")

    def get_term_metrics(term_id):
        # Grades
        grades = supabase.table("grades").select("score").eq(
            "school_id", school_id
        ).eq("term_id", str(term_id)).execute()

        scores = [g["score"] for g in (grades.data or []) if g.get("score")]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0
        pass_rate = round(sum(1 for s in scores if s >= 60) / len(scores) * 100, 1) if scores else 0

        # Attendance
        attendance = supabase.table("attendance").select("status").eq(
            "school_id", school_id
        ).eq("term_id", str(term_id)).execute()

        att_records = attendance.data or []
        att_rate = _calc_attendance_rate(att_records)

        return {
            "average_score": avg_score,
            "pass_rate": pass_rate,
            "attendance_rate": att_rate,
            "total_grades": len(scores),
            "total_attendance_records": len(att_records)
        }

    term1_metrics = get_term_metrics(term1_id)
    term2_metrics = get_term_metrics(term2_id)

    return {
        "term1": {"id": str(term1_id), **term1_metrics},
        "term2": {"id": str(term2_id), **term2_metrics},
        "changes": {
            "average_score": round(term2_metrics["average_score"] - term1_metrics["average_score"], 1),
            "pass_rate": round(term2_metrics["pass_rate"] - term1_metrics["pass_rate"], 1),
            "attendance_rate": round(term2_metrics["attendance_rate"] - term1_metrics["attendance_rate"], 1)
        }
    }
