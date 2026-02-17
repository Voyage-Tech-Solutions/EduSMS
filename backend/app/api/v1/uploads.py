"""
EduCore Backend - File Upload API
Endpoints for file upload and management
"""
import logging
from typing import Optional, List

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query
from pydantic import BaseModel

from app.core.storage import (
    storage_manager, upload_avatar, upload_document,
    FileCategory, StorageBucket
)
from app.api.deps import get_current_user, get_supabase
from app.core.audit import audit_logger, AuditAction

logger = logging.getLogger(__name__)
router = APIRouter()


class UploadResponse(BaseModel):
    """Response model for file uploads"""
    success: bool
    url: str
    thumbnail_url: Optional[str] = None
    path: str
    bucket: str
    original_name: str
    mime_type: str
    size: int


class FileInfo(BaseModel):
    """File information model"""
    name: str
    path: str
    size: int
    mime_type: Optional[str] = None
    created_at: Optional[str] = None


@router.post("/avatar", response_model=UploadResponse)
async def upload_user_avatar(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Upload a user avatar image.

    Accepts: JPEG, PNG, WebP
    Max size: 5MB
    Images are automatically optimized and thumbnailed.
    """
    user_id = current_user["id"]
    school_id = current_user.get("school_id")

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    result = await upload_avatar(
        file=file,
        user_id=user_id,
        school_id=school_id
    )

    # Update user profile with new avatar URL
    supabase.table("user_profiles").update({
        "avatar_url": result["url"]
    }).eq("id", user_id).execute()

    # Audit log
    await audit_logger.log(
        supabase=supabase,
        action="profile.avatar_update",
        user_id=user_id,
        school_id=school_id,
        entity_type="user_profile",
        entity_id=user_id,
        metadata={"file_path": result["path"]}
    )

    return UploadResponse(
        success=True,
        url=result["url"],
        thumbnail_url=result.get("thumbnail_url"),
        path=result["path"],
        bucket=result["bucket"],
        original_name=result["metadata"]["original_name"],
        mime_type=result["metadata"]["mime_type"],
        size=result["metadata"]["size"]
    )


@router.post("/document", response_model=UploadResponse)
async def upload_document_file(
    file: UploadFile = File(...),
    category: str = Form("student_document"),
    entity_type: Optional[str] = Form(None),
    entity_id: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Upload a document file.

    Categories:
    - student_document: Student records, certificates
    - academic: Academic materials, assessments
    - financial: Financial documents, receipts
    - administrative: Administrative documents
    - assignment: Assignment submissions

    Accepts: PDF, Word docs, Excel, Images
    Max size: 10-50MB depending on category
    """
    user_id = current_user["id"]
    school_id = current_user.get("school_id")

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    # Validate category
    try:
        file_category = FileCategory(category)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid category: {category}")

    metadata = {
        "uploaded_by": user_id,
        "description": description
    }

    if entity_type and entity_id:
        metadata["entity_type"] = entity_type
        metadata["entity_id"] = entity_id

    result = await upload_document(
        file=file,
        school_id=school_id,
        category=file_category,
        user_id=user_id,
        metadata=metadata
    )

    # Audit log
    await audit_logger.log(
        supabase=supabase,
        action="document.upload",
        user_id=user_id,
        school_id=school_id,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata={
            "file_path": result["path"],
            "category": category,
            "original_name": result["metadata"]["original_name"]
        }
    )

    return UploadResponse(
        success=True,
        url=result["url"],
        thumbnail_url=result.get("thumbnail_url"),
        path=result["path"],
        bucket=result["bucket"],
        original_name=result["metadata"]["original_name"],
        mime_type=result["metadata"]["mime_type"],
        size=result["metadata"]["size"]
    )


@router.post("/student/{student_id}/document", response_model=UploadResponse)
async def upload_student_document(
    student_id: str,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    description: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Upload a document for a specific student.

    Document types:
    - birth_certificate
    - transfer_certificate
    - medical_record
    - report_card
    - photo_id
    - other
    """
    user_id = current_user["id"]
    school_id = current_user.get("school_id")

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    # Verify student belongs to school
    student = supabase.table("students").select("id").eq(
        "id", student_id
    ).eq("school_id", school_id).single().execute()

    if not student.data:
        raise HTTPException(status_code=404, detail="Student not found")

    result = await upload_document(
        file=file,
        school_id=school_id,
        category=FileCategory.STUDENT_DOCUMENT,
        user_id=user_id,
        metadata={
            "student_id": student_id,
            "document_type": document_type,
            "description": description,
            "uploaded_by": user_id
        }
    )

    # Audit log
    await audit_logger.log(
        supabase=supabase,
        action="student.document_upload",
        user_id=user_id,
        school_id=school_id,
        entity_type="student",
        entity_id=student_id,
        metadata={
            "document_type": document_type,
            "file_path": result["path"]
        }
    )

    return UploadResponse(
        success=True,
        url=result["url"],
        thumbnail_url=result.get("thumbnail_url"),
        path=result["path"],
        bucket=result["bucket"],
        original_name=result["metadata"]["original_name"],
        mime_type=result["metadata"]["mime_type"],
        size=result["metadata"]["size"]
    )


@router.get("/signed-url")
async def get_signed_url(
    bucket: str = Query(...),
    path: str = Query(...),
    expires_in: int = Query(default=3600, ge=60, le=86400),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a signed URL for private file access.

    Args:
        bucket: Storage bucket name
        path: File path
        expires_in: URL expiration in seconds (1 min to 24 hours)

    Returns:
        Signed URL valid for the specified duration
    """
    school_id = current_user.get("school_id")

    # Verify file belongs to user's school (path should start with school_id)
    if school_id and not path.startswith(school_id):
        raise HTTPException(status_code=403, detail="Access denied")

    url = await storage_manager.get_signed_url(bucket, path, expires_in)

    return {"signed_url": url, "expires_in": expires_in}


@router.delete("/file")
async def delete_file(
    bucket: str = Query(...),
    path: str = Query(...),
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Delete a file from storage.

    Only admins can delete files, or the user who uploaded them.
    """
    user_id = current_user["id"]
    school_id = current_user.get("school_id")
    role = current_user.get("role")

    # Verify ownership or admin access
    if school_id and not path.startswith(school_id):
        raise HTTPException(status_code=403, detail="Access denied")

    # Check if user owns the file or is admin
    if role not in ["system_admin", "principal", "office_admin"]:
        file_record = supabase.table("file_uploads").select("user_id").eq(
            "file_path", path
        ).single().execute()

        if file_record.data and file_record.data["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="You can only delete your own files")

    success = await storage_manager.delete_file(bucket, path)

    if success:
        # Audit log
        await audit_logger.log(
            supabase=supabase,
            action="file.delete",
            user_id=user_id,
            school_id=school_id,
            metadata={"bucket": bucket, "path": path}
        )
        return {"success": True, "message": "File deleted"}

    raise HTTPException(status_code=500, detail="Failed to delete file")


@router.get("/list", response_model=List[FileInfo])
async def list_files(
    bucket: str = Query(default="documents"),
    path: str = Query(default=""),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """
    List files in a storage path.

    Only returns files from the user's school.
    """
    school_id = current_user.get("school_id")

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    # Ensure path is within school's directory
    full_path = f"{school_id}/{path}" if path else school_id

    files = await storage_manager.list_files(bucket, full_path, limit, offset)

    return [
        FileInfo(
            name=f.get("name", ""),
            path=f"{full_path}/{f.get('name', '')}",
            size=f.get("metadata", {}).get("size", 0),
            mime_type=f.get("metadata", {}).get("mimetype"),
            created_at=f.get("created_at")
        )
        for f in files
    ]
