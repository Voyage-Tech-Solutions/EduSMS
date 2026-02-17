"""
EduCore Backend - Analytics Insights API
AI-powered insights and recommendations
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
# AUTOMATED INSIGHTS
# ============================================================

@router.get("")
async def get_insights(
    category: Optional[str] = None,  # academic, attendance, financial, enrollment
    priority: Optional[str] = None,  # high, medium, low
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get automated insights and recommendations"""
    school_id = current_user.get("school_id")

    insights = []

    # Academic insights
    if not category or category == "academic":
        academic_insights = await _generate_academic_insights(school_id, supabase)
        insights.extend(academic_insights)

    # Attendance insights
    if not category or category == "attendance":
        attendance_insights = await _generate_attendance_insights(school_id, supabase)
        insights.extend(attendance_insights)

    # Financial insights
    if not category or category == "financial":
        financial_insights = await _generate_financial_insights(school_id, supabase)
        insights.extend(financial_insights)

    # Enrollment insights
    if not category or category == "enrollment":
        enrollment_insights = await _generate_enrollment_insights(school_id, supabase)
        insights.extend(enrollment_insights)

    # Filter by priority
    if priority:
        insights = [i for i in insights if i.get("priority") == priority]

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    insights.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 3))

    return {
        "insights": insights,
        "generated_at": datetime.utcnow().isoformat()
    }


async def _generate_academic_insights(school_id, supabase):
    """Generate academic insights"""
    insights = []

    # Get grades
    grades = supabase.table("grades").select(
        "score, subject_id, class_id, subjects(name), classes(name)"
    ).eq("school_id", school_id).execute()

    if not grades.data:
        return insights

    scores = [g["score"] for g in grades.data if g.get("score")]
    avg_score = sum(scores) / len(scores) if scores else 0
    fail_rate = sum(1 for s in scores if s < 60) / len(scores) * 100 if scores else 0

    # High failure rate alert
    if fail_rate > 20:
        insights.append({
            "id": "academic_high_failure",
            "category": "academic",
            "priority": "high",
            "type": "alert",
            "title": "High Failure Rate Detected",
            "description": f"Overall failure rate is {fail_rate:.1f}%, which is above the 20% threshold.",
            "recommendation": "Review curriculum difficulty and consider additional support programs.",
            "metric": {"name": "Failure Rate", "value": fail_rate, "unit": "%", "threshold": 20}
        })

    # Subject performance analysis
    by_subject = defaultdict(list)
    for g in grades.data:
        if g.get("score") and g.get("subjects"):
            by_subject[g["subjects"]["name"]].append(g["score"])

    for subject, subject_scores in by_subject.items():
        subject_avg = sum(subject_scores) / len(subject_scores)
        if subject_avg < avg_score - 10:
            insights.append({
                "id": f"academic_weak_subject_{subject}",
                "category": "academic",
                "priority": "medium",
                "type": "observation",
                "title": f"Underperforming Subject: {subject}",
                "description": f"{subject} average ({subject_avg:.1f}) is significantly below school average ({avg_score:.1f}).",
                "recommendation": f"Consider reviewing {subject} curriculum and teaching methods."
            })

    # Class comparison
    by_class = defaultdict(list)
    class_names = {}
    for g in grades.data:
        if g.get("score") and g.get("classes"):
            by_class[g["class_id"]].append(g["score"])
            class_names[g["class_id"]] = g["classes"]["name"]

    class_avgs = {cid: sum(s) / len(s) for cid, s in by_class.items()}
    if class_avgs:
        best_class = max(class_avgs, key=class_avgs.get)
        worst_class = min(class_avgs, key=class_avgs.get)

        if class_avgs[best_class] - class_avgs[worst_class] > 15:
            insights.append({
                "id": "academic_class_disparity",
                "category": "academic",
                "priority": "medium",
                "type": "observation",
                "title": "Significant Performance Gap Between Classes",
                "description": f"There's a {class_avgs[best_class] - class_avgs[worst_class]:.1f} point gap between highest and lowest performing classes.",
                "recommendation": "Investigate teaching methods and resources in underperforming classes."
            })

    return insights


async def _generate_attendance_insights(school_id, supabase):
    """Generate attendance insights"""
    insights = []

    today = date.today()
    last_30_days = today - timedelta(days=30)

    attendance = supabase.table("attendance").select(
        "status, date, student_id"
    ).eq("school_id", school_id).gte("date", last_30_days.isoformat()).execute()

    if not attendance.data:
        return insights

    records = attendance.data
    total = len(records)
    present = sum(1 for r in records if r.get("status") == "present")
    attendance_rate = present / total * 100 if total > 0 else 0

    # Low attendance alert
    if attendance_rate < 90:
        insights.append({
            "id": "attendance_low_rate",
            "category": "attendance",
            "priority": "high",
            "type": "alert",
            "title": "Low Overall Attendance Rate",
            "description": f"30-day attendance rate ({attendance_rate:.1f}%) is below 90% target.",
            "recommendation": "Implement attendance improvement initiatives and parent outreach.",
            "metric": {"name": "Attendance Rate", "value": attendance_rate, "unit": "%", "threshold": 90}
        })

    # Chronic absenteeism
    student_absences = defaultdict(int)
    student_total = defaultdict(int)
    for r in records:
        sid = r.get("student_id")
        student_total[sid] += 1
        if r.get("status") in ["absent", "unexcused"]:
            student_absences[sid] += 1

    chronic_count = sum(
        1 for sid, absences in student_absences.items()
        if student_total[sid] > 0 and (absences / student_total[sid]) >= 0.1
    )

    if chronic_count > 0:
        total_students = len(student_total)
        chronic_percent = chronic_count / total_students * 100 if total_students > 0 else 0
        insights.append({
            "id": "attendance_chronic_absenteeism",
            "category": "attendance",
            "priority": "high" if chronic_percent > 10 else "medium",
            "type": "alert",
            "title": "Chronic Absenteeism Detected",
            "description": f"{chronic_count} students ({chronic_percent:.1f}%) have chronic absenteeism (>10% absence rate).",
            "recommendation": "Initiate intervention programs for chronically absent students."
        })

    # Daily pattern analysis
    day_attendance = defaultdict(lambda: {"present": 0, "total": 0})
    for r in records:
        if r.get("date"):
            day = datetime.fromisoformat(r["date"]).strftime("%A")
            day_attendance[day]["total"] += 1
            if r.get("status") == "present":
                day_attendance[day]["present"] += 1

    day_rates = {
        day: data["present"] / data["total"] * 100 if data["total"] > 0 else 0
        for day, data in day_attendance.items()
    }

    if day_rates:
        worst_day = min(day_rates, key=day_rates.get)
        if day_rates[worst_day] < 85:
            insights.append({
                "id": "attendance_day_pattern",
                "category": "attendance",
                "priority": "low",
                "type": "pattern",
                "title": f"Lower Attendance on {worst_day}s",
                "description": f"{worst_day}s have the lowest attendance ({day_rates[worst_day]:.1f}%).",
                "recommendation": f"Consider scheduling engaging activities on {worst_day}s."
            })

    return insights


async def _generate_financial_insights(school_id, supabase):
    """Generate financial insights"""
    insights = []

    fees = supabase.table("fee_records").select(
        "amount, amount_paid, status, due_date, student_id"
    ).eq("school_id", school_id).execute()

    if not fees.data:
        return insights

    total_billed = sum(f.get("amount", 0) for f in fees.data)
    total_collected = sum(f.get("amount_paid", 0) for f in fees.data)
    collection_rate = total_collected / total_billed * 100 if total_billed > 0 else 0

    # Low collection rate
    if collection_rate < 80:
        insights.append({
            "id": "financial_low_collection",
            "category": "financial",
            "priority": "high",
            "type": "alert",
            "title": "Low Fee Collection Rate",
            "description": f"Collection rate ({collection_rate:.1f}%) is below 80% target.",
            "recommendation": "Implement payment reminders and flexible payment plans.",
            "metric": {"name": "Collection Rate", "value": collection_rate, "unit": "%", "threshold": 80}
        })

    # Overdue analysis
    today = date.today()
    overdue = [f for f in fees.data if f.get("due_date") and f["due_date"] < today.isoformat() and f.get("status") != "paid"]
    overdue_amount = sum(f.get("amount", 0) - f.get("amount_paid", 0) for f in overdue)

    if overdue_amount > 0:
        overdue_percent = overdue_amount / total_billed * 100 if total_billed > 0 else 0
        insights.append({
            "id": "financial_overdue",
            "category": "financial",
            "priority": "high" if overdue_percent > 15 else "medium",
            "type": "alert",
            "title": f"${overdue_amount:,.2f} in Overdue Fees",
            "description": f"{len(overdue)} fee records are overdue, representing {overdue_percent:.1f}% of total billing.",
            "recommendation": "Prioritize collection on overdue accounts with escalation procedures."
        })

    # Student concentration risk
    student_balances = defaultdict(float)
    for f in fees.data:
        sid = f.get("student_id")
        student_balances[sid] += f.get("amount", 0) - f.get("amount_paid", 0)

    large_balances = [b for b in student_balances.values() if b > 5000]
    if large_balances:
        insights.append({
            "id": "financial_concentration",
            "category": "financial",
            "priority": "medium",
            "type": "observation",
            "title": f"{len(large_balances)} Accounts with Large Outstanding Balances",
            "description": f"Accounts with balances over $5,000 represent concentration risk.",
            "recommendation": "Work with these families on payment arrangements."
        })

    return insights


async def _generate_enrollment_insights(school_id, supabase):
    """Generate enrollment insights"""
    insights = []

    students = supabase.table("students").select(
        "id, status, grade_id, enrollment_date, grades(name, capacity)"
    ).eq("school_id", school_id).execute()

    if not students.data:
        return insights

    active = [s for s in students.data if s.get("status") == "active"]

    # Capacity analysis
    grade_counts = defaultdict(int)
    grade_capacities = {}
    for s in active:
        if s.get("grades"):
            grade_name = s["grades"]["name"]
            grade_counts[grade_name] += 1
            if "capacity" in s["grades"]:
                grade_capacities[grade_name] = s["grades"]["capacity"]

    for grade, count in grade_counts.items():
        capacity = grade_capacities.get(grade, 30)
        utilization = count / capacity * 100 if capacity > 0 else 0

        if utilization >= 95:
            insights.append({
                "id": f"enrollment_capacity_{grade}",
                "category": "enrollment",
                "priority": "high",
                "type": "alert",
                "title": f"{grade} Near Capacity",
                "description": f"{grade} is at {utilization:.1f}% capacity ({count}/{capacity} students).",
                "recommendation": "Consider adding sections or waitlist management."
            })
        elif utilization < 50:
            insights.append({
                "id": f"enrollment_underutilized_{grade}",
                "category": "enrollment",
                "priority": "low",
                "type": "observation",
                "title": f"{grade} Underutilized",
                "description": f"{grade} is at only {utilization:.1f}% capacity.",
                "recommendation": "Consider marketing efforts or consolidation."
            })

    # Enrollment trend
    today = date.today()
    this_year = sum(
        1 for s in students.data
        if s.get("enrollment_date") and s["enrollment_date"][:4] == str(today.year)
    )
    last_year = sum(
        1 for s in students.data
        if s.get("enrollment_date") and s["enrollment_date"][:4] == str(today.year - 1)
    )

    if last_year > 0:
        growth = (this_year - last_year) / last_year * 100
        if growth < -10:
            insights.append({
                "id": "enrollment_decline",
                "category": "enrollment",
                "priority": "high",
                "type": "alert",
                "title": "Enrollment Decline Detected",
                "description": f"New enrollments are down {abs(growth):.1f}% compared to last year.",
                "recommendation": "Review enrollment strategies and conduct family surveys."
            })
        elif growth > 20:
            insights.append({
                "id": "enrollment_growth",
                "category": "enrollment",
                "priority": "low",
                "type": "positive",
                "title": "Strong Enrollment Growth",
                "description": f"New enrollments are up {growth:.1f}% compared to last year.",
                "recommendation": "Ensure adequate resources and staffing for growth."
            })

    return insights


# ============================================================
# TREND ANALYSIS
# ============================================================

@router.get("/trends")
async def get_trends(
    metric: str,  # attendance, grades, enrollment, revenue
    period: str = "monthly",  # daily, weekly, monthly, quarterly
    months: int = 12,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get trend analysis for specific metrics"""
    school_id = current_user.get("school_id")

    if metric == "attendance":
        return await _get_attendance_trends(school_id, period, months, supabase)
    elif metric == "grades":
        return await _get_grade_trends(school_id, period, months, supabase)
    elif metric == "enrollment":
        return await _get_enrollment_trends(school_id, period, months, supabase)
    elif metric == "revenue":
        return await _get_revenue_trends(school_id, period, months, supabase)
    else:
        raise HTTPException(status_code=400, detail="Invalid metric")


async def _get_attendance_trends(school_id, period, months, supabase):
    """Get attendance trends"""
    start_date = date.today() - timedelta(days=months * 30)

    result = supabase.table("attendance").select("date, status").eq(
        "school_id", school_id
    ).gte("date", start_date.isoformat()).execute()

    records = result.data or []

    # Group by period
    trends = defaultdict(lambda: {"present": 0, "total": 0})
    for r in records:
        if r.get("date"):
            if period == "monthly":
                key = r["date"][:7]
            elif period == "weekly":
                dt = datetime.fromisoformat(r["date"])
                key = f"{dt.year}-W{dt.isocalendar()[1]:02d}"
            else:
                key = r["date"]

            trends[key]["total"] += 1
            if r.get("status") == "present":
                trends[key]["present"] += 1

    data = [
        {
            "period": p,
            "rate": round(d["present"] / d["total"] * 100, 1) if d["total"] > 0 else 0,
            "total": d["total"]
        }
        for p, d in sorted(trends.items())
    ]

    return {"metric": "attendance", "period": period, "data": data}


async def _get_grade_trends(school_id, period, months, supabase):
    """Get grade trends"""
    terms = supabase.table("terms").select("id, name, start_date").eq(
        "school_id", school_id
    ).order("start_date", desc=True).limit(8).execute()

    data = []
    for term in reversed(terms.data or []):
        grades = supabase.table("grades").select("score").eq(
            "school_id", school_id
        ).eq("term_id", term["id"]).execute()

        scores = [g["score"] for g in (grades.data or []) if g.get("score")]
        avg = sum(scores) / len(scores) if scores else 0

        data.append({
            "period": term["name"],
            "average": round(avg, 1),
            "total_grades": len(scores)
        })

    return {"metric": "grades", "period": "term", "data": data}


async def _get_enrollment_trends(school_id, period, months, supabase):
    """Get enrollment trends"""
    result = supabase.table("students").select(
        "enrollment_date, status"
    ).eq("school_id", school_id).execute()

    students = result.data or []

    # Group by month
    trends = defaultdict(int)
    for s in students:
        if s.get("enrollment_date"):
            month = s["enrollment_date"][:7]
            trends[month] += 1

    # Cumulative count
    data = []
    cumulative = 0
    for month in sorted(trends.keys())[-months:]:
        cumulative += trends[month]
        data.append({
            "period": month,
            "new_enrollments": trends[month],
            "cumulative": cumulative
        })

    return {"metric": "enrollment", "period": "monthly", "data": data}


async def _get_revenue_trends(school_id, period, months, supabase):
    """Get revenue trends"""
    start_date = date.today() - timedelta(days=months * 30)

    result = supabase.table("payments").select(
        "amount, payment_date"
    ).eq("school_id", school_id).gte("payment_date", start_date.isoformat()).execute()

    payments = result.data or []

    trends = defaultdict(float)
    for p in payments:
        if p.get("payment_date"):
            month = p["payment_date"][:7]
            trends[month] += p.get("amount", 0)

    data = [
        {"period": m, "revenue": amount}
        for m, amount in sorted(trends.items())
    ]

    return {"metric": "revenue", "period": "monthly", "data": data}


# ============================================================
# PREDICTIONS
# ============================================================

@router.get("/predictions")
async def get_predictions(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get predictions based on current trends (simplified)"""
    school_id = current_user.get("school_id")

    predictions = []

    # Predict next month's attendance
    last_month_att = supabase.table("attendance").select("status").eq(
        "school_id", school_id
    ).gte("date", (date.today() - timedelta(days=30)).isoformat()).execute()

    if last_month_att.data:
        current_rate = sum(1 for a in last_month_att.data if a.get("status") == "present") / len(last_month_att.data) * 100
        predictions.append({
            "metric": "attendance_rate",
            "current": round(current_rate, 1),
            "predicted": round(current_rate * 0.98, 1),  # Simplified prediction
            "confidence": "medium",
            "period": "next_month"
        })

    # Predict collection rate
    fees = supabase.table("fee_records").select("amount, amount_paid").eq(
        "school_id", school_id
    ).execute()

    if fees.data:
        total = sum(f.get("amount", 0) for f in fees.data)
        collected = sum(f.get("amount_paid", 0) for f in fees.data)
        current_rate = collected / total * 100 if total > 0 else 0
        predictions.append({
            "metric": "collection_rate",
            "current": round(current_rate, 1),
            "predicted": round(min(current_rate * 1.02, 100), 1),
            "confidence": "low",
            "period": "end_of_term"
        })

    return {"predictions": predictions, "disclaimer": "Predictions are estimates based on historical trends."}
