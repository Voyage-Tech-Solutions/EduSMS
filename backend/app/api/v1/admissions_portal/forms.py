"""
EduCore Backend - Application Forms API
Customizable admission application forms
"""
import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# MODELS
# ============================================================

class FormField(BaseModel):
    """A single field in an application form"""
    id: str
    name: str
    label: str
    type: str  # text, textarea, number, email, phone, date, select, radio, checkbox, file
    section: str = "general"
    required: bool = True
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    options: Optional[List[dict]] = None  # For select, radio, checkbox
    validation: Optional[dict] = None  # min, max, pattern, etc.
    order_index: int = 0
    conditional: Optional[dict] = None  # Show if another field has specific value


class FormSection(BaseModel):
    """A section in an application form"""
    id: str
    name: str
    title: str
    description: Optional[str] = None
    order_index: int = 0


class FormCreate(BaseModel):
    """Create an application form"""
    name: str
    description: Optional[str] = None
    grade_levels: List[str] = []  # Which grades this form is for
    academic_year_id: Optional[UUID] = None
    sections: List[FormSection] = []
    fields: List[FormField] = []
    required_documents: List[str] = []
    instructions: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    application_fee: float = 0
    is_active: bool = True


class FormUpdate(BaseModel):
    """Update an application form"""
    name: Optional[str] = None
    description: Optional[str] = None
    grade_levels: Optional[List[str]] = None
    sections: Optional[List[FormSection]] = None
    fields: Optional[List[FormField]] = None
    required_documents: Optional[List[str]] = None
    instructions: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    application_fee: Optional[float] = None
    is_active: Optional[bool] = None


# ============================================================
# DEFAULT FORM TEMPLATE
# ============================================================

DEFAULT_SECTIONS = [
    {"id": "student", "name": "student_info", "title": "Student Information", "order_index": 0},
    {"id": "parent", "name": "parent_info", "title": "Parent/Guardian Information", "order_index": 1},
    {"id": "academic", "name": "academic_history", "title": "Academic History", "order_index": 2},
    {"id": "additional", "name": "additional_info", "title": "Additional Information", "order_index": 3}
]

DEFAULT_FIELDS = [
    # Student Information
    {"id": "first_name", "name": "first_name", "label": "First Name", "type": "text", "section": "student", "required": True, "order_index": 0},
    {"id": "middle_name", "name": "middle_name", "label": "Middle Name", "type": "text", "section": "student", "required": False, "order_index": 1},
    {"id": "last_name", "name": "last_name", "label": "Last Name", "type": "text", "section": "student", "required": True, "order_index": 2},
    {"id": "date_of_birth", "name": "date_of_birth", "label": "Date of Birth", "type": "date", "section": "student", "required": True, "order_index": 3},
    {"id": "gender", "name": "gender", "label": "Gender", "type": "select", "section": "student", "required": True, "order_index": 4, "options": [{"value": "male", "label": "Male"}, {"value": "female", "label": "Female"}, {"value": "other", "label": "Other"}]},
    {"id": "grade_applying", "name": "grade_applying", "label": "Grade Applying For", "type": "select", "section": "student", "required": True, "order_index": 5},
    {"id": "student_photo", "name": "student_photo", "label": "Student Photo", "type": "file", "section": "student", "required": False, "order_index": 6},

    # Parent Information
    {"id": "parent1_name", "name": "parent1_name", "label": "Parent/Guardian 1 Full Name", "type": "text", "section": "parent", "required": True, "order_index": 0},
    {"id": "parent1_relationship", "name": "parent1_relationship", "label": "Relationship to Student", "type": "select", "section": "parent", "required": True, "order_index": 1, "options": [{"value": "father", "label": "Father"}, {"value": "mother", "label": "Mother"}, {"value": "guardian", "label": "Guardian"}, {"value": "other", "label": "Other"}]},
    {"id": "parent1_email", "name": "parent1_email", "label": "Email Address", "type": "email", "section": "parent", "required": True, "order_index": 2},
    {"id": "parent1_phone", "name": "parent1_phone", "label": "Phone Number", "type": "phone", "section": "parent", "required": True, "order_index": 3},
    {"id": "parent1_occupation", "name": "parent1_occupation", "label": "Occupation", "type": "text", "section": "parent", "required": False, "order_index": 4},
    {"id": "address", "name": "address", "label": "Home Address", "type": "textarea", "section": "parent", "required": True, "order_index": 5},

    # Academic History
    {"id": "previous_school", "name": "previous_school", "label": "Previous School Name", "type": "text", "section": "academic", "required": False, "order_index": 0},
    {"id": "previous_grade", "name": "previous_grade", "label": "Last Grade Completed", "type": "text", "section": "academic", "required": False, "order_index": 1},
    {"id": "reason_for_transfer", "name": "reason_for_transfer", "label": "Reason for Transfer (if applicable)", "type": "textarea", "section": "academic", "required": False, "order_index": 2},

    # Additional Information
    {"id": "medical_conditions", "name": "medical_conditions", "label": "Medical Conditions/Allergies", "type": "textarea", "section": "additional", "required": False, "order_index": 0, "help_text": "Please list any medical conditions or allergies we should be aware of"},
    {"id": "special_needs", "name": "special_needs", "label": "Special Educational Needs", "type": "textarea", "section": "additional", "required": False, "order_index": 1},
    {"id": "how_did_you_hear", "name": "how_did_you_hear", "label": "How did you hear about us?", "type": "select", "section": "additional", "required": False, "order_index": 2, "options": [{"value": "website", "label": "Website"}, {"value": "social_media", "label": "Social Media"}, {"value": "referral", "label": "Friend/Family Referral"}, {"value": "advertisement", "label": "Advertisement"}, {"value": "other", "label": "Other"}]}
]


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("")
async def list_forms(
    academic_year_id: Optional[UUID] = None,
    is_active: Optional[bool] = True,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List application forms"""
    school_id = current_user.get("school_id")

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    query = supabase.table("application_forms").select("*").eq("school_id", school_id)

    if academic_year_id:
        query = query.eq("academic_year_id", str(academic_year_id))
    if is_active is not None:
        query = query.eq("is_active", is_active)

    query = query.order("created_at", desc=True)

    result = query.execute()

    return {"forms": result.data or []}


@router.get("/{form_id}")
async def get_form(
    form_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get a specific application form"""
    result = supabase.table("application_forms").select("*").eq(
        "id", str(form_id)
    ).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Form not found")

    return result.data


@router.post("")
async def create_form(
    form: FormCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a new application form"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    form_data = {
        "school_id": school_id,
        "created_by": user_id,
        "name": form.name,
        "description": form.description,
        "grade_levels": form.grade_levels,
        "academic_year_id": str(form.academic_year_id) if form.academic_year_id else None,
        "sections": [s.dict() for s in form.sections] if form.sections else DEFAULT_SECTIONS,
        "fields": [f.dict() for f in form.fields] if form.fields else DEFAULT_FIELDS,
        "required_documents": form.required_documents,
        "instructions": form.instructions,
        "terms_and_conditions": form.terms_and_conditions,
        "application_fee": form.application_fee,
        "is_active": form.is_active
    }

    result = supabase.table("application_forms").insert(form_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create form")

    return result.data[0]


@router.post("/from-default")
async def create_from_default(
    name: str,
    grade_levels: List[str] = [],
    academic_year_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a form from the default template"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    form_data = {
        "school_id": school_id,
        "created_by": user_id,
        "name": name,
        "grade_levels": grade_levels,
        "academic_year_id": str(academic_year_id) if academic_year_id else None,
        "sections": DEFAULT_SECTIONS,
        "fields": DEFAULT_FIELDS,
        "required_documents": ["birth_certificate", "previous_report_card", "passport_photo"],
        "is_active": True
    }

    result = supabase.table("application_forms").insert(form_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create form")

    return result.data[0]


@router.put("/{form_id}")
async def update_form(
    form_id: UUID,
    update: FormUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update an application form"""
    existing = supabase.table("application_forms").select("id").eq(
        "id", str(form_id)
    ).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Form not found")

    update_data = {}
    if update.name is not None:
        update_data["name"] = update.name
    if update.description is not None:
        update_data["description"] = update.description
    if update.grade_levels is not None:
        update_data["grade_levels"] = update.grade_levels
    if update.sections is not None:
        update_data["sections"] = [s.dict() for s in update.sections]
    if update.fields is not None:
        update_data["fields"] = [f.dict() for f in update.fields]
    if update.required_documents is not None:
        update_data["required_documents"] = update.required_documents
    if update.instructions is not None:
        update_data["instructions"] = update.instructions
    if update.terms_and_conditions is not None:
        update_data["terms_and_conditions"] = update.terms_and_conditions
    if update.application_fee is not None:
        update_data["application_fee"] = update.application_fee
    if update.is_active is not None:
        update_data["is_active"] = update.is_active

    result = supabase.table("application_forms").update(update_data).eq(
        "id", str(form_id)
    ).execute()

    return result.data[0] if result.data else None


@router.delete("/{form_id}")
async def delete_form(
    form_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete an application form (soft delete)"""
    # Check if form has applications
    applications = supabase.table("admission_applications").select(
        "id", count="exact"
    ).eq("form_id", str(form_id)).execute()

    if applications.count and applications.count > 0:
        # Soft delete
        supabase.table("application_forms").update({
            "is_active": False
        }).eq("id", str(form_id)).execute()
    else:
        # Hard delete
        supabase.table("application_forms").delete().eq("id", str(form_id)).execute()

    return {"success": True}


@router.post("/{form_id}/duplicate")
async def duplicate_form(
    form_id: UUID,
    new_name: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a copy of an application form"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    original = supabase.table("application_forms").select("*").eq(
        "id", str(form_id)
    ).single().execute()

    if not original.data:
        raise HTTPException(status_code=404, detail="Form not found")

    new_form = {**original.data}
    del new_form["id"]
    del new_form["created_at"]
    del new_form["updated_at"]
    new_form["created_by"] = user_id
    new_form["school_id"] = school_id
    new_form["name"] = new_name or f"(Copy) {new_form['name']}"

    result = supabase.table("application_forms").insert(new_form).execute()

    return result.data[0] if result.data else None
