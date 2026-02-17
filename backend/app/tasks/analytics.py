"""
EduCore Backend - Analytics Tasks
Background tasks for analytics and ML predictions
"""
from celery import shared_task
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def weekly_rollup(self) -> Dict:
    """
    Generate weekly analytics rollup for all schools
    Runs every Sunday at 2 AM UTC
    """
    try:
        from app.db.supabase import get_supabase_admin

        supabase = get_supabase_admin()

        # Get all active schools
        schools = supabase.table("schools").select("id").eq("is_active", True).execute()

        results = []
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=7)

        for school in (schools.data or []):
            school_id = school["id"]

            # Calculate weekly metrics
            metrics = calculate_school_weekly_metrics(supabase, school_id, start_date, end_date)

            # Store in analytics table
            supabase.table("analytics_snapshots").insert({
                "school_id": school_id,
                "snapshot_type": "weekly",
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "metrics": metrics,
                "created_at": datetime.utcnow().isoformat(),
            }).execute()

            results.append({"school_id": school_id, "metrics": metrics})

        logger.info(f"Weekly rollup completed for {len(results)} schools")
        return {"success": True, "schools_processed": len(results)}

    except Exception as e:
        logger.error(f"Failed to generate weekly rollup: {e}")
        return {"success": False, "error": str(e)}


def calculate_school_weekly_metrics(supabase, school_id: str, start_date, end_date) -> Dict:
    """Calculate weekly metrics for a school"""
    try:
        start_str = start_date.isoformat()
        end_str = end_date.isoformat()

        # Attendance metrics
        attendance = supabase.table("attendance_records").select(
            "status"
        ).eq("school_id", school_id).gte("date", start_str).lte("date", end_str).execute()

        attendance_data = attendance.data or []
        total_attendance = len(attendance_data)
        present = len([a for a in attendance_data if a["status"] == "present"])

        # Financial metrics
        payments = supabase.table("payments").select(
            "amount"
        ).eq("school_id", school_id).gte("payment_date", start_str).lte("payment_date", end_str).execute()

        total_collected = sum(p.get("amount", 0) for p in (payments.data or []))

        # Assessment metrics
        scores = supabase.table("assessment_scores").select(
            "score, assessments(total_marks)"
        ).eq("school_id", school_id).gte("created_at", start_str).lte("created_at", end_str).execute()

        return {
            "attendance": {
                "total_records": total_attendance,
                "present": present,
                "rate": round((present / total_attendance * 100), 1) if total_attendance > 0 else 0,
            },
            "finance": {
                "collected": total_collected,
                "payment_count": len(payments.data or []),
            },
            "assessments": {
                "scores_recorded": len(scores.data or []),
            },
        }

    except Exception as e:
        logger.error(f"Error calculating metrics for school {school_id}: {e}")
        return {}


@shared_task(bind=True)
def generate_risk_predictions(self) -> Dict:
    """
    Generate at-risk student predictions using ML model
    Runs every Sunday at 3 AM UTC
    """
    try:
        from app.db.supabase import get_supabase_admin

        supabase = get_supabase_admin()

        # Get all active schools
        schools = supabase.table("schools").select("id").eq("is_active", True).execute()

        total_predictions = 0
        high_risk_count = 0

        for school in (schools.data or []):
            school_id = school["id"]

            # Get active students
            students = supabase.table("students").select(
                "id"
            ).eq("school_id", school_id).eq("status", "active").execute()

            for student in (students.data or []):
                # Generate prediction for each student
                result = predict_student_risk.delay(student["id"], school_id)
                total_predictions += 1

        logger.info(f"Queued {total_predictions} risk predictions")
        return {"success": True, "predictions_queued": total_predictions}

    except Exception as e:
        logger.error(f"Failed to generate risk predictions: {e}")
        return {"success": False, "error": str(e)}


@shared_task(bind=True)
def predict_student_risk(self, student_id: str, school_id: str) -> Dict:
    """
    Predict individual student risk score

    Args:
        student_id: Student UUID
        school_id: School UUID
    """
    try:
        from app.db.supabase import get_supabase_admin

        supabase = get_supabase_admin()

        # Fetch student data for prediction
        student = supabase.table("students").select("*").eq("id", student_id).single().execute()

        if not student.data:
            return {"success": False, "error": "Student not found"}

        # Fetch features for ML model
        features = extract_student_features(supabase, student_id)

        # Run prediction model (placeholder - would use actual ML model)
        risk_score, risk_level, factors = calculate_risk_score(features)

        # Store prediction
        supabase.table("risk_predictions").upsert({
            "student_id": student_id,
            "prediction_type": "academic_risk",
            "risk_score": risk_score,
            "risk_level": risk_level,
            "contributing_factors": factors,
            "recommended_interventions": get_recommended_interventions(risk_level, factors),
            "predicted_at": datetime.utcnow().isoformat(),
            "model_version": "v1.0.0",
        }, on_conflict="student_id,prediction_type").execute()

        return {
            "success": True,
            "student_id": student_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
        }

    except Exception as e:
        logger.error(f"Failed to predict risk for student {student_id}: {e}")
        return {"success": False, "error": str(e)}


def extract_student_features(supabase, student_id: str) -> Dict:
    """Extract features for ML prediction"""
    try:
        # Get attendance data (last 30 days)
        thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()

        attendance = supabase.table("attendance_records").select(
            "status"
        ).eq("student_id", student_id).gte("date", thirty_days_ago).execute()

        attendance_data = attendance.data or []
        total_days = len(attendance_data)
        present_days = len([a for a in attendance_data if a["status"] == "present"])
        absent_days = len([a for a in attendance_data if a["status"] == "absent"])

        # Get academic data
        scores = supabase.table("assessment_scores").select(
            "score, percentage"
        ).eq("student_id", student_id).gte("created_at", thirty_days_ago).execute()

        score_data = scores.data or []
        avg_score = sum(s.get("percentage", 0) for s in score_data) / len(score_data) if score_data else 0

        # Get fee status
        invoices = supabase.table("invoices").select(
            "status, amount, amount_paid"
        ).eq("student_id", student_id).eq("status", "overdue").execute()

        overdue_amount = sum(
            (inv.get("amount", 0) - inv.get("amount_paid", 0))
            for inv in (invoices.data or [])
        )

        return {
            "attendance_rate": (present_days / total_days * 100) if total_days > 0 else 100,
            "absence_count": absent_days,
            "avg_score": avg_score,
            "overdue_fees": overdue_amount,
            "days_tracked": total_days,
            "assessments_count": len(score_data),
        }

    except Exception as e:
        logger.error(f"Error extracting features for student {student_id}: {e}")
        return {}


def calculate_risk_score(features: Dict) -> tuple:
    """
    Calculate risk score from features
    This is a simplified rule-based model - would be replaced with ML model
    """
    score = 0.0
    factors = []

    # Attendance factor (weight: 40%)
    attendance_rate = features.get("attendance_rate", 100)
    if attendance_rate < 70:
        score += 0.4
        factors.append({"factor": "low_attendance", "value": attendance_rate, "weight": 0.4})
    elif attendance_rate < 85:
        score += 0.2
        factors.append({"factor": "moderate_attendance", "value": attendance_rate, "weight": 0.2})

    # Academic factor (weight: 40%)
    avg_score = features.get("avg_score", 50)
    if avg_score < 40:
        score += 0.4
        factors.append({"factor": "failing_grades", "value": avg_score, "weight": 0.4})
    elif avg_score < 60:
        score += 0.2
        factors.append({"factor": "low_grades", "value": avg_score, "weight": 0.2})

    # Financial factor (weight: 20%)
    overdue_fees = features.get("overdue_fees", 0)
    if overdue_fees > 1000:
        score += 0.2
        factors.append({"factor": "significant_overdue_fees", "value": overdue_fees, "weight": 0.2})
    elif overdue_fees > 0:
        score += 0.1
        factors.append({"factor": "overdue_fees", "value": overdue_fees, "weight": 0.1})

    # Determine risk level
    if score >= 0.7:
        risk_level = "critical"
    elif score >= 0.5:
        risk_level = "high"
    elif score >= 0.3:
        risk_level = "medium"
    else:
        risk_level = "low"

    return round(score, 4), risk_level, factors


def get_recommended_interventions(risk_level: str, factors: List[Dict]) -> List[str]:
    """Get recommended interventions based on risk factors"""
    interventions = []

    factor_names = [f["factor"] for f in factors]

    if "low_attendance" in factor_names or "moderate_attendance" in factor_names:
        interventions.append("Schedule parent conference to discuss attendance")
        interventions.append("Implement attendance monitoring plan")

    if "failing_grades" in factor_names or "low_grades" in factor_names:
        interventions.append("Assign to tutoring program")
        interventions.append("Create individualized learning plan")
        interventions.append("Schedule teacher consultation")

    if "significant_overdue_fees" in factor_names or "overdue_fees" in factor_names:
        interventions.append("Contact family about payment plan options")
        interventions.append("Review for scholarship eligibility")

    if risk_level in ["critical", "high"]:
        interventions.append("Flag for counselor review")
        interventions.append("Create comprehensive intervention plan")

    return interventions


@shared_task(bind=True)
def calculate_teacher_metrics(self, teacher_id: str, school_id: str) -> Dict:
    """
    Calculate teacher performance metrics

    Args:
        teacher_id: Teacher user ID
        school_id: School UUID
    """
    try:
        from app.db.supabase import get_supabase_admin

        supabase = get_supabase_admin()

        # Get teacher's classes
        assignments = supabase.table("teacher_assignments").select(
            "class_id, subject_id"
        ).eq("teacher_id", teacher_id).execute()

        class_ids = [a["class_id"] for a in (assignments.data or [])]

        if not class_ids:
            return {"success": True, "message": "No classes assigned"}

        # Calculate metrics
        thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()

        # Attendance marking rate
        sessions = supabase.table("attendance_sessions").select(
            "id"
        ).in_("class_id", class_ids).eq("recorded_by", teacher_id).gte(
            "date", thirty_days_ago
        ).execute()

        # Assessment completion
        assessments = supabase.table("assessments").select(
            "id, status"
        ).eq("teacher_id", teacher_id).execute()

        assessment_data = assessments.data or []
        total_assessments = len(assessment_data)
        graded = len([a for a in assessment_data if a["status"] == "closed"])

        metrics = {
            "attendance_sessions_recorded": len(sessions.data or []),
            "total_assessments": total_assessments,
            "graded_assessments": graded,
            "grading_completion_rate": round((graded / total_assessments * 100), 1) if total_assessments > 0 else 0,
            "classes_count": len(class_ids),
        }

        return {"success": True, "teacher_id": teacher_id, "metrics": metrics}

    except Exception as e:
        logger.error(f"Failed to calculate teacher metrics for {teacher_id}: {e}")
        return {"success": False, "error": str(e)}
