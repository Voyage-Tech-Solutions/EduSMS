"""
EduCore Backend - Grade Calculations API
Weighted average calculations, term grades, GPA, and reports
"""
import logging
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# MODELS
# ============================================================

class TermGradeCreate(BaseModel):
    """Create/update term grade"""
    student_id: UUID
    class_id: UUID
    subject_id: UUID
    term_id: Optional[UUID] = None
    teacher_comment: Optional[str] = None
    conduct_grade: Optional[str] = None
    effort_grade: Optional[str] = None


class TermGradeResponse(BaseModel):
    """Term grade response"""
    id: UUID
    student_id: UUID
    class_id: UUID
    subject_id: UUID
    raw_average: Optional[float] = None
    weighted_average: Optional[float] = None
    final_percentage: Optional[float] = None
    final_letter_grade: Optional[str] = None
    gpa_points: Optional[float] = None
    status: str
    teacher_comment: Optional[str] = None


class ClassGradeSummary(BaseModel):
    """Summary of grades for a class"""
    class_id: UUID
    subject_id: UUID
    total_students: int
    graded_students: int
    class_average: Optional[float] = None
    grade_distribution: dict
    highest_grade: Optional[float] = None
    lowest_grade: Optional[float] = None


# ============================================================
# CALCULATION FUNCTIONS
# ============================================================

def calculate_raw_average(entries: List[dict]) -> Optional[float]:
    """Calculate simple average from gradebook entries"""
    graded = [e for e in entries if e.get("score") is not None and not e.get("is_excused")]

    if not graded:
        return None

    total_score = sum(e["score"] for e in graded)
    total_max = sum(e["max_score"] for e in graded)

    if total_max == 0:
        return None

    return round((total_score / total_max) * 100, 2)


def calculate_weighted_average(entries: List[dict], categories: List[dict]) -> Optional[float]:
    """Calculate weighted average using category weights"""
    if not categories:
        return calculate_raw_average(entries)

    category_map = {str(c["id"]): c for c in categories}
    category_totals = {}

    # Group entries by category and calculate category averages
    for entry in entries:
        if entry.get("score") is None or entry.get("is_excused"):
            continue

        cat_id = str(entry.get("category_id")) if entry.get("category_id") else "uncategorized"

        if cat_id not in category_totals:
            category_totals[cat_id] = {
                "total_score": 0,
                "total_max": 0,
                "weight": category_map.get(cat_id, {}).get("weight", 0),
                "drop_lowest": category_map.get(cat_id, {}).get("drop_lowest", 0),
                "scores": []
            }

        category_totals[cat_id]["scores"].append({
            "score": entry["score"],
            "max_score": entry["max_score"],
            "percentage": (entry["score"] / entry["max_score"] * 100) if entry["max_score"] > 0 else 0
        })

    # Calculate category averages with drop lowest
    weighted_sum = 0
    total_weight = 0

    for cat_id, data in category_totals.items():
        scores = data["scores"]
        drop_count = data["drop_lowest"]

        # Sort by percentage and drop lowest scores
        if drop_count > 0 and len(scores) > drop_count:
            scores = sorted(scores, key=lambda x: x["percentage"])[drop_count:]

        if scores:
            total_score = sum(s["score"] for s in scores)
            total_max = sum(s["max_score"] for s in scores)
            category_avg = (total_score / total_max * 100) if total_max > 0 else 0

            weight = data["weight"]
            weighted_sum += category_avg * weight
            total_weight += weight

    if total_weight == 0:
        return None

    return round(weighted_sum / total_weight, 2)


def get_letter_grade(percentage: float, scale_config: dict) -> tuple:
    """Get letter grade and GPA from percentage using scale config"""
    for grade, config in scale_config.items():
        min_score = config.get("min", 0)
        max_score = config.get("max", 100)

        if min_score <= percentage <= max_score:
            return grade, config.get("gpa")

    return "F", 0.0


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/student/{student_id}/class/{class_id}/subject/{subject_id}")
async def calculate_student_grade(
    student_id: UUID,
    class_id: UUID,
    subject_id: UUID,
    term_id: Optional[UUID] = None,
    grading_scale_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Calculate a student's current grade for a class/subject"""
    school_id = current_user.get("school_id")

    # Get gradebook entries
    query = supabase.table("gradebook_entries").select(
        "*"
    ).eq("student_id", str(student_id)).eq(
        "class_id", str(class_id)
    ).eq("subject_id", str(subject_id))

    if term_id:
        query = query.eq("term_id", str(term_id))

    entries_result = query.execute()
    entries = entries_result.data or []

    # Get categories
    categories_result = supabase.table("grade_categories").select(
        "id, name, weight, drop_lowest, is_extra_credit"
    ).eq("class_id", str(class_id)).eq("subject_id", str(subject_id)).execute()

    categories = categories_result.data or []

    # Get grading scale
    scale_config = None
    if grading_scale_id:
        scale_result = supabase.table("grading_scales").select(
            "scale_config"
        ).eq("id", str(grading_scale_id)).single().execute()
        if scale_result.data:
            scale_config = scale_result.data["scale_config"]

    if not scale_config:
        # Get default scale for school
        default_scale = supabase.table("grading_scales").select(
            "scale_config"
        ).eq("school_id", school_id).eq("is_default", True).single().execute()
        if default_scale.data:
            scale_config = default_scale.data["scale_config"]

    # Calculate grades
    raw_average = calculate_raw_average(entries)
    weighted_average = calculate_weighted_average(entries, categories)

    final_percentage = weighted_average or raw_average

    # Get letter grade
    letter_grade = None
    gpa_points = None
    if final_percentage is not None and scale_config:
        letter_grade, gpa_points = get_letter_grade(final_percentage, scale_config)

    # Category breakdown
    category_breakdown = []
    for cat in categories:
        cat_entries = [e for e in entries if e.get("category_id") == cat["id"]]
        cat_graded = [e for e in cat_entries if e.get("score") is not None and not e.get("is_excused")]

        if cat_graded:
            total_score = sum(e["score"] for e in cat_graded)
            total_max = sum(e["max_score"] for e in cat_graded)
            cat_avg = round((total_score / total_max * 100), 2) if total_max > 0 else None
        else:
            cat_avg = None

        category_breakdown.append({
            "category_id": cat["id"],
            "name": cat["name"],
            "weight": cat["weight"],
            "entries_count": len(cat_entries),
            "graded_count": len(cat_graded),
            "average": cat_avg
        })

    return {
        "student_id": str(student_id),
        "class_id": str(class_id),
        "subject_id": str(subject_id),
        "total_entries": len(entries),
        "graded_entries": len([e for e in entries if e.get("score") is not None]),
        "missing_entries": len([e for e in entries if e.get("is_missing")]),
        "excused_entries": len([e for e in entries if e.get("is_excused")]),
        "raw_average": raw_average,
        "weighted_average": weighted_average,
        "final_percentage": final_percentage,
        "letter_grade": letter_grade,
        "gpa_points": gpa_points,
        "category_breakdown": category_breakdown
    }


@router.get("/class/{class_id}/subject/{subject_id}/summary")
async def calculate_class_summary(
    class_id: UUID,
    subject_id: UUID,
    term_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get grade summary statistics for a class"""
    # Get all students in class
    students_result = supabase.table("students").select(
        "id"
    ).eq("class_id", str(class_id)).eq("status", "active").execute()

    students = students_result.data or []
    total_students = len(students)

    # Get all entries for class/subject
    query = supabase.table("gradebook_entries").select(
        "student_id, score, max_score, is_excused"
    ).eq("class_id", str(class_id)).eq("subject_id", str(subject_id))

    if term_id:
        query = query.eq("term_id", str(term_id))

    entries_result = query.execute()
    entries = entries_result.data or []

    # Calculate per-student averages
    student_averages = {}
    for entry in entries:
        if entry.get("score") is None or entry.get("is_excused"):
            continue

        student_id = entry["student_id"]
        if student_id not in student_averages:
            student_averages[student_id] = {"total_score": 0, "total_max": 0}

        student_averages[student_id]["total_score"] += entry["score"]
        student_averages[student_id]["total_max"] += entry["max_score"]

    # Calculate averages
    averages = []
    for data in student_averages.values():
        if data["total_max"] > 0:
            avg = (data["total_score"] / data["total_max"]) * 100
            averages.append(round(avg, 2))

    # Statistics
    if averages:
        class_average = round(sum(averages) / len(averages), 2)
        highest = max(averages)
        lowest = min(averages)
    else:
        class_average = None
        highest = None
        lowest = None

    # Grade distribution
    grade_distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    for avg in averages:
        if avg >= 90:
            grade_distribution["A"] += 1
        elif avg >= 80:
            grade_distribution["B"] += 1
        elif avg >= 70:
            grade_distribution["C"] += 1
        elif avg >= 60:
            grade_distribution["D"] += 1
        else:
            grade_distribution["F"] += 1

    return {
        "class_id": str(class_id),
        "subject_id": str(subject_id),
        "total_students": total_students,
        "graded_students": len(student_averages),
        "class_average": class_average,
        "highest_grade": highest,
        "lowest_grade": lowest,
        "grade_distribution": grade_distribution
    }


@router.post("/term-grade")
async def calculate_and_save_term_grade(
    data: TermGradeCreate,
    grading_scale_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Calculate and save a term grade for a student"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    # Calculate grade
    grade_data = await calculate_student_grade(
        data.student_id,
        data.class_id,
        data.subject_id,
        data.term_id,
        grading_scale_id,
        current_user,
        supabase
    )

    # Check if term grade already exists
    existing = supabase.table("term_grades").select("id").eq(
        "student_id", str(data.student_id)
    ).eq("class_id", str(data.class_id)).eq(
        "subject_id", str(data.subject_id)
    ).eq("term_id", str(data.term_id) if data.term_id else None).execute()

    term_grade_data = {
        "school_id": school_id,
        "student_id": str(data.student_id),
        "class_id": str(data.class_id),
        "subject_id": str(data.subject_id),
        "term_id": str(data.term_id) if data.term_id else None,
        "raw_average": grade_data["raw_average"],
        "weighted_average": grade_data["weighted_average"],
        "final_percentage": grade_data["final_percentage"],
        "final_letter_grade": grade_data["letter_grade"],
        "gpa_points": grade_data["gpa_points"],
        "status": "calculated",
        "teacher_comment": data.teacher_comment,
        "conduct_grade": data.conduct_grade,
        "effort_grade": data.effort_grade
    }

    if existing.data:
        # Update existing
        result = supabase.table("term_grades").update(
            term_grade_data
        ).eq("id", existing.data[0]["id"]).execute()
    else:
        # Insert new
        result = supabase.table("term_grades").insert(term_grade_data).execute()

    return result.data[0] if result.data else None


@router.post("/class/{class_id}/subject/{subject_id}/calculate-all")
async def calculate_all_term_grades(
    class_id: UUID,
    subject_id: UUID,
    term_id: Optional[UUID] = None,
    grading_scale_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Calculate and save term grades for all students in a class"""
    school_id = current_user.get("school_id")

    # Get all students in class
    students_result = supabase.table("students").select(
        "id"
    ).eq("class_id", str(class_id)).eq("status", "active").execute()

    students = students_result.data or []
    processed = 0

    for student in students:
        try:
            await calculate_and_save_term_grade(
                TermGradeCreate(
                    student_id=UUID(student["id"]),
                    class_id=class_id,
                    subject_id=subject_id,
                    term_id=term_id
                ),
                grading_scale_id,
                current_user,
                supabase
            )
            processed += 1
        except Exception as e:
            logger.error(f"Error calculating grade for student {student['id']}: {e}")

    return {
        "success": True,
        "total_students": len(students),
        "processed": processed
    }


@router.post("/term-grade/{term_grade_id}/finalize")
async def finalize_term_grade(
    term_grade_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Finalize a term grade (locks it from further changes)"""
    user_id = current_user["id"]

    result = supabase.table("term_grades").update({
        "status": "finalized",
        "finalized_by": user_id,
        "finalized_at": datetime.utcnow().isoformat()
    }).eq("id", str(term_grade_id)).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Term grade not found")

    return result.data[0]


@router.get("/student/{student_id}/gpa")
async def calculate_student_gpa(
    student_id: UUID,
    academic_year_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Calculate GPA for a student"""
    query = supabase.table("term_grades").select(
        "gpa_points, final_percentage"
    ).eq("student_id", str(student_id)).eq("status", "finalized")

    if academic_year_id:
        query = query.eq("academic_year_id", str(academic_year_id))

    result = query.execute()
    grades = result.data or []

    if not grades:
        return {
            "student_id": str(student_id),
            "gpa": None,
            "grades_count": 0,
            "message": "No finalized grades found"
        }

    # Calculate GPA
    gpa_points = [g["gpa_points"] for g in grades if g.get("gpa_points") is not None]

    if not gpa_points:
        return {
            "student_id": str(student_id),
            "gpa": None,
            "grades_count": len(grades),
            "message": "No GPA points available"
        }

    gpa = round(sum(gpa_points) / len(gpa_points), 2)

    return {
        "student_id": str(student_id),
        "gpa": gpa,
        "grades_count": len(grades),
        "average_percentage": round(
            sum(g["final_percentage"] for g in grades if g.get("final_percentage")) / len(grades),
            2
        ) if grades else None
    }
