"""
EduCore Backend - Parent Document Management API
Upload and manage documents like absence notes, medical forms, etc.
"""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime

from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# MODELS
# ============================================================

class DocumentUploadRequest(BaseModel):
    """Request to upload a document"""
    student_id: UUID
    document_type: str  # absence_note, medical_form, permission_slip, other
    title: str
    description: Optional[str] = None
    related_date: Optional[date] = None  # e.g., absence date
    file_url: str  # Pre-uploaded file URL


class DocumentUpdate(BaseModel):
    """Update document metadata"""
    title: Optional[str] = None
    description: Optional[str] = None


# ============================================================
# DOCUMENT TYPES
# ============================================================

DOCUMENT_TYPES = [
    {"id": "absence_note", "name": "Absence Note", "description": "Explanation for student absence", "requires_date": True},
    {"id": "medical_form", "name": "Medical Form", "description": "Medical documentation or health forms", "requires_date": False},
    {"id": "permission_slip", "name": "Permission Slip", "description": "Signed permission for activities/trips", "requires_date": True},
    {"id": "immunization_record", "name": "Immunization Record", "description": "Vaccination records", "requires_date": False},
    {"id": "birth_certificate", "name": "Birth Certificate", "description": "Official birth certificate", "requires_date": False},
    {"id": "guardianship_document", "name": "Guardianship Document", "description": "Legal guardianship papers", "requires_date": False},
    {"id": "iep_document", "name": "IEP Document", "description": "Individualized Education Program", "requires_date": False},
    {"id": "other", "name": "Other", "description": "Other documents", "requires_date": False}
]


@router.get("/types")
async def get_document_types(
    current_user: dict = Depends(get_current_user)
):
    """Get available document types"""
    return {"document_types": DOCUMENT_TYPES}


# ============================================================
# DOCUMENT CRUD
# ============================================================

@router.get("")
async def list_documents(
    student_id: Optional[UUID] = None,
    document_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List documents uploaded by parent"""
    parent_id = current_user.get("id")

    # Get parent's children
    relations = supabase.table("parent_student_relations").select(
        "student_id"
    ).eq("parent_id", parent_id).execute()

    student_ids = [r["student_id"] for r in (relations.data or [])]

    if not student_ids:
        return {"documents": [], "total": 0}

    if student_id:
        if str(student_id) not in student_ids:
            raise HTTPException(status_code=403, detail="Access denied")
        student_ids = [str(student_id)]

    query = supabase.table("parent_documents").select(
        "*, student:student_id(first_name, last_name)"
    ).in_("student_id", student_ids).eq("uploaded_by", parent_id)

    if document_type:
        query = query.eq("document_type", document_type)
    if status:
        query = query.eq("status", status)

    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

    result = query.execute()

    return {
        "documents": result.data or [],
        "total": len(result.data) if result.data else 0,
        "limit": limit,
        "offset": offset
    }


@router.get("/{document_id}")
async def get_document(
    document_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get document details"""
    parent_id = current_user.get("id")

    result = supabase.table("parent_documents").select(
        "*, student:student_id(first_name, last_name), reviewer:reviewed_by(first_name, last_name)"
    ).eq("id", str(document_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Document not found")

    if result.data.get("uploaded_by") != parent_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return result.data


@router.post("")
async def upload_document(
    doc: DocumentUploadRequest,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Upload a new document"""
    parent_id = current_user.get("id")
    school_id = current_user.get("school_id")

    # Verify parent owns student
    relation = supabase.table("parent_student_relations").select("id").eq(
        "parent_id", parent_id
    ).eq("student_id", str(doc.student_id)).execute()

    if not relation.data:
        raise HTTPException(status_code=403, detail="You can only upload documents for your own children")

    doc_data = {
        "school_id": school_id,
        "student_id": str(doc.student_id),
        "uploaded_by": parent_id,
        "document_type": doc.document_type,
        "title": doc.title,
        "description": doc.description,
        "related_date": doc.related_date.isoformat() if doc.related_date else None,
        "file_url": doc.file_url,
        "status": "pending"  # pending, approved, rejected
    }

    result = supabase.table("parent_documents").insert(doc_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to upload document")

    return result.data[0]


@router.put("/{document_id}")
async def update_document(
    document_id: UUID,
    update: DocumentUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update document metadata"""
    parent_id = current_user.get("id")

    existing = supabase.table("parent_documents").select("uploaded_by, status").eq(
        "id", str(document_id)
    ).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Document not found")

    if existing.data["uploaded_by"] != parent_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Can only update pending documents
    if existing.data["status"] != "pending":
        raise HTTPException(status_code=400, detail="Can only update pending documents")

    update_data = {}
    if update.title is not None:
        update_data["title"] = update.title
    if update.description is not None:
        update_data["description"] = update.description

    result = supabase.table("parent_documents").update(update_data).eq(
        "id", str(document_id)
    ).execute()

    return result.data[0] if result.data else None


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a document"""
    parent_id = current_user.get("id")

    existing = supabase.table("parent_documents").select("uploaded_by, status").eq(
        "id", str(document_id)
    ).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Document not found")

    if existing.data["uploaded_by"] != parent_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Can only delete pending documents
    if existing.data["status"] != "pending":
        raise HTTPException(status_code=400, detail="Can only delete pending documents")

    supabase.table("parent_documents").delete().eq("id", str(document_id)).execute()

    return {"success": True}


# ============================================================
# ABSENCE NOTES (SPECIAL HANDLING)
# ============================================================

@router.post("/absence-note")
async def submit_absence_note(
    student_id: UUID,
    absence_date: date,
    reason: str,
    details: Optional[str] = None,
    file_url: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Submit an absence note for a specific date"""
    parent_id = current_user.get("id")
    school_id = current_user.get("school_id")

    # Verify parent owns student
    relation = supabase.table("parent_student_relations").select("id").eq(
        "parent_id", parent_id
    ).eq("student_id", str(student_id)).execute()

    if not relation.data:
        raise HTTPException(status_code=403, detail="Access denied")

    # Check if absence exists for this date
    attendance = supabase.table("attendance").select("id, status").eq(
        "student_id", str(student_id)
    ).eq("date", absence_date.isoformat()).single().execute()

    # Create absence note document
    doc_data = {
        "school_id": school_id,
        "student_id": str(student_id),
        "uploaded_by": parent_id,
        "document_type": "absence_note",
        "title": f"Absence Note - {absence_date.isoformat()}",
        "description": f"Reason: {reason}\n{details or ''}",
        "related_date": absence_date.isoformat(),
        "file_url": file_url,
        "status": "pending",
        "metadata": {
            "reason": reason,
            "details": details,
            "attendance_id": attendance.data["id"] if attendance.data else None
        }
    }

    result = supabase.table("parent_documents").insert(doc_data).execute()

    # If attendance record exists, add note reference
    if attendance.data:
        supabase.table("attendance").update({
            "excuse_note_id": result.data[0]["id"] if result.data else None
        }).eq("id", attendance.data["id"]).execute()

    return {
        "document": result.data[0] if result.data else None,
        "attendance_record": attendance.data
    }


@router.get("/absence-notes")
async def get_absence_notes(
    student_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get absence notes"""
    parent_id = current_user.get("id")

    # Get parent's children
    relations = supabase.table("parent_student_relations").select(
        "student_id"
    ).eq("parent_id", parent_id).execute()

    student_ids = [r["student_id"] for r in (relations.data or [])]

    if student_id:
        if str(student_id) not in student_ids:
            raise HTTPException(status_code=403, detail="Access denied")
        student_ids = [str(student_id)]

    query = supabase.table("parent_documents").select(
        "*, student:student_id(first_name, last_name)"
    ).in_("student_id", student_ids).eq("document_type", "absence_note")

    if start_date:
        query = query.gte("related_date", start_date.isoformat())
    if end_date:
        query = query.lte("related_date", end_date.isoformat())

    result = query.order("related_date", desc=True).execute()

    return {"absence_notes": result.data or []}


# ============================================================
# REQUIRED DOCUMENTS
# ============================================================

@router.get("/required")
async def get_required_documents(
    student_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get list of required documents and their status"""
    parent_id = current_user.get("id")
    school_id = current_user.get("school_id")

    # Verify parent owns student
    relation = supabase.table("parent_student_relations").select("id").eq(
        "parent_id", parent_id
    ).eq("student_id", str(student_id)).execute()

    if not relation.data:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get school's required documents
    requirements = supabase.table("required_documents").select("*").eq(
        "school_id", school_id
    ).eq("is_active", True).execute()

    # Get submitted documents
    submitted = supabase.table("parent_documents").select(
        "document_type, status"
    ).eq("student_id", str(student_id)).execute()

    submitted_map = {}
    for doc in (submitted.data or []):
        dtype = doc["document_type"]
        if dtype not in submitted_map or doc["status"] == "approved":
            submitted_map[dtype] = doc["status"]

    # Build checklist
    checklist = []
    for req in (requirements.data or []):
        dtype = req["document_type"]
        checklist.append({
            "document_type": dtype,
            "name": req["name"],
            "description": req.get("description"),
            "is_required": req.get("is_required", True),
            "submitted": dtype in submitted_map,
            "status": submitted_map.get(dtype)
        })

    # Add any standard required docs not in school config
    standard_required = ["birth_certificate", "immunization_record"]
    for dtype in standard_required:
        if not any(c["document_type"] == dtype for c in checklist):
            checklist.append({
                "document_type": dtype,
                "name": next((t["name"] for t in DOCUMENT_TYPES if t["id"] == dtype), dtype),
                "description": None,
                "is_required": True,
                "submitted": dtype in submitted_map,
                "status": submitted_map.get(dtype)
            })

    return {
        "required_documents": checklist,
        "complete_count": sum(1 for c in checklist if c["status"] == "approved"),
        "pending_count": sum(1 for c in checklist if c["status"] == "pending"),
        "missing_count": sum(1 for c in checklist if c["is_required"] and not c["submitted"])
    }


# ============================================================
# UPLOAD PRESIGNED URL
# ============================================================

@router.post("/upload-url")
async def get_upload_url(
    filename: str,
    content_type: str,
    student_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get a presigned URL for uploading a document"""
    parent_id = current_user.get("id")
    school_id = current_user.get("school_id")

    # Verify parent owns student
    relation = supabase.table("parent_student_relations").select("id").eq(
        "parent_id", parent_id
    ).eq("student_id", str(student_id)).execute()

    if not relation.data:
        raise HTTPException(status_code=403, detail="Access denied")

    # Generate a unique path
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    file_path = f"parent-documents/{school_id}/{student_id}/{timestamp}_{filename}"

    # In production, this would generate a presigned URL from Supabase Storage
    # For now, return the expected path
    return {
        "upload_url": f"/api/v1/uploads/parent-documents",
        "file_path": file_path,
        "expires_in": 3600
    }
