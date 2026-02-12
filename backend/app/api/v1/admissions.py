"""
EduCore Backend - Admissions API Endpoints
Complete workflow for application management
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import uuid

from app.core.security import get_current_user, require_office_admin
from app.db.supabase import supabase_admin

router = APIRouter(prefix="/admissions", tags=["Admissions"])


def generate_application_number(school_id: str) -> str:
    """Generate unique application number"""
    year = datetime.now().year
    short_id = str(uuid.uuid4())[:6].upper()
    return f"APP-{year}-{short_id}"


@router.get("/stats")
async def get_admissions_stats(
    term_id: Optional[str] = None,
    current_user: dict = Depends(require_office_admin),
):
    """Get admissions statistics"""
    school_id = current_user.get("school_id")
    
    if not supabase_admin:
        return {
            "total": 0, "pending": 0, "under_review": 0,
            "approved": 0, "enrolled": 0, "declined": 0
        }
    
    query = supabase_admin.table("admissions_applications").select("status", count="exact").eq("school_id", school_id)
    if term_id:
        query = query.eq("term_id", term_id)
    
    result = query.execute()
    
    stats = {"total": 0, "incomplete": 0, "pending": 0, "under_review": 0, "approved": 0, "enrolled": 0, "declined": 0, "withdrawn": 0}
    for app in result.data:
        stats["total"] += 1
        stats[app["status"]] = stats.get(app["status"], 0) + 1
    
    return stats


@router.get("")
async def list_applications(
    status_filter: Optional[str] = Query(None, alias="status"),
    term_id: Optional[str] = None,
    grade_id: Optional[str] = None,
    q: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(require_office_admin),
):
    """List all applications with filters"""
    school_id = current_user.get("school_id")
    
    if not supabase_admin:
        return {"data": [], "total": 0, "page": skip // limit + 1, "page_size": limit}
    
    query = supabase_admin.table("admissions_applications").select("*", count="exact").eq("school_id", school_id)
    
    if status_filter:
        query = query.eq("status", status_filter)
    if term_id:
        query = query.eq("term_id", term_id)
    if grade_id:
        query = query.eq("grade_applied_id", grade_id)
    if q:
        query = query.or_(f"student_first_name.ilike.%{q}%,student_last_name.ilike.%{q}%,application_no.ilike.%{q}%")
    
    result = query.range(skip, skip + limit - 1).order("created_at", desc=True).execute()
    
    return {
        "data": result.data,
        "total": result.count or 0,
        "page": skip // limit + 1,
        "page_size": limit
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_application(
    application_data: Dict[str, Any],
    current_user: dict = Depends(require_office_admin),
):
    """Create a new admission application"""
    school_id = current_user.get("school_id")
    
    app_dict = {
        "school_id": school_id,
        "application_no": generate_application_number(school_id),
        "student_first_name": application_data["student_first_name"],
        "student_last_name": application_data["student_last_name"],
        "student_dob": application_data["student_dob"],
        "gender": application_data.get("gender", "male"),
        "grade_applied_id": application_data.get("grade_applied_id"),
        "term_id": application_data.get("term_id"),
        "status": "incomplete",
    }
    
    if not supabase_admin:
        return {**app_dict, "id": "mock-app-id", "created_at": datetime.now().isoformat()}
    
    result = supabase_admin.table("admissions_applications").insert(app_dict).execute()
    return result.data[0]


@router.get("/{application_id}")
async def get_application(
    application_id: str,
    current_user: dict = Depends(require_office_admin),
):
    """Get specific application details"""
    school_id = current_user.get("school_id")
    
    if not supabase_admin:
        return {"id": application_id, "school_id": school_id, "status": "pending"}
    
    result = supabase_admin.table("admissions_applications").select("*").eq("id", application_id).eq("school_id", school_id).execute()
    
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    
    return result.data[0]


@router.patch("/{application_id}")
async def update_application(
    application_id: str,
    update_data: Dict[str, Any],
    current_user: dict = Depends(require_office_admin),
):
    """Update application details"""
    school_id = current_user.get("school_id")
    
    if not supabase_admin:
        return {"id": application_id, **update_data}
    
    # Verify ownership
    existing = supabase_admin.table("admissions_applications").select("id").eq("id", application_id).eq("school_id", school_id).execute()
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    
    result = supabase_admin.table("admissions_applications").update(update_data).eq("id", application_id).execute()
    return result.data[0]


@router.post("/{application_id}/submit")
async def submit_application(
    application_id: str,
    current_user: dict = Depends(require_office_admin),
):
    """Submit application (change status from incomplete to pending)"""
    school_id = current_user.get("school_id")
    
    if not supabase_admin:
        return {"id": application_id, "status": "pending"}
    
    result = supabase_admin.table("admissions_applications").update({
        "status": "pending",
        "submitted_at": datetime.now().isoformat()
    }).eq("id", application_id).eq("school_id", school_id).execute()
    
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    
    return result.data[0]


@router.post("/{application_id}/start-review")
async def start_review(
    application_id: str,
    current_user: dict = Depends(require_office_admin),
):
    """Start reviewing an application"""
    school_id = current_user.get("school_id")
    user_id = current_user.get("id")
    
    if not supabase_admin:
        return {"id": application_id, "status": "under_review"}
    
    result = supabase_admin.table("admissions_applications").update({
        "status": "under_review",
        "reviewer_id": user_id
    }).eq("id", application_id).eq("school_id", school_id).execute()
    
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    
    return result.data[0]


@router.post("/{application_id}/approve")
async def approve_application(
    application_id: str,
    approval_data: Dict[str, Any],
    current_user: dict = Depends(require_office_admin),
):
    """Approve an application"""
    school_id = current_user.get("school_id")
    user_id = current_user.get("id")
    
    if not supabase_admin:
        return {"id": application_id, "status": "approved"}
    
    result = supabase_admin.table("admissions_applications").update({
        "status": "approved",
        "decision_by": user_id,
        "decision_at": datetime.now().isoformat(),
        "review_notes": approval_data.get("notes", "")
    }).eq("id", application_id).eq("school_id", school_id).execute()
    
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    
    return result.data[0]


@router.post("/{application_id}/decline")
async def decline_application(
    application_id: str,
    decline_data: Dict[str, Any],
    current_user: dict = Depends(require_office_admin),
):
    """Decline an application"""
    school_id = current_user.get("school_id")
    user_id = current_user.get("id")
    
    if not supabase_admin:
        return {"id": application_id, "status": "declined"}
    
    result = supabase_admin.table("admissions_applications").update({
        "status": "declined",
        "decision_by": user_id,
        "decision_at": datetime.now().isoformat(),
        "decision_reason": decline_data.get("reason", ""),
        "review_notes": decline_data.get("notes", "")
    }).eq("id", application_id).eq("school_id", school_id).execute()
    
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    
    return result.data[0]


@router.post("/{application_id}/enroll")
async def enroll_student(
    application_id: str,
    enrollment_data: Dict[str, Any],
    current_user: dict = Depends(require_office_admin),
):
    """Convert approved application to enrolled student"""
    school_id = current_user.get("school_id")
    
    if not supabase_admin:
        return {"id": application_id, "status": "enrolled", "student_id": "mock-student-id"}
    
    # Get application
    app_result = supabase_admin.table("admissions_applications").select("*").eq("id", application_id).eq("school_id", school_id).execute()
    if not app_result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    
    app = app_result.data[0]
    if app["status"] != "approved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only approved applications can be enrolled")
    
    # Generate admission number
    year = datetime.now().year
    short_id = str(uuid.uuid4())[:6].upper()
    admission_number = f"STU-{year}-{short_id}"
    
    # Create student record
    student_dict = {
        "school_id": school_id,
        "admission_number": admission_number,
        "first_name": app["student_first_name"],
        "last_name": app["student_last_name"],
        "date_of_birth": app["student_dob"],
        "gender": app["gender"],
        "grade_id": app["grade_applied_id"],
        "class_id": enrollment_data.get("class_id"),
        "status": "active",
        "admission_date": enrollment_data.get("admission_date", date.today().isoformat())
    }
    
    student_result = supabase_admin.table("students").insert(student_dict).execute()
    student_id = student_result.data[0]["id"]
    
    # Update application
    supabase_admin.table("admissions_applications").update({
        "status": "enrolled",
        "student_id": student_id
    }).eq("id", application_id).execute()
    
    return {"id": application_id, "status": "enrolled", "student_id": student_id}


@router.get("/{application_id}/documents")
async def get_application_documents(
    application_id: str,
    current_user: dict = Depends(require_office_admin),
):
    """Get documents for an application"""
    school_id = current_user.get("school_id")
    
    if not supabase_admin:
        return []
    
    # Verify application belongs to school
    app = supabase_admin.table("admissions_applications").select("id").eq("id", application_id).eq("school_id", school_id).execute()
    if not app.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    
    result = supabase_admin.table("admissions_documents").select("*").eq("application_id", application_id).execute()
    return result.data


@router.post("/{application_id}/documents")
async def add_application_document(
    application_id: str,
    document_data: Dict[str, Any],
    current_user: dict = Depends(require_office_admin),
):
    """Add document to application"""
    school_id = current_user.get("school_id")
    
    if not supabase_admin:
        return {"id": "mock-doc-id", **document_data}
    
    # Verify application
    app = supabase_admin.table("admissions_applications").select("id").eq("id", application_id).eq("school_id", school_id).execute()
    if not app.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    
    doc_dict = {
        "application_id": application_id,
        "document_type": document_data["document_type"],
        "file_url": document_data.get("file_url"),
        "uploaded": document_data.get("uploaded", False),
        "verified": document_data.get("verified", False)
    }
    
    result = supabase_admin.table("admissions_documents").insert(doc_dict).execute()
    return result.data[0]


@router.patch("/documents/{document_id}")
async def update_document(
    document_id: str,
    update_data: Dict[str, Any],
    current_user: dict = Depends(require_office_admin),
):
    """Update document (verify, upload, etc)"""
    user_id = current_user.get("id")
    
    if not supabase_admin:
        return {"id": document_id, **update_data}
    
    if update_data.get("verified"):
        update_data["verified_by"] = user_id
        update_data["verified_at"] = datetime.now().isoformat()
    
    result = supabase_admin.table("admissions_documents").update(update_data).eq("id", document_id).execute()
    
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    return result.data[0]


@router.get("/export")
async def export_applications(
    format: str = Query("csv", regex="^(csv|pdf)$"),
    status_filter: Optional[str] = None,
    term_id: Optional[str] = None,
    current_user: dict = Depends(require_office_admin),
):
    """Export applications data"""
    school_id = current_user.get("school_id")
    
    # This would generate actual CSV/PDF in production
    return {"message": "Export functionality - implement with pandas/reportlab", "format": format}
