"""
EduCore Backend - Admission Documents API
Document upload and verification for applications
"""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# MODELS
# ============================================================

class DocumentUpload(BaseModel):
    """Upload a document"""
    application_id: UUID
    document_type: str
    file_url: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None


class DocumentVerify(BaseModel):
    """Verify a document"""
    is_verified: bool
    verification_notes: Optional[str] = None


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/application/{application_id}")
async def get_application_documents(
    application_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get all documents for an application"""
    result = supabase.table("admission_documents").select("*").eq(
        "application_id", str(application_id)
    ).order("uploaded_at", desc=True).execute()

    # Get required documents from form
    application = supabase.table("admission_applications").select(
        "application_forms(required_documents)"
    ).eq("id", str(application_id)).single().execute()

    required_docs = []
    if application.data:
        required_docs = application.data.get("application_forms", {}).get("required_documents", [])

    documents = result.data or []
    uploaded_types = [d.get("document_type") for d in documents]

    return {
        "documents": documents,
        "required_documents": required_docs,
        "missing_documents": [d for d in required_docs if d not in uploaded_types],
        "is_complete": all(d in uploaded_types for d in required_docs)
    }


@router.get("/{document_id}")
async def get_document(
    document_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get a specific document"""
    result = supabase.table("admission_documents").select("*").eq(
        "id", str(document_id)
    ).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Document not found")

    return result.data


@router.post("")
async def upload_document(
    document: DocumentUpload,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Upload a document for an application"""
    user_id = current_user["id"]

    # Check application exists
    application = supabase.table("admission_applications").select("id").eq(
        "id", str(document.application_id)
    ).single().execute()

    if not application.data:
        raise HTTPException(status_code=404, detail="Application not found")

    # Check if document type already uploaded
    existing = supabase.table("admission_documents").select("id").eq(
        "application_id", str(document.application_id)
    ).eq("document_type", document.document_type).execute()

    if existing.data:
        # Update existing document
        result = supabase.table("admission_documents").update({
            "file_url": document.file_url,
            "file_name": document.file_name,
            "file_size": document.file_size,
            "uploaded_at": datetime.utcnow().isoformat(),
            "uploaded_by": user_id,
            "is_verified": False,
            "verification_notes": None
        }).eq("id", existing.data[0]["id"]).execute()
    else:
        # Insert new document
        doc_data = {
            "application_id": str(document.application_id),
            "document_type": document.document_type,
            "file_url": document.file_url,
            "file_name": document.file_name,
            "file_size": document.file_size,
            "uploaded_at": datetime.utcnow().isoformat(),
            "uploaded_by": user_id,
            "is_verified": False
        }
        result = supabase.table("admission_documents").insert(doc_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to upload document")

    return result.data[0]


@router.put("/{document_id}/verify")
async def verify_document(
    document_id: UUID,
    verification: DocumentVerify,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Verify or reject a document"""
    user_id = current_user["id"]

    existing = supabase.table("admission_documents").select("id").eq(
        "id", str(document_id)
    ).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Document not found")

    result = supabase.table("admission_documents").update({
        "is_verified": verification.is_verified,
        "verification_notes": verification.verification_notes,
        "verified_by": user_id,
        "verified_at": datetime.utcnow().isoformat()
    }).eq("id", str(document_id)).execute()

    return result.data[0] if result.data else None


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a document"""
    existing = supabase.table("admission_documents").select("id").eq(
        "id", str(document_id)
    ).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Document not found")

    supabase.table("admission_documents").delete().eq("id", str(document_id)).execute()

    return {"success": True}


@router.post("/bulk-verify")
async def bulk_verify_documents(
    application_id: UUID,
    document_ids: List[UUID],
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Verify multiple documents at once"""
    user_id = current_user["id"]

    verified_count = 0
    for doc_id in document_ids:
        result = supabase.table("admission_documents").update({
            "is_verified": True,
            "verified_by": user_id,
            "verified_at": datetime.utcnow().isoformat()
        }).eq("id", str(doc_id)).eq("application_id", str(application_id)).execute()

        if result.data:
            verified_count += 1

    return {"success": True, "verified_count": verified_count}


@router.get("/types")
async def get_document_types(
    current_user: dict = Depends(get_current_user)
):
    """Get list of standard document types"""
    return {
        "types": [
            {"id": "birth_certificate", "name": "Birth Certificate", "required": True},
            {"id": "passport_photo", "name": "Passport Photo", "required": True},
            {"id": "previous_report_card", "name": "Previous Report Card", "required": True},
            {"id": "transfer_certificate", "name": "Transfer Certificate", "required": False},
            {"id": "immunization_records", "name": "Immunization Records", "required": False},
            {"id": "proof_of_address", "name": "Proof of Address", "required": False},
            {"id": "parent_id", "name": "Parent/Guardian ID", "required": False},
            {"id": "medical_records", "name": "Medical Records", "required": False},
            {"id": "recommendation_letter", "name": "Recommendation Letter", "required": False},
            {"id": "other", "name": "Other", "required": False}
        ]
    }
