"""
EduCore Backend - Admission Applications API
Application submission and management
"""
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import date, datetime
import secrets

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# MODELS
# ============================================================

class ApplicationSubmit(BaseModel):
    """Submit an application"""
    form_id: UUID
    form_data: Dict[str, Any]
    documents: Optional[Dict[str, str]] = None  # field_name -> file_url


class ApplicationUpdate(BaseModel):
    """Update application status"""
    status: Optional[str] = None  # submitted, under_review, interview_scheduled, accepted, rejected, waitlisted, enrolled
    notes: Optional[str] = None
    reviewer_id: Optional[UUID] = None
    interview_date: Optional[datetime] = None
    decision_reason: Optional[str] = None


class ApplicationReview(BaseModel):
    """Application review/scoring"""
    category: str  # academic, behavior, interview, documents
    score: int  # 1-5
    comments: Optional[str] = None


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("")
async def list_applications(
    form_id: Optional[UUID] = None,
    status: Optional[str] = None,
    grade_applying: Optional[str] = None,
    academic_year_id: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List admission applications with filters"""
    school_id = current_user.get("school_id")

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    query = supabase.table("admission_applications").select(
        "*, application_forms(name)"
    ).eq("school_id", school_id)

    if form_id:
        query = query.eq("form_id", str(form_id))
    if status:
        query = query.eq("status", status)
    if grade_applying:
        query = query.eq("grade_applying", grade_applying)
    if academic_year_id:
        query = query.eq("academic_year_id", str(academic_year_id))
    if date_from:
        query = query.gte("submitted_at", date_from.isoformat())
    if date_to:
        query = query.lte("submitted_at", date_to.isoformat())

    query = query.order("submitted_at", desc=True).range(offset, offset + limit - 1)

    result = query.execute()

    applications = result.data or []

    # Filter by search (applicant name)
    if search:
        search_lower = search.lower()
        applications = [
            a for a in applications
            if search_lower in (a.get("form_data", {}).get("first_name", "") + " " +
                               a.get("form_data", {}).get("last_name", "")).lower()
        ]

    return {
        "applications": applications,
        "total": len(applications),
        "limit": limit,
        "offset": offset
    }


@router.get("/stats")
async def get_application_stats(
    academic_year_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get application statistics"""
    school_id = current_user.get("school_id")

    query = supabase.table("admission_applications").select(
        "status, grade_applying, submitted_at"
    ).eq("school_id", school_id)

    if academic_year_id:
        query = query.eq("academic_year_id", str(academic_year_id))

    result = query.execute()

    applications = result.data or []

    stats = {
        "total": len(applications),
        "by_status": {},
        "by_grade": {},
        "this_week": 0,
        "this_month": 0
    }

    from datetime import timedelta
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    for app in applications:
        # By status
        status = app.get("status", "submitted")
        stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

        # By grade
        grade = app.get("grade_applying", "unknown")
        stats["by_grade"][grade] = stats["by_grade"].get(grade, 0) + 1

        # Time-based
        submitted = app.get("submitted_at")
        if submitted:
            submitted_dt = datetime.fromisoformat(submitted.replace("Z", ""))
            if submitted_dt >= week_ago:
                stats["this_week"] += 1
            if submitted_dt >= month_ago:
                stats["this_month"] += 1

    # Calculate rates
    total = stats["total"]
    if total > 0:
        accepted = stats["by_status"].get("accepted", 0)
        enrolled = stats["by_status"].get("enrolled", 0)
        rejected = stats["by_status"].get("rejected", 0)

        stats["acceptance_rate"] = round((accepted + enrolled) / total * 100, 1)
        stats["rejection_rate"] = round(rejected / total * 100, 1)
        stats["conversion_rate"] = round(enrolled / (accepted + enrolled) * 100, 1) if (accepted + enrolled) > 0 else 0

    return stats


@router.get("/{application_id}")
async def get_application(
    application_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get a specific application with full details"""
    result = supabase.table("admission_applications").select(
        "*, application_forms(name, sections, fields, required_documents)"
    ).eq("id", str(application_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Application not found")

    application = result.data

    # Get documents
    documents = supabase.table("admission_documents").select("*").eq(
        "application_id", str(application_id)
    ).execute()
    application["documents"] = documents.data or []

    # Get reviews
    reviews = supabase.table("admission_reviews").select(
        "*, user_profiles(first_name, last_name)"
    ).eq("application_id", str(application_id)).execute()
    application["reviews"] = reviews.data or []

    # Get interview if scheduled
    interview = supabase.table("admission_interviews").select("*").eq(
        "application_id", str(application_id)
    ).single().execute()
    application["interview"] = interview.data

    return application


@router.get("/track/{tracking_code}")
async def track_application(
    tracking_code: str,
    supabase = Depends(get_supabase)
):
    """Track application status by tracking code (public endpoint)"""
    result = supabase.table("admission_applications").select(
        "id, tracking_code, status, submitted_at, grade_applying, form_data"
    ).eq("tracking_code", tracking_code).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Application not found")

    app = result.data

    # Only return limited info
    return {
        "tracking_code": app["tracking_code"],
        "status": app["status"],
        "submitted_at": app["submitted_at"],
        "grade_applying": app["grade_applying"],
        "applicant_name": f"{app['form_data'].get('first_name', '')} {app['form_data'].get('last_name', '')}"
    }


@router.post("")
async def submit_application(
    application: ApplicationSubmit,
    supabase = Depends(get_supabase)
):
    """Submit a new application (public endpoint)"""
    # Get form
    form = supabase.table("application_forms").select(
        "school_id, academic_year_id, fields, required_documents, application_fee"
    ).eq("id", str(application.form_id)).eq("is_active", True).single().execute()

    if not form.data:
        raise HTTPException(status_code=404, detail="Application form not found or inactive")

    # Validate required fields
    required_fields = [f["name"] for f in form.data.get("fields", []) if f.get("required")]
    missing_fields = [f for f in required_fields if f not in application.form_data or not application.form_data[f]]

    if missing_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required fields: {', '.join(missing_fields)}"
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

    application_record = result.data[0]

    # Save documents
    if application.documents:
        for field_name, file_url in application.documents.items():
            doc_data = {
                "application_id": application_record["id"],
                "document_type": field_name,
                "file_url": file_url,
                "uploaded_at": datetime.utcnow().isoformat()
            }
            supabase.table("admission_documents").insert(doc_data).execute()

    return {
        "success": True,
        "application_id": application_record["id"],
        "tracking_code": tracking_code,
        "message": "Application submitted successfully"
    }


@router.put("/{application_id}")
async def update_application(
    application_id: UUID,
    update: ApplicationUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update application status"""
    user_id = current_user["id"]

    existing = supabase.table("admission_applications").select("id, status").eq(
        "id", str(application_id)
    ).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Application not found")

    update_data = {"updated_by": user_id}

    if update.status is not None:
        update_data["status"] = update.status
        update_data["status_updated_at"] = datetime.utcnow().isoformat()
    if update.notes is not None:
        update_data["notes"] = update.notes
    if update.reviewer_id is not None:
        update_data["reviewer_id"] = str(update.reviewer_id)
    if update.decision_reason is not None:
        update_data["decision_reason"] = update.decision_reason

    result = supabase.table("admission_applications").update(update_data).eq(
        "id", str(application_id)
    ).execute()

    return result.data[0] if result.data else None


@router.post("/{application_id}/review")
async def add_review(
    application_id: UUID,
    review: ApplicationReview,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Add a review to an application"""
    user_id = current_user["id"]

    existing = supabase.table("admission_applications").select("id").eq(
        "id", str(application_id)
    ).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Application not found")

    review_data = {
        "application_id": str(application_id),
        "reviewer_id": user_id,
        "category": review.category,
        "score": review.score,
        "comments": review.comments,
        "reviewed_at": datetime.utcnow().isoformat()
    }

    result = supabase.table("admission_reviews").insert(review_data).execute()

    # Update application status
    supabase.table("admission_applications").update({
        "status": "under_review"
    }).eq("id", str(application_id)).eq("status", "submitted").execute()

    return result.data[0] if result.data else None


@router.post("/{application_id}/accept")
async def accept_application(
    application_id: UUID,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Accept an application"""
    user_id = current_user["id"]

    supabase.table("admission_applications").update({
        "status": "accepted",
        "decision_by": user_id,
        "decision_at": datetime.utcnow().isoformat(),
        "decision_reason": notes
    }).eq("id", str(application_id)).execute()

    return {"success": True, "status": "accepted"}


@router.post("/{application_id}/reject")
async def reject_application(
    application_id: UUID,
    reason: str,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Reject an application"""
    user_id = current_user["id"]

    supabase.table("admission_applications").update({
        "status": "rejected",
        "decision_by": user_id,
        "decision_at": datetime.utcnow().isoformat(),
        "decision_reason": reason
    }).eq("id", str(application_id)).execute()

    return {"success": True, "status": "rejected"}


@router.post("/{application_id}/waitlist")
async def waitlist_application(
    application_id: UUID,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Put an application on waitlist"""
    user_id = current_user["id"]

    supabase.table("admission_applications").update({
        "status": "waitlisted",
        "decision_by": user_id,
        "decision_at": datetime.utcnow().isoformat(),
        "decision_reason": notes
    }).eq("id", str(application_id)).execute()

    return {"success": True, "status": "waitlisted"}


@router.post("/{application_id}/enroll")
async def enroll_applicant(
    application_id: UUID,
    class_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Convert accepted application to enrolled student"""
    user_id = current_user["id"]
    school_id = current_user.get("school_id")

    # Get application
    application = supabase.table("admission_applications").select(
        "form_data, status, grade_applying"
    ).eq("id", str(application_id)).single().execute()

    if not application.data:
        raise HTTPException(status_code=404, detail="Application not found")

    if application.data["status"] != "accepted":
        raise HTTPException(status_code=400, detail="Only accepted applications can be enrolled")

    form_data = application.data["form_data"]

    # Create student record
    student_data = {
        "school_id": school_id,
        "class_id": str(class_id),
        "first_name": form_data.get("first_name"),
        "middle_name": form_data.get("middle_name"),
        "last_name": form_data.get("last_name"),
        "date_of_birth": form_data.get("date_of_birth"),
        "gender": form_data.get("gender"),
        "address": form_data.get("address"),
        "admission_date": date.today().isoformat(),
        "status": "active"
    }

    student_result = supabase.table("students").insert(student_data).execute()

    if not student_result.data:
        raise HTTPException(status_code=500, detail="Failed to create student record")

    student_id = student_result.data[0]["id"]

    # Update application status
    supabase.table("admission_applications").update({
        "status": "enrolled",
        "enrolled_student_id": student_id,
        "enrolled_at": datetime.utcnow().isoformat()
    }).eq("id", str(application_id)).execute()

    return {
        "success": True,
        "student_id": student_id,
        "message": "Student enrolled successfully"
    }
