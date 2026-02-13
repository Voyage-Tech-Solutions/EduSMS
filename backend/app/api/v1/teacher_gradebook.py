from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import csv
import io
from app.models.teacher import CreateAssessmentRequest, ImportMarksRequest, LockGradebookRequest, AssessmentScore
from app.core.auth import get_current_user, get_user_school_id
from app.db.supabase import get_supabase_admin

router = APIRouter(prefix="/teacher/gradebook", tags=["teacher-gradebook"])

@router.get("")
async def get_gradebook(
    class_id: UUID,
    subject_id: UUID,
    term_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get gradebook spreadsheet data"""
    supabase = get_supabase_admin()
    school_id = get_user_school_id(current_user)
    
    # Check if gradebook is locked
    lock_check = supabase.table("gradebook_locks").select("*").eq(
        "class_id", str(class_id)
    ).eq("subject_id", str(subject_id)).eq("term_id", str(term_id) if term_id else None).execute()
    
    is_locked = len(lock_check.data) > 0
    
    # Get students in class
    students = supabase.table("students").select("""
        id, admission_number, first_name, last_name
    """).eq("class_id", str(class_id)).eq("status", "active").order("admission_number").execute()
    
    # Get assessments
    assessments_query = supabase.table("assessments").select("*").eq(
        "class_id", str(class_id)
    ).eq("subject_id", str(subject_id))
    
    if term_id:
        assessments_query = assessments_query.eq("term_id", str(term_id))
    
    assessments = assessments_query.order("date_assigned").execute()
    
    # Get all scores
    assessment_ids = [a["id"] for a in assessments.data]
    scores = {}
    if assessment_ids:
        scores_result = supabase.table("assessment_scores").select("*").in_(
            "assessment_id", assessment_ids
        ).execute()
        
        for score in scores_result.data:
            key = f"{score['student_id']}_{score['assessment_id']}"
            scores[key] = score
    
    # Build spreadsheet data
    rows = []
    for student in students.data:
        row = {
            "student_id": student["id"],
            "admission_number": student["admission_number"],
            "name": f"{student['first_name']} {student['last_name']}",
            "scores": {},
            "total": 0,
            "average": 0,
            "rank": 0
        }
        
        total_marks = 0
        total_possible = 0
        
        for assessment in assessments.data:
            key = f"{student['id']}_{assessment['id']}"
            score_data = scores.get(key)
            
            if score_data and score_data["score"] is not None:
                row["scores"][assessment["id"]] = score_data["score"]
                total_marks += score_data["score"]
                total_possible += assessment["total_marks"]
            else:
                row["scores"][assessment["id"]] = None
        
        if total_possible > 0:
            row["average"] = round((total_marks / total_possible) * 100, 2)
        
        rows.append(row)
    
    # Calculate ranks
    rows.sort(key=lambda x: x["average"], reverse=True)
    for i, row in enumerate(rows):
        row["rank"] = i + 1
    
    return {
        "is_locked": is_locked,
        "assessments": assessments.data,
        "students": rows
    }

@router.post("/assessments")
async def create_assessment(
    request: CreateAssessmentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create new assessment"""
    supabase = get_supabase_admin()
    school_id = get_user_school_id(current_user)
    
    # Create assessment
    assessment = supabase.table("assessments").insert({
        "school_id": school_id,
        "teacher_id": current_user["id"],
        "class_id": str(request.class_id),
        "subject_id": str(request.subject_id),
        "term_id": str(request.term_id),
        "type": request.type,
        "title": request.title,
        "total_marks": request.total_marks,
        "date_assigned": str(request.date_assigned) if request.date_assigned else None,
        "due_date": str(request.due_date) if request.due_date else None,
        "status": "published"
    }).execute()
    
    # Pre-generate score rows for all students
    students = supabase.table("students").select("id").eq(
        "class_id", str(request.class_id)
    ).eq("status", "active").execute()
    
    score_rows = [{
        "assessment_id": assessment.data[0]["id"],
        "student_id": student["id"],
        "score": None
    } for student in students.data]
    
    if score_rows:
        supabase.table("assessment_scores").insert(score_rows).execute()
    
    return {"message": "Assessment created", "assessment_id": assessment.data[0]["id"]}

@router.patch("/assessments/{assessment_id}")
async def update_assessment(
    assessment_id: UUID,
    request: CreateAssessmentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update assessment"""
    supabase = get_supabase_admin()
    
    result = supabase.table("assessments").update({
        "title": request.title,
        "type": request.type,
        "total_marks": request.total_marks,
        "date_assigned": str(request.date_assigned) if request.date_assigned else None,
        "due_date": str(request.due_date) if request.due_date else None
    }).eq("id", str(assessment_id)).eq("teacher_id", current_user["id"]).execute()
    
    return {"message": "Assessment updated"}

@router.post("/assessments/{assessment_id}/scores")
async def save_scores(
    assessment_id: UUID,
    scores: List[AssessmentScore],
    current_user: dict = Depends(get_current_user)
):
    """Save assessment scores (bulk)"""
    supabase = get_supabase_admin()
    
    # Get assessment to validate total_marks
    assessment = supabase.table("assessments").select("total_marks").eq(
        "id", str(assessment_id)
    ).single().execute()
    
    # Update scores
    for score in scores:
        if score.score is not None and score.score > assessment.data["total_marks"]:
            raise HTTPException(status_code=400, detail=f"Score exceeds total marks for student {score.student_id}")
        
        percentage = (score.score / assessment.data["total_marks"] * 100) if score.score is not None else None
        
        supabase.table("assessment_scores").update({
            "score": score.score,
            "percentage": percentage,
            "marked_by": current_user["id"],
            "marked_at": datetime.now().isoformat()
        }).eq("assessment_id", str(assessment_id)).eq("student_id", str(score.student_id)).execute()
    
    return {"message": f"Saved {len(scores)} scores"}

@router.post("/assessments/{assessment_id}/import")
async def import_marks(
    assessment_id: UUID,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Import marks from CSV"""
    supabase = get_supabase_admin()
    
    # Read CSV
    content = await file.read()
    csv_file = io.StringIO(content.decode('utf-8'))
    reader = csv.DictReader(csv_file)
    
    # Get assessment
    assessment = supabase.table("assessments").select("total_marks").eq(
        "id", str(assessment_id)
    ).single().execute()
    
    # Validate and import
    errors = []
    imported = 0
    
    for row in reader:
        admission_number = row.get("admission_number")
        score = row.get("score")
        
        if not admission_number or not score:
            errors.append(f"Missing data in row: {row}")
            continue
        
        try:
            score_value = float(score)
            if score_value > assessment.data["total_marks"]:
                errors.append(f"Score {score_value} exceeds total marks for {admission_number}")
                continue
            
            # Get student
            student = supabase.table("students").select("id").eq(
                "admission_number", admission_number
            ).single().execute()
            
            if not student.data:
                errors.append(f"Student not found: {admission_number}")
                continue
            
            # Update score
            percentage = (score_value / assessment.data["total_marks"]) * 100
            supabase.table("assessment_scores").update({
                "score": score_value,
                "percentage": percentage,
                "marked_by": current_user["id"],
                "marked_at": datetime.now().isoformat()
            }).eq("assessment_id", str(assessment_id)).eq("student_id", student.data["id"]).execute()
            
            imported += 1
            
        except Exception as e:
            errors.append(f"Error processing {admission_number}: {str(e)}")
    
    return {
        "message": f"Imported {imported} marks",
        "imported": imported,
        "errors": errors
    }

@router.post("/lock")
async def lock_gradebook(
    request: LockGradebookRequest,
    current_user: dict = Depends(get_current_user)
):
    """Lock gradebook"""
    supabase = get_supabase_admin()
    school_id = get_user_school_id(current_user)
    
    # Check if already locked
    existing = supabase.table("gradebook_locks").select("id").eq(
        "class_id", str(request.class_id)
    ).eq("subject_id", str(request.subject_id)).eq("term_id", str(request.term_id)).execute()
    
    if existing.data:
        raise HTTPException(status_code=400, detail="Gradebook already locked")
    
    # Create lock
    supabase.table("gradebook_locks").insert({
        "school_id": school_id,
        "class_id": str(request.class_id),
        "subject_id": str(request.subject_id),
        "term_id": str(request.term_id),
        "locked_by": current_user["id"],
        "reason": request.reason
    }).execute()
    
    return {"message": "Gradebook locked successfully"}

@router.post("/unlock-request")
async def request_unlock(
    class_id: UUID,
    subject_id: UUID,
    term_id: UUID,
    reason: str,
    current_user: dict = Depends(get_current_user)
):
    """Request gradebook unlock"""
    supabase = get_supabase_admin()
    school_id = get_user_school_id(current_user)
    
    # Update lock record
    supabase.table("gradebook_locks").update({
        "unlock_requested": True,
        "unlock_requested_at": datetime.now().isoformat()
    }).eq("class_id", str(class_id)).eq("subject_id", str(subject_id)).eq("term_id", str(term_id)).execute()
    
    # Create approval request
    supabase.table("approval_requests").insert({
        "school_id": school_id,
        "type": "policy_override",
        "entity_type": "gradebook_lock",
        "entity_id": str(class_id),
        "requested_by": current_user["id"],
        "priority": "normal",
        "metadata": {
            "description": f"Unlock gradebook: {reason}",
            "class_id": str(class_id),
            "subject_id": str(subject_id),
            "term_id": str(term_id)
        }
    }).execute()
    
    return {"message": "Unlock request submitted for approval"}

@router.get("/export")
async def export_gradebook(
    class_id: UUID,
    subject_id: UUID,
    term_id: Optional[UUID] = None,
    format: str = "csv",
    current_user: dict = Depends(get_current_user)
):
    """Export gradebook"""
    # Get gradebook data
    data = await get_gradebook(class_id, subject_id, term_id, current_user)
    
    if format == "csv":
        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        header = ["Admission #", "Name"]
        for assessment in data["assessments"]:
            header.append(assessment["title"])
        header.extend(["Total", "Average %", "Rank"])
        writer.writerow(header)
        
        # Rows
        for student in data["students"]:
            row = [student["admission_number"], student["name"]]
            for assessment in data["assessments"]:
                score = student["scores"].get(assessment["id"])
                row.append(score if score is not None else "")
            row.extend([student.get("total", ""), student["average"], student["rank"]])
            writer.writerow(row)
        
        return {"content": output.getvalue(), "filename": f"gradebook_{class_id}.csv"}
    
    return {"message": "PDF export - implement with reportlab"}
