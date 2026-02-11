"""
EduCore Backend - Schools Management API Endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional, List
from datetime import datetime

from app.models import (
    SchoolCreate,
    SchoolResponse,
    GradeCreate,
    GradeResponse,
    ClassCreate,
    ClassResponse,
    SubjectCreate,
    SubjectResponse,
)
from app.core.security import (
    get_current_user,
    require_system_admin,
    require_principal,
    require_office_admin,
)
from app.db.supabase import supabase_admin


router = APIRouter(prefix="/schools", tags=["Schools"])


# ============== SCHOOL MANAGEMENT (System Admin) ==============

@router.get("", response_model=List[SchoolResponse])
async def list_schools(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(require_system_admin),
):
    """List all schools (System Admin only)"""
    if supabase_admin:
        result = supabase_admin.table("schools").select("*").range(skip, skip + limit - 1).order("created_at", desc=True).execute()
        return result.data
    else:
        return [
            {
                "id": "mock-school-1",
                "name": "Demo Primary School",
                "address": "123 Education Street",
                "phone": "+1234567890",
                "email": "admin@demoschool.edu",
                "logo_url": None,
                "is_active": True,
                "created_at": datetime.now().isoformat(),
            }
        ]


@router.post("", response_model=SchoolResponse, status_code=status.HTTP_201_CREATED)
async def create_school(
    school_data: SchoolCreate,
    current_user: dict = Depends(require_system_admin),
):
    """Create a new school/tenant (System Admin only)"""
    school_dict = {
        "name": school_data.name,
        "address": school_data.address,
        "phone": school_data.phone,
        "email": school_data.email,
        "logo_url": school_data.logo_url,
        "is_active": True,
    }
    
    if supabase_admin:
        result = supabase_admin.table("schools").insert(school_dict).execute()
        return result.data[0]
    else:
        return {**school_dict, "id": "mock-new-school", "created_at": datetime.now().isoformat()}


@router.get("/current", response_model=SchoolResponse)
async def get_current_school(
    current_user: dict = Depends(get_current_user),
):
    """Get the current user's school"""
    school_id = current_user.get("school_id")
    
    if not school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with a school"
        )
    
    if supabase_admin:
        result = supabase_admin.table("schools").select("*").eq("id", school_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="School not found"
            )
        
        return result.data[0]
    else:
        return {
            "id": school_id,
            "name": "Demo Primary School",
            "address": "123 Education Street",
            "is_active": True,
        }


# ============== GRADES ==============

@router.get("/grades", response_model=List[GradeResponse])
async def list_grades(
    current_user: dict = Depends(get_current_user),
):
    """List all grades for the current school"""
    school_id = current_user.get("school_id")
    
    if supabase_admin:
        result = supabase_admin.table("grades").select("*").eq("school_id", school_id).order("order").execute()
        return result.data
    else:
        return [
            {"id": f"grade-{i}", "school_id": school_id, "name": f"Grade {i}", "order": i}
            for i in range(1, 13)
        ]


@router.post("/grades", response_model=GradeResponse, status_code=status.HTTP_201_CREATED)
async def create_grade(
    grade_data: GradeCreate,
    current_user: dict = Depends(require_principal),
):
    """Create a new grade level"""
    school_id = current_user.get("school_id")
    
    grade_dict = {
        "school_id": school_id,
        "name": grade_data.name,
        "order": grade_data.order,
    }
    
    if supabase_admin:
        result = supabase_admin.table("grades").insert(grade_dict).execute()
        return result.data[0]
    else:
        return {**grade_dict, "id": "mock-new-grade", "created_at": datetime.now().isoformat()}


# ============== CLASSES ==============

@router.get("/classes", response_model=List[ClassResponse])
async def list_classes(
    grade_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """List all classes for the current school"""
    school_id = current_user.get("school_id")
    
    if supabase_admin:
        query = supabase_admin.table("classes").select("*").eq("school_id", school_id)
        
        if grade_id:
            query = query.eq("grade_id", grade_id)
        
        result = query.order("name").execute()
        return result.data
    else:
        return [
            {"id": "class-1a", "school_id": school_id, "name": "A", "grade_id": "grade-1", "teacher_id": None},
            {"id": "class-1b", "school_id": school_id, "name": "B", "grade_id": "grade-1", "teacher_id": None},
        ]


@router.post("/classes", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
async def create_class(
    class_data: ClassCreate,
    current_user: dict = Depends(require_principal),
):
    """Create a new class section"""
    school_id = current_user.get("school_id")
    
    class_dict = {
        "school_id": school_id,
        "name": class_data.name,
        "grade_id": class_data.grade_id,
        "teacher_id": class_data.teacher_id,
    }
    
    if supabase_admin:
        # Verify grade belongs to school
        grade = supabase_admin.table("grades").select("id").eq("id", class_data.grade_id).eq("school_id", school_id).execute()
        
        if not grade.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grade not found"
            )
        
        result = supabase_admin.table("classes").insert(class_dict).execute()
        return result.data[0]
    else:
        return {**class_dict, "id": "mock-new-class", "created_at": datetime.now().isoformat()}


# ============== SUBJECTS ==============

@router.get("/subjects", response_model=List[SubjectResponse])
async def list_subjects(
    current_user: dict = Depends(get_current_user),
):
    """List all subjects for the current school"""
    school_id = current_user.get("school_id")
    
    if supabase_admin:
        result = supabase_admin.table("subjects").select("*").eq("school_id", school_id).order("name").execute()
        return result.data
    else:
        return [
            {"id": "subj-1", "school_id": school_id, "name": "Mathematics", "code": "MATH"},
            {"id": "subj-2", "school_id": school_id, "name": "English", "code": "ENG"},
            {"id": "subj-3", "school_id": school_id, "name": "Science", "code": "SCI"},
        ]


@router.post("/subjects", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(
    subject_data: SubjectCreate,
    current_user: dict = Depends(require_principal),
):
    """Create a new subject"""
    school_id = current_user.get("school_id")
    
    subject_dict = {
        "school_id": school_id,
        "name": subject_data.name,
        "code": subject_data.code,
    }
    
    if supabase_admin:
        result = supabase_admin.table("subjects").insert(subject_dict).execute()
        return result.data[0]
    else:
        return {**subject_dict, "id": "mock-new-subject", "created_at": datetime.now().isoformat()}
