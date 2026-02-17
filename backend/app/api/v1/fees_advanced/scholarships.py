"""
EduCore Backend - Scholarships API
Scholarship programs and student awards management
"""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# MODELS
# ============================================================

class ScholarshipCreate(BaseModel):
    """Create a scholarship program"""
    name: str
    description: Optional[str] = None
    scholarship_type: str = "merit"  # merit, need_based, athletic, artistic, full, partial
    amount: Optional[float] = None
    percentage: Optional[float] = None  # Percentage of fees covered
    academic_year_id: Optional[UUID] = None
    eligibility_criteria: Optional[str] = None
    max_recipients: Optional[int] = None
    application_deadline: Optional[date] = None
    is_renewable: bool = False
    renewal_criteria: Optional[str] = None


class ScholarshipUpdate(BaseModel):
    """Update a scholarship program"""
    name: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    percentage: Optional[float] = None
    eligibility_criteria: Optional[str] = None
    max_recipients: Optional[int] = None
    application_deadline: Optional[date] = None
    is_active: Optional[bool] = None


class ScholarshipAward(BaseModel):
    """Award scholarship to a student"""
    student_id: UUID
    scholarship_id: UUID
    academic_year_id: UUID
    award_amount: Optional[float] = None
    award_percentage: Optional[float] = None
    start_date: date
    end_date: Optional[date] = None
    notes: Optional[str] = None


class ScholarshipApplication(BaseModel):
    """Student scholarship application"""
    student_id: UUID
    scholarship_id: UUID
    essay: Optional[str] = None
    supporting_documents: List[str] = []
    recommendation_letters: List[str] = []


# ============================================================
# SCHOLARSHIP PROGRAM ENDPOINTS
# ============================================================

@router.get("")
async def list_scholarships(
    scholarship_type: Optional[str] = None,
    academic_year_id: Optional[UUID] = None,
    active_only: bool = True,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List scholarship programs"""
    school_id = current_user.get("school_id")

    query = supabase.table("scholarships").select("*").eq("school_id", school_id)

    if scholarship_type:
        query = query.eq("scholarship_type", scholarship_type)
    if academic_year_id:
        query = query.eq("academic_year_id", str(academic_year_id))
    if active_only:
        query = query.eq("is_active", True)

    query = query.order("name")

    result = query.execute()

    # Add recipient counts
    scholarships = result.data or []
    for sch in scholarships:
        recipients = supabase.table("student_scholarships").select(
            "id", count="exact"
        ).eq("scholarship_id", sch["id"]).eq("status", "active").execute()
        sch["current_recipients"] = recipients.count or 0

    return {"scholarships": scholarships}


@router.get("/{scholarship_id}")
async def get_scholarship(
    scholarship_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get scholarship details with recipients"""
    result = supabase.table("scholarships").select("*").eq(
        "id", str(scholarship_id)
    ).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Scholarship not found")

    scholarship = result.data

    # Get recipients
    recipients = supabase.table("student_scholarships").select(
        "*, students(first_name, last_name, student_number)"
    ).eq("scholarship_id", str(scholarship_id)).eq("status", "active").execute()

    scholarship["recipients"] = recipients.data or []

    # Get pending applications
    applications = supabase.table("scholarship_applications").select(
        "*, students(first_name, last_name, student_number)"
    ).eq("scholarship_id", str(scholarship_id)).eq("status", "pending").execute()

    scholarship["pending_applications"] = applications.data or []

    return scholarship


@router.post("")
async def create_scholarship(
    scholarship: ScholarshipCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a scholarship program"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    scholarship_data = {
        "school_id": school_id,
        "created_by": user_id,
        "name": scholarship.name,
        "description": scholarship.description,
        "scholarship_type": scholarship.scholarship_type,
        "amount": scholarship.amount,
        "percentage": scholarship.percentage,
        "academic_year_id": str(scholarship.academic_year_id) if scholarship.academic_year_id else None,
        "eligibility_criteria": scholarship.eligibility_criteria,
        "max_recipients": scholarship.max_recipients,
        "application_deadline": scholarship.application_deadline.isoformat() if scholarship.application_deadline else None,
        "is_renewable": scholarship.is_renewable,
        "renewal_criteria": scholarship.renewal_criteria,
        "is_active": True
    }

    result = supabase.table("scholarships").insert(scholarship_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create scholarship")

    return result.data[0]


@router.put("/{scholarship_id}")
async def update_scholarship(
    scholarship_id: UUID,
    update: ScholarshipUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update a scholarship program"""
    existing = supabase.table("scholarships").select("id").eq(
        "id", str(scholarship_id)
    ).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Scholarship not found")

    update_data = {}
    if update.name is not None:
        update_data["name"] = update.name
    if update.description is not None:
        update_data["description"] = update.description
    if update.amount is not None:
        update_data["amount"] = update.amount
    if update.percentage is not None:
        update_data["percentage"] = update.percentage
    if update.eligibility_criteria is not None:
        update_data["eligibility_criteria"] = update.eligibility_criteria
    if update.max_recipients is not None:
        update_data["max_recipients"] = update.max_recipients
    if update.application_deadline is not None:
        update_data["application_deadline"] = update.application_deadline.isoformat()
    if update.is_active is not None:
        update_data["is_active"] = update.is_active

    result = supabase.table("scholarships").update(update_data).eq(
        "id", str(scholarship_id)
    ).execute()

    return result.data[0] if result.data else None


@router.delete("/{scholarship_id}")
async def delete_scholarship(
    scholarship_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Deactivate a scholarship program"""
    supabase.table("scholarships").update({
        "is_active": False
    }).eq("id", str(scholarship_id)).execute()

    return {"success": True}


# ============================================================
# SCHOLARSHIP AWARD ENDPOINTS
# ============================================================

@router.post("/award")
async def award_scholarship(
    award: ScholarshipAward,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Award a scholarship to a student"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    # Check scholarship exists
    scholarship = supabase.table("scholarships").select(
        "amount, percentage, max_recipients"
    ).eq("id", str(award.scholarship_id)).single().execute()

    if not scholarship.data:
        raise HTTPException(status_code=404, detail="Scholarship not found")

    # Check recipient limit
    if scholarship.data.get("max_recipients"):
        current_count = supabase.table("student_scholarships").select(
            "id", count="exact"
        ).eq("scholarship_id", str(award.scholarship_id)).eq("status", "active").execute()

        if current_count.count >= scholarship.data["max_recipients"]:
            raise HTTPException(status_code=400, detail="Scholarship recipient limit reached")

    # Check if student already has this scholarship
    existing = supabase.table("student_scholarships").select("id").eq(
        "student_id", str(award.student_id)
    ).eq("scholarship_id", str(award.scholarship_id)).eq("status", "active").execute()

    if existing.data:
        raise HTTPException(status_code=400, detail="Student already has this scholarship")

    # Calculate award amount
    award_amount = award.award_amount or scholarship.data.get("amount")
    award_percentage = award.award_percentage or scholarship.data.get("percentage")

    award_data = {
        "school_id": school_id,
        "student_id": str(award.student_id),
        "scholarship_id": str(award.scholarship_id),
        "academic_year_id": str(award.academic_year_id),
        "award_amount": award_amount,
        "award_percentage": award_percentage,
        "start_date": award.start_date.isoformat(),
        "end_date": award.end_date.isoformat() if award.end_date else None,
        "notes": award.notes,
        "awarded_by": user_id,
        "awarded_at": datetime.utcnow().isoformat(),
        "status": "active"
    }

    result = supabase.table("student_scholarships").insert(award_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to award scholarship")

    return result.data[0]


@router.get("/awards")
async def list_awards(
    student_id: Optional[UUID] = None,
    scholarship_id: Optional[UUID] = None,
    academic_year_id: Optional[UUID] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List scholarship awards"""
    school_id = current_user.get("school_id")

    query = supabase.table("student_scholarships").select(
        "*, students(first_name, last_name, student_number), scholarships(name, scholarship_type)"
    ).eq("school_id", school_id)

    if student_id:
        query = query.eq("student_id", str(student_id))
    if scholarship_id:
        query = query.eq("scholarship_id", str(scholarship_id))
    if academic_year_id:
        query = query.eq("academic_year_id", str(academic_year_id))
    if status:
        query = query.eq("status", status)

    query = query.order("awarded_at", desc=True)

    result = query.execute()

    return {"awards": result.data or []}


@router.get("/student/{student_id}")
async def get_student_scholarships(
    student_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get all scholarships for a student"""
    result = supabase.table("student_scholarships").select(
        "*, scholarships(name, scholarship_type, description)"
    ).eq("student_id", str(student_id)).order("start_date", desc=True).execute()

    # Calculate total savings
    total_amount = sum(a.get("award_amount") or 0 for a in (result.data or []) if a.get("status") == "active")

    return {
        "student_id": str(student_id),
        "scholarships": result.data or [],
        "active_count": len([a for a in (result.data or []) if a.get("status") == "active"]),
        "total_award_amount": total_amount
    }


@router.post("/awards/{award_id}/revoke")
async def revoke_scholarship(
    award_id: UUID,
    reason: str,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Revoke a scholarship from a student"""
    user_id = current_user["id"]

    supabase.table("student_scholarships").update({
        "status": "revoked",
        "revoked_at": datetime.utcnow().isoformat(),
        "revoked_by": user_id,
        "revocation_reason": reason
    }).eq("id", str(award_id)).execute()

    return {"success": True}


@router.post("/awards/{award_id}/renew")
async def renew_scholarship(
    award_id: UUID,
    academic_year_id: UUID,
    new_amount: Optional[float] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Renew a scholarship for a new academic year"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    # Get current award
    current_award = supabase.table("student_scholarships").select("*").eq(
        "id", str(award_id)
    ).single().execute()

    if not current_award.data:
        raise HTTPException(status_code=404, detail="Award not found")

    # Create renewal
    renewal_data = {**current_award.data}
    del renewal_data["id"]
    del renewal_data["created_at"]
    del renewal_data["updated_at"]
    renewal_data["academic_year_id"] = str(academic_year_id)
    renewal_data["start_date"] = date.today().isoformat()
    renewal_data["awarded_at"] = datetime.utcnow().isoformat()
    renewal_data["awarded_by"] = user_id
    renewal_data["previous_award_id"] = str(award_id)
    renewal_data["status"] = "active"

    if new_amount:
        renewal_data["award_amount"] = new_amount

    result = supabase.table("student_scholarships").insert(renewal_data).execute()

    # Mark old award as renewed
    supabase.table("student_scholarships").update({
        "status": "renewed"
    }).eq("id", str(award_id)).execute()

    return result.data[0] if result.data else None


# ============================================================
# SCHOLARSHIP APPLICATIONS
# ============================================================

@router.post("/applications")
async def submit_application(
    application: ScholarshipApplication,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Submit a scholarship application"""
    school_id = current_user.get("school_id")

    # Check deadline
    scholarship = supabase.table("scholarships").select(
        "application_deadline, is_active"
    ).eq("id", str(application.scholarship_id)).single().execute()

    if not scholarship.data:
        raise HTTPException(status_code=404, detail="Scholarship not found")

    if not scholarship.data.get("is_active"):
        raise HTTPException(status_code=400, detail="Scholarship is not accepting applications")

    if scholarship.data.get("application_deadline"):
        deadline = date.fromisoformat(scholarship.data["application_deadline"])
        if date.today() > deadline:
            raise HTTPException(status_code=400, detail="Application deadline has passed")

    app_data = {
        "school_id": school_id,
        "student_id": str(application.student_id),
        "scholarship_id": str(application.scholarship_id),
        "essay": application.essay,
        "supporting_documents": application.supporting_documents,
        "recommendation_letters": application.recommendation_letters,
        "submitted_at": datetime.utcnow().isoformat(),
        "status": "pending"
    }

    result = supabase.table("scholarship_applications").insert(app_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to submit application")

    return result.data[0]


@router.post("/applications/{application_id}/review")
async def review_application(
    application_id: UUID,
    decision: str,  # approved, rejected
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Review a scholarship application"""
    user_id = current_user["id"]

    supabase.table("scholarship_applications").update({
        "status": decision,
        "reviewed_at": datetime.utcnow().isoformat(),
        "reviewed_by": user_id,
        "review_notes": notes
    }).eq("id", str(application_id)).execute()

    return {"success": True, "decision": decision}
