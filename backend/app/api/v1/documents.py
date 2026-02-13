from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import date
from pydantic import BaseModel
from app.core.auth import get_current_user, get_user_school_id
from app.db.supabase_client import get_supabase_admin

router = APIRouter()

class DocumentUpload(BaseModel):
    entity_type: str
    entity_id: str
    document_type: str
    file_url: str
    file_name: str
    file_size: int
    mime_type: str
    expiry_date: Optional[date] = None
    notes: Optional[str] = None

class DocumentVerify(BaseModel):
    verified: bool
    notes: Optional[str] = None

class DocumentRequirementCreate(BaseModel):
    entity_type: str
    document_type: str
    grade_id: Optional[str] = None
    required: bool = True

@router.get("/compliance-summary")
async def get_compliance_summary(
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    result = supabase.rpc("get_document_compliance_summary", {"p_school_id": school_id}).execute()
    return result.data[0] if result.data else {}

@router.get("/documents")
async def get_documents(
    entity_type: Optional[str] = None,
    status: Optional[str] = None,
    expired_only: bool = False,
    missing_only: bool = False,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    query = supabase.table("documents").select("*").eq("school_id", school_id)
    
    if entity_type:
        query = query.eq("entity_type", entity_type)
    if status:
        query = query.eq("status", status)
    if expired_only:
        query = query.eq("status", "expired")
    if missing_only:
        query = query.eq("status", "missing")
    
    result = query.order("uploaded_at", desc=True).execute()
    return result.data

@router.post("/documents")
async def upload_document(
    doc: DocumentUpload,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    data = {
        **doc.dict(),
        "school_id": school_id,
        "uploaded_by": user["id"],
        "status": "uploaded"
    }
    result = supabase.table("documents").insert(data).execute()
    return result.data[0]

@router.patch("/documents/{doc_id}/verify")
async def verify_document(
    doc_id: str,
    verify: DocumentVerify,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    data = {
        "verified": verify.verified,
        "verified_by": user["id"],
        "verified_at": "now()",
        "status": "verified" if verify.verified else "rejected",
        "notes": verify.notes
    }
    result = supabase.table("documents").update(data).eq("id", doc_id).execute()
    return result.data[0]

@router.get("/requirements")
async def get_requirements(
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    result = supabase.table("document_requirements").select("*").eq("school_id", school_id).eq("active", True).execute()
    return result.data

@router.post("/requirements")
async def create_requirement(
    req: DocumentRequirementCreate,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    data = {**req.dict(), "school_id": school_id}
    result = supabase.table("document_requirements").insert(data).execute()
    return result.data[0]
