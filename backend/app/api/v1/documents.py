"""
EduCore Backend - Documents & Compliance API
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from app.core.security import require_office_admin, require_teacher
from app.db.supabase import supabase_admin

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/compliance/summary")
async def get_compliance_summary(current_user: dict = Depends(require_office_admin)):
    """Get compliance summary statistics"""
    school_id = current_user.get("school_id")
    if not supabase_admin:
        return {"total_students": 0, "fully_compliant": 0, "missing_docs": 0, "expired_docs": 0, "pending_verification": 0}
    
    students = supabase_admin.table("students").select("id", count="exact").eq("school_id", school_id).eq("status", "active").execute()
    total = students.count or 0
    
    docs = supabase_admin.table("student_documents").select("status", count="exact").execute()
    missing = sum(1 for d in docs.data if d.get("status") == "missing")
    expired = sum(1 for d in docs.data if d.get("status") == "expired")
    pending = sum(1 for d in docs.data if d.get("status") == "uploaded")
    
    return {"total_students": total, "fully_compliant": total - missing, "missing_docs": missing, "expired_docs": expired, "pending_verification": pending}


@router.get("")
async def list_documents(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    document_type: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    grade_id: Optional[str] = None,
    expired_only: bool = False,
    missing_only: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(require_teacher),
):
    """List documents with filters"""
    school_id = current_user.get("school_id")
    if not supabase_admin:
        return {"data": [], "total": 0}
    
    query = supabase_admin.table("student_documents").select("*, students!inner(school_id, first_name, last_name, admission_number, grade_id)", count="exact").eq("students.school_id", school_id)
    
    if entity_id:
        query = query.eq("student_id", entity_id)
    if document_type:
        query = query.eq("document_type", document_type)
    if status_filter:
        query = query.eq("status", status_filter)
    if grade_id:
        query = query.eq("students.grade_id", grade_id)
    if expired_only:
        query = query.eq("status", "expired")
    if missing_only:
        query = query.eq("status", "missing")
    
    result = query.range(skip, skip + limit - 1).order("created_at", desc=True).execute()
    return {"data": result.data, "total": result.count or 0}


@router.post("")
async def upload_document(document_data: Dict[str, Any], current_user: dict = Depends(require_office_admin)):
    """Upload a document"""
    user_id = current_user.get("id")
    doc_dict = {
        "student_id": document_data["entity_id"],
        "document_type": document_data["document_type"],
        "file_url": document_data.get("file_url"),
        "file_name": document_data.get("file_name"),
        "file_size": document_data.get("file_size"),
        "mime_type": document_data.get("mime_type"),
        "expiry_date": document_data.get("expiry_date"),
        "status": "uploaded",
        "uploaded": True,
        "uploaded_by": user_id,
        "notes": document_data.get("notes")
    }
    if supabase_admin:
        result = supabase_admin.table("student_documents").insert(doc_dict).execute()
        return result.data[0]
    return {**doc_dict, "id": "mock-doc"}


@router.patch("/{document_id}/verify")
async def verify_document(document_id: str, verify_data: Dict[str, Any], current_user: dict = Depends(require_office_admin)):
    """Verify or reject a document"""
    user_id = current_user.get("id")
    action = verify_data.get("action", "verify")
    update_data = {
        "status": "verified" if action == "verify" else "rejected",
        "verified": action == "verify",
        "verified_by": user_id,
        "verified_at": datetime.now().isoformat(),
        "notes": verify_data.get("notes")
    }
    if supabase_admin:
        result = supabase_admin.table("student_documents").update(update_data).eq("id", document_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Document not found")
        return result.data[0]
    return {"id": document_id, **update_data}


@router.post("/bulk-reminder")
async def send_bulk_reminder(reminder_data: Dict[str, Any], current_user: dict = Depends(require_office_admin)):
    """Send bulk document reminder"""
    school_id = current_user.get("school_id")
    user_id = current_user.get("id")
    target = reminder_data.get("target", "missing")
    grade_id = reminder_data.get("grade_id")
    
    # Create document requests
    if supabase_admin:
        query = supabase_admin.table("student_documents").select("student_id, document_type").eq("status", target)
        if grade_id:
            query = query.eq("students.grade_id", grade_id)
        docs = query.execute()
        
        requests = []
        for doc in docs.data:
            requests.append({
                "school_id": school_id,
                "entity_type": "student",
                "entity_id": doc["student_id"],
                "document_type": doc["document_type"],
                "requested_by": user_id,
                "message": reminder_data.get("message", "Please upload required document"),
                "status": "pending"
            })
        
        if requests:
            supabase_admin.table("document_requests").insert(requests).execute()
        return {"sent": len(requests)}
    return {"sent": 0}


@router.post("/request")
async def request_document(request_data: Dict[str, Any], current_user: dict = Depends(require_office_admin)):
    """Request specific document from student"""
    school_id = current_user.get("school_id")
    user_id = current_user.get("id")
    req_dict = {
        "school_id": school_id,
        "entity_type": "student",
        "entity_id": request_data["entity_id"],
        "document_type": request_data["document_type"],
        "requested_by": user_id,
        "message": request_data.get("message", ""),
        "status": "pending"
    }
    if supabase_admin:
        result = supabase_admin.table("document_requests").insert(req_dict).execute()
        return result.data[0]
    return {**req_dict, "id": "mock-request"}


@router.get("/requirements")
async def list_requirements(current_user: dict = Depends(require_teacher)):
    """List document requirements"""
    school_id = current_user.get("school_id")
    if supabase_admin:
        result = supabase_admin.table("document_requirements").select("*").eq("school_id", school_id).eq("active", True).execute()
        return result.data
    return []


@router.post("/requirements")
async def create_requirement(requirement_data: Dict[str, Any], current_user: dict = Depends(require_office_admin)):
    """Create document requirement"""
    school_id = current_user.get("school_id")
    req_dict = {
        "school_id": school_id,
        "entity_type": requirement_data["entity_type"],
        "document_type": requirement_data["document_type"],
        "required": requirement_data.get("required", True),
        "grade_id": requirement_data.get("grade_id"),
        "active": True
    }
    if supabase_admin:
        result = supabase_admin.table("document_requirements").insert(req_dict).execute()
        return result.data[0]
    return {**req_dict, "id": "mock-req"}


@router.get("/export")
async def export_documents(format: str = Query("csv"), status: Optional[str] = None, current_user: dict = Depends(require_office_admin)):
    """Export documents compliance report"""
    return {"message": "Export functionality", "format": format}
