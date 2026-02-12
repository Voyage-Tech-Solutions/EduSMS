"""
EduCore Backend - Assessments API
Academic performance tracking and grade management
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional, Dict, Any, List
from datetime import datetime, date

from app.core.security import get_current_user, require_teacher
from app.db.supabase import supabase_admin

router = APIRouter()


@router.get("")
async def list_assessments(
    term_id: Optional[str] = None,
    grade_id: Optional[str] = None,
    class_id: Optional[str] = None,
    subject_id: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: dict = Depends(require_teacher),
):
    """List assessments with filters"""
    school_id = current_user.get("school_id")
    
    if not supabase_admin:
        return []
    
    query = supabase_admin.table("assessments").select("*").eq("school_id", school_id)
    
    if term_id:
        query = query.eq("term_id", term_id)
    if grade_id:
        query = query.eq("grade_id", grade_id)
    if class_id:
        query = query.eq("class_id", class_id)
    if subject_id:
        query = query.eq("subject_id", subject_id)
    if status_filter:
        query = query.eq("status", status_filter)
    
    result = query.order("created_at", desc=True).execute()
    return result.data


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_assessment(
    assessment_data: Dict[str, Any],
    current_user: dict = Depends(require_teacher),
):
    """Create new assessment"""
    school_id = current_user.get("school_id")
    user_id = current_user.get("id")
    
    assessment_dict = {
        "school_id": school_id,
        "term_id": assessment_data.get("term_id"),
        "grade_id": assessment_data.get("grade_id"),
        "class_id": assessment_data.get("class_id"),
        "subject_id": assessment_data["subject_id"],
        "teacher_id": user_id,
        "type": assessment_data["type"],
        "title": assessment_data["title"],
        "total_marks": assessment_data["total_marks"],
        "date_assigned": assessment_data.get("date_assigned"),
        "due_date": assessment_data.get("due_date"),
        "status": "draft"
    }
    
    if not supabase_admin:
        return {**assessment_dict, "id": "mock-assessment"}
    
    result = supabase_admin.table("assessments").insert(assessment_dict).execute()
    return result.data[0]


@router.post("/{assessment_id}/publish")
async def publish_assessment(
    assessment_id: str,
    current_user: dict = Depends(require_teacher),
):
    """Publish assessment"""
    if not supabase_admin:
        return {"id": assessment_id, "status": "published"}
    
    result = supabase_admin.table("assessments").update({
        "status": "published"
    }).eq("id", assessment_id).execute()
    
    return result.data[0] if result.data else {}


@router.post("/{assessment_id}/scores")
async def record_scores(
    assessment_id: str,
    scores_data: Dict[str, Any],
    current_user: dict = Depends(require_teacher),
):
    """Record scores for assessment"""
    user_id = current_user.get("id")
    
    if not supabase_admin:
        return {"message": "Scores recorded"}
    
    # Get assessment to get total_marks
    assessment = supabase_admin.table("assessments").select("total_marks").eq("id", assessment_id).execute()
    if not assessment.data:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    total_marks = float(assessment.data[0]["total_marks"])
    
    scores = []
    for record in scores_data.get("scores", []):
        score = float(record["score"])
        percentage = round((score / total_marks * 100), 2)
        
        score_dict = {
            "assessment_id": assessment_id,
            "student_id": record["student_id"],
            "score": score,
            "percentage": percentage,
            "marked_by": user_id,
            "marked_at": datetime.now().isoformat()
        }
        scores.append(score_dict)
    
    result = supabase_admin.table("assessment_scores").upsert(scores, on_conflict="assessment_id,student_id").execute()
    return {"message": f"{len(scores)} scores recorded", "data": result.data}


@router.get("/{assessment_id}/scores")
async def get_assessment_scores(
    assessment_id: str,
    current_user: dict = Depends(require_teacher),
):
    """Get scores for assessment"""
    if not supabase_admin:
        return []
    
    result = supabase_admin.table("assessment_scores").select(
        "*, students(first_name, last_name, admission_number)"
    ).eq("assessment_id", assessment_id).execute()
    
    return result.data
