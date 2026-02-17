"""
EduCore Backend - Public Admissions API
Public endpoints for prospective students and parents
"""
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
import secrets

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# MODELS
# ============================================================

class SchoolInquiry(BaseModel):
    """Prospective parent inquiry"""
    school_id: UUID
    parent_name: str
    email: str
    phone: Optional[str] = None
    student_name: Optional[str] = None
    grade_interest: Optional[str] = None
    message: Optional[str] = None


class ApplicationSubmission(BaseModel):
    """Public application submission"""
    form_id: UUID
    form_data: Dict[str, Any]


# ============================================================
# ENDPOINTS (No authentication required)
# ============================================================

@router.get("/schools/{school_id}/info")
async def get_school_info(
    school_id: UUID,
    supabase = Depends(get_supabase)
):
    """Get public school information for admissions"""
    result = supabase.table("schools").select(
        "id, name, address, phone, email, website, logo_url, description"
    ).eq("id", str(school_id)).eq("is_active", True).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="School not found")

    school = result.data

    # Get admission settings
    settings = supabase.table("admission_settings").select(
        "admission_open, application_deadline, admission_message"
    ).eq("school_id", str(school_id)).single().execute()

    school["admission_settings"] = settings.data if settings.data else {
        "admission_open": True,
        "application_deadline": None,
        "admission_message": None
    }

    # Get available grades
    grades = supabase.table("grades").select(
        "id, name, level"
    ).eq("school_id", str(school_id)).order("level").execute()

    school["available_grades"] = grades.data or []

    return school


@router.get("/schools/{school_id}/forms")
async def get_public_forms(
    school_id: UUID,
    grade_level: Optional[str] = None,
    supabase = Depends(get_supabase)
):
    """Get available application forms for a school"""
    query = supabase.table("application_forms").select(
        "id, name, description, grade_levels, application_fee, instructions"
    ).eq("school_id", str(school_id)).eq("is_active", True)

    result = query.execute()

    forms = result.data or []

    # Filter by grade if specified
    if grade_level:
        forms = [
            f for f in forms
            if not f.get("grade_levels") or grade_level in f.get("grade_levels", [])
        ]

    return {"forms": forms}


@router.get("/forms/{form_id}")
async def get_public_form(
    form_id: UUID,
    supabase = Depends(get_supabase)
):
    """Get a specific application form (public view)"""
    result = supabase.table("application_forms").select(
        "id, name, description, sections, fields, required_documents, instructions, terms_and_conditions, application_fee, grade_levels"
    ).eq("id", str(form_id)).eq("is_active", True).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Form not found or inactive")

    form = result.data

    # Get school info
    school = supabase.table("application_forms").select(
        "schools(id, name, logo_url)"
    ).eq("id", str(form_id)).single().execute()

    if school.data:
        form["school"] = school.data.get("schools")

    # Get available grades for dropdown
    if form.get("school"):
        grades = supabase.table("grades").select(
            "id, name, level"
        ).eq("school_id", form["school"]["id"]).order("level").execute()

        # Update grade_applying field options
        for field in form.get("fields", []):
            if field.get("name") == "grade_applying":
                field["options"] = [
                    {"value": g["name"], "label": g["name"]}
                    for g in (grades.data or [])
                ]

    return form


@router.post("/apply")
async def submit_public_application(
    application: ApplicationSubmission,
    supabase = Depends(get_supabase)
):
    """Submit a public application"""
    # Get form details
    form = supabase.table("application_forms").select(
        "school_id, academic_year_id, fields, required_documents, application_fee"
    ).eq("id", str(application.form_id)).eq("is_active", True).single().execute()

    if not form.data:
        raise HTTPException(status_code=404, detail="Application form not found or inactive")

    # Validate required fields
    required_fields = [
        f["name"] for f in form.data.get("fields", [])
        if f.get("required")
    ]

    missing = []
    for field in required_fields:
        value = application.form_data.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(field)

    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required fields: {', '.join(missing)}"
        )

    # Generate tracking code
    tracking_code = f"APP-{secrets.token_hex(4).upper()}"

    # Create application
    app_data = {
        "school_id": form.data["school_id"],
        "form_id": str(application.form_id),
        "academic_year_id": form.data.get("academic_year_id"),
        "tracking_code": tracking_code,
        "form_data": application.form_data,
        "grade_applying": application.form_data.get("grade_applying"),
        "status": "submitted",
        "submitted_at": datetime.utcnow().isoformat(),
        "application_fee": form.data.get("application_fee", 0),
        "fee_paid": form.data.get("application_fee", 0) == 0
    }

    result = supabase.table("admission_applications").insert(app_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to submit application")

    applicant_name = f"{application.form_data.get('first_name', '')} {application.form_data.get('last_name', '')}"

    return {
        "success": True,
        "tracking_code": tracking_code,
        "application_id": result.data[0]["id"],
        "applicant_name": applicant_name.strip(),
        "message": "Your application has been submitted successfully. Please save your tracking code to check the status of your application."
    }


@router.get("/track/{tracking_code}")
async def track_application_status(
    tracking_code: str,
    supabase = Depends(get_supabase)
):
    """Track application status using tracking code"""
    result = supabase.table("admission_applications").select(
        "tracking_code, status, submitted_at, grade_applying, form_data, admission_interviews(interview_slots(date, start_time, location))"
    ).eq("tracking_code", tracking_code.upper()).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Application not found. Please check your tracking code.")

    app = result.data
    form_data = app.get("form_data", {})

    # Build status message
    status_messages = {
        "submitted": "Your application has been received and is pending review.",
        "under_review": "Your application is currently being reviewed by our admissions team.",
        "interview_scheduled": "An interview has been scheduled.",
        "accepted": "Congratulations! Your application has been accepted.",
        "rejected": "We regret to inform you that your application was not accepted.",
        "waitlisted": "Your application has been placed on the waiting list.",
        "enrolled": "You have been enrolled. Welcome to our school!"
    }

    response = {
        "tracking_code": app["tracking_code"],
        "applicant_name": f"{form_data.get('first_name', '')} {form_data.get('last_name', '')}".strip(),
        "grade_applying": app["grade_applying"],
        "status": app["status"],
        "status_message": status_messages.get(app["status"], "Status unknown"),
        "submitted_at": app["submitted_at"]
    }

    # Add interview details if scheduled
    interviews = app.get("admission_interviews") or []
    if interviews:
        interview = interviews[0]
        slot = interview.get("interview_slots", {})
        response["interview"] = {
            "date": slot.get("date"),
            "time": slot.get("start_time"),
            "location": slot.get("location")
        }

    return response


@router.post("/inquiry")
async def submit_inquiry(
    inquiry: SchoolInquiry,
    supabase = Depends(get_supabase)
):
    """Submit an inquiry about admissions"""
    # Check school exists
    school = supabase.table("schools").select("id, name").eq(
        "id", str(inquiry.school_id)
    ).single().execute()

    if not school.data:
        raise HTTPException(status_code=404, detail="School not found")

    inquiry_data = {
        "school_id": str(inquiry.school_id),
        "parent_name": inquiry.parent_name,
        "email": inquiry.email,
        "phone": inquiry.phone,
        "student_name": inquiry.student_name,
        "grade_interest": inquiry.grade_interest,
        "message": inquiry.message,
        "status": "new",
        "submitted_at": datetime.utcnow().isoformat()
    }

    result = supabase.table("admission_inquiries").insert(inquiry_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to submit inquiry")

    return {
        "success": True,
        "message": f"Thank you for your interest in {school.data['name']}. We will contact you soon."
    }


@router.get("/schools/{school_id}/faqs")
async def get_admission_faqs(
    school_id: UUID,
    supabase = Depends(get_supabase)
):
    """Get admission FAQs for a school"""
    result = supabase.table("admission_faqs").select(
        "question, answer, order_index"
    ).eq("school_id", str(school_id)).eq("is_active", True).order("order_index").execute()

    return {"faqs": result.data or []}


@router.get("/schools/{school_id}/important-dates")
async def get_important_dates(
    school_id: UUID,
    supabase = Depends(get_supabase)
):
    """Get important admission dates"""
    # Get from admission settings
    settings = supabase.table("admission_settings").select(
        "application_deadline, notification_date, enrollment_deadline, orientation_date"
    ).eq("school_id", str(school_id)).single().execute()

    dates = []

    if settings.data:
        if settings.data.get("application_deadline"):
            dates.append({
                "name": "Application Deadline",
                "date": settings.data["application_deadline"]
            })
        if settings.data.get("notification_date"):
            dates.append({
                "name": "Decision Notification",
                "date": settings.data["notification_date"]
            })
        if settings.data.get("enrollment_deadline"):
            dates.append({
                "name": "Enrollment Deadline",
                "date": settings.data["enrollment_deadline"]
            })
        if settings.data.get("orientation_date"):
            dates.append({
                "name": "New Student Orientation",
                "date": settings.data["orientation_date"]
            })

    return {"important_dates": dates}


@router.post("/documents/upload-url")
async def get_document_upload_url(
    application_id: Optional[UUID] = None,
    document_type: str = "other",
    file_name: str = "document",
    supabase = Depends(get_supabase)
):
    """Get a signed URL for document upload"""
    # This would integrate with Supabase Storage
    # For now, return a placeholder

    # Generate a unique file path
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    file_path = f"admissions/{application_id or 'temp'}/{document_type}_{timestamp}_{file_name}"

    # In production, this would create a signed upload URL
    return {
        "upload_url": f"/api/v1/uploads/signed?path={file_path}",
        "file_path": file_path,
        "expires_in": 3600
    }
