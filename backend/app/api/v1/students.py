"""
EduCore Backend - Students API Endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional, List
from datetime import datetime
import uuid

from app.models import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    StudentStatus,
    GuardianCreate,
    GuardianResponse,
)
from app.core.security import get_current_user, require_office_admin, require_teacher
from app.db.supabase import supabase_admin
from app.db.tenant import get_tenant


router = APIRouter(prefix="/students", tags=["Students"])


def generate_admission_number(school_id: str) -> str:
    """Generate unique admission number"""
    year = datetime.now().year
    short_id = str(uuid.uuid4())[:6].upper()
    return f"STU-{year}-{short_id}"


@router.get("", response_model=List[StudentResponse])
async def list_students(
    grade_id: Optional[str] = None,
    class_id: Optional[str] = None,
    status: Optional[StudentStatus] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(require_teacher),
):
    """List all students for the current school with optional filters"""
    school_id = current_user.get("school_id")
    
    if not school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="School context required"
        )
    
    if supabase_admin:
        query = supabase_admin.table("students").select("*").eq("school_id", school_id)
        
        if grade_id:
            query = query.eq("grade_id", grade_id)
        if class_id:
            query = query.eq("class_id", class_id)
        if status:
            query = query.eq("status", status.value)
        if search:
            query = query.or_(f"first_name.ilike.%{search}%,last_name.ilike.%{search}%,admission_number.ilike.%{search}%")
        
        result = query.range(skip, skip + limit - 1).order("created_at", desc=True).execute()
        return result.data
    else:
        # Mock data for development
        return [
            {
                "id": "mock-student-1",
                "school_id": school_id,
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "2010-05-15",
                "gender": "male",
                "admission_number": "STU-2024-ABC123",
                "grade_id": "grade-1",
                "class_id": "class-1a",
                "status": "active",
                "created_at": datetime.now().isoformat(),
            }
        ]


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    student_data: StudentCreate,
    current_user: dict = Depends(require_office_admin),
):
    """Create a new student"""
    school_id = current_user.get("school_id")
    
    if not school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="School context required"
        )
    
    admission_number = generate_admission_number(school_id)
    
    student_dict = {
        "school_id": school_id,
        "first_name": student_data.first_name,
        "last_name": student_data.last_name,
        "date_of_birth": student_data.date_of_birth.isoformat(),
        "gender": student_data.gender.value,
        "admission_number": admission_number,
        "grade_id": student_data.grade_id,
        "class_id": student_data.class_id,
        "status": StudentStatus.ACTIVE.value,
    }
    
    if supabase_admin:
        result = supabase_admin.table("students").insert(student_dict).execute()
        return result.data[0]
    else:
        return {**student_dict, "id": "mock-new-student", "created_at": datetime.now().isoformat()}


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: str,
    current_user: dict = Depends(require_teacher),
):
    """Get a specific student by ID"""
    school_id = current_user.get("school_id")
    
    if supabase_admin:
        result = supabase_admin.table("students").select("*").eq("id", student_id).eq("school_id", school_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        return result.data[0]
    else:
        return {
            "id": student_id,
            "school_id": school_id,
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "2010-05-15",
            "gender": "male",
            "admission_number": "STU-2024-ABC123",
            "status": "active",
        }


@router.patch("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: str,
    student_data: StudentUpdate,
    current_user: dict = Depends(require_office_admin),
):
    """Update a student's information"""
    school_id = current_user.get("school_id")
    
    update_data = {k: v for k, v in student_data.model_dump().items() if v is not None}
    
    if "gender" in update_data:
        update_data["gender"] = update_data["gender"].value
    if "status" in update_data:
        update_data["status"] = update_data["status"].value
    if "date_of_birth" in update_data:
        update_data["date_of_birth"] = update_data["date_of_birth"].isoformat()
    
    if supabase_admin:
        # Verify student exists and belongs to school
        existing = supabase_admin.table("students").select("id").eq("id", student_id).eq("school_id", school_id).execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        result = supabase_admin.table("students").update(update_data).eq("id", student_id).execute()
        return result.data[0]
    else:
        return {
            "id": student_id,
            "school_id": school_id,
            **update_data,
        }


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
    student_id: str,
    current_user: dict = Depends(require_office_admin),
):
    """Soft delete a student (set status to inactive)"""
    school_id = current_user.get("school_id")
    
    if supabase_admin:
        existing = supabase_admin.table("students").select("id").eq("id", student_id).eq("school_id", school_id).execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        supabase_admin.table("students").update({"status": StudentStatus.INACTIVE.value}).eq("id", student_id).execute()


# ============== GUARDIANS ==============

@router.get("/{student_id}/guardians", response_model=List[GuardianResponse])
async def list_guardians(
    student_id: str,
    current_user: dict = Depends(require_teacher),
):
    """List all guardians for a student"""
    school_id = current_user.get("school_id")
    
    if supabase_admin:
        student = supabase_admin.table("students").select("id").eq("id", student_id).eq("school_id", school_id).execute()
        if not student.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
        result = supabase_admin.table("guardians").select("*").eq("student_id", student_id).execute()
        return result.data
    return []


@router.post("/{student_id}/guardians", response_model=GuardianResponse, status_code=status.HTTP_201_CREATED)
async def add_guardian(
    student_id: str,
    guardian_data: GuardianCreate,
    current_user: dict = Depends(require_office_admin),
):
    """Add a guardian to a student"""
    school_id = current_user.get("school_id")
    guardian_dict = {
        "student_id": student_id,
        "first_name": guardian_data.first_name,
        "last_name": guardian_data.last_name,
        "relationship": guardian_data.relationship,
        "phone": guardian_data.phone,
        "email": guardian_data.email,
        "is_primary": guardian_data.is_primary,
    }
    if supabase_admin:
        student = supabase_admin.table("students").select("id").eq("id", student_id).eq("school_id", school_id).execute()
        if not student.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
        result = supabase_admin.table("guardians").insert(guardian_dict).execute()
        return result.data[0]
    return {**guardian_dict, "id": "mock-new-guardian"}


# ============== DOCUMENTS ==============

@router.get("/{student_id}/documents")
async def list_student_documents(
    student_id: str,
    current_user: dict = Depends(require_teacher),
):
    """List documents for a student"""
    school_id = current_user.get("school_id")
    if supabase_admin:
        student = supabase_admin.table("students").select("id").eq("id", student_id).eq("school_id", school_id).execute()
        if not student.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
        result = supabase_admin.table("student_documents").select("*").eq("student_id", student_id).execute()
        return result.data
    return []


@router.post("/{student_id}/documents")
async def add_student_document(
    student_id: str,
    document_data: dict,
    current_user: dict = Depends(require_office_admin),
):
    """Add document to student"""
    school_id = current_user.get("school_id")
    if supabase_admin:
        student = supabase_admin.table("students").select("id").eq("id", student_id).eq("school_id", school_id).execute()
        if not student.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
        doc_dict = {
            "student_id": student_id,
            "document_type": document_data["document_type"],
            "file_url": document_data.get("file_url"),
            "uploaded": document_data.get("uploaded", False),
            "verified": document_data.get("verified", False)
        }
        result = supabase_admin.table("student_documents").insert(doc_dict).execute()
        return result.data[0]
    return {"id": "mock-doc", **document_data}


@router.patch("/documents/{document_id}")
async def update_student_document(
    document_id: str,
    update_data: dict,
    current_user: dict = Depends(require_office_admin),
):
    """Update/verify document"""
    user_id = current_user.get("id")
    if update_data.get("verified"):
        update_data["verified_by"] = user_id
        update_data["verified_at"] = datetime.now().isoformat()
    if supabase_admin:
        result = supabase_admin.table("student_documents").update(update_data).eq("id", document_id).execute()
        if not result.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return result.data[0]
    return {"id": document_id, **update_data}


@router.get("/export")
async def export_students(
    format: str = Query("csv", regex="^(csv|pdf)$"),
    grade_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(require_office_admin),
):
    """Export students data"""
    return {"message": "Export functionality", "format": format}
