"""
EduCore Backend - File Storage Utilities
Supabase Storage integration for file uploads and management
"""
import logging
import mimetypes
import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, BinaryIO, Union
from uuid import uuid4
from enum import Enum
from io import BytesIO

from PIL import Image
from fastapi import UploadFile, HTTPException

from app.core.config import settings
from app.db.supabase import get_supabase_admin

logger = logging.getLogger(__name__)


class StorageBucket(str, Enum):
    """Available storage buckets"""
    AVATARS = "avatars"
    DOCUMENTS = "documents"
    ATTACHMENTS = "attachments"
    PHOTOS = "photos"
    REPORTS = "reports"
    SUBMISSIONS = "submissions"
    IMPORTS = "imports"
    EXPORTS = "exports"


class FileCategory(str, Enum):
    """File categories for organization"""
    PROFILE = "profile"
    STUDENT_DOCUMENT = "student_document"
    ACADEMIC = "academic"
    FINANCIAL = "financial"
    ADMINISTRATIVE = "administrative"
    ASSIGNMENT = "assignment"
    REPORT = "report"


# Allowed MIME types by category
ALLOWED_MIME_TYPES = {
    FileCategory.PROFILE: ["image/jpeg", "image/png", "image/webp"],
    FileCategory.STUDENT_DOCUMENT: [
        "application/pdf",
        "image/jpeg", "image/png",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ],
    FileCategory.ACADEMIC: [
        "application/pdf",
        "image/jpeg", "image/png",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ],
    FileCategory.FINANCIAL: [
        "application/pdf",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/csv"
    ],
    FileCategory.ASSIGNMENT: [
        "application/pdf",
        "image/jpeg", "image/png",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
    ],
}

# Maximum file sizes by category (in bytes)
MAX_FILE_SIZES = {
    FileCategory.PROFILE: 5 * 1024 * 1024,  # 5MB
    FileCategory.STUDENT_DOCUMENT: 10 * 1024 * 1024,  # 10MB
    FileCategory.ACADEMIC: 20 * 1024 * 1024,  # 20MB
    FileCategory.FINANCIAL: 10 * 1024 * 1024,  # 10MB
    FileCategory.ASSIGNMENT: 50 * 1024 * 1024,  # 50MB
    FileCategory.REPORT: 20 * 1024 * 1024,  # 20MB
}


class StorageManager:
    """
    Manages file storage operations with Supabase Storage.

    Features:
    - Secure file uploads with validation
    - Image optimization and resizing
    - Signed URLs for private access
    - File organization by school/user
    - Metadata tracking
    """

    def __init__(self):
        self.supabase = get_supabase_admin()

    def _get_bucket(self, category: FileCategory) -> str:
        """Map category to storage bucket"""
        bucket_map = {
            FileCategory.PROFILE: StorageBucket.AVATARS,
            FileCategory.STUDENT_DOCUMENT: StorageBucket.DOCUMENTS,
            FileCategory.ACADEMIC: StorageBucket.DOCUMENTS,
            FileCategory.FINANCIAL: StorageBucket.DOCUMENTS,
            FileCategory.ASSIGNMENT: StorageBucket.SUBMISSIONS,
            FileCategory.REPORT: StorageBucket.REPORTS,
        }
        return bucket_map.get(category, StorageBucket.ATTACHMENTS).value

    def _generate_file_path(
        self,
        school_id: str,
        category: FileCategory,
        filename: str,
        user_id: Optional[str] = None
    ) -> str:
        """Generate organized file path"""
        # Generate unique filename
        ext = os.path.splitext(filename)[1].lower()
        unique_name = f"{uuid4().hex}{ext}"

        # Build path: school_id/category/[user_id/]year-month/filename
        date_folder = datetime.utcnow().strftime("%Y-%m")

        if user_id:
            return f"{school_id}/{category.value}/{user_id}/{date_folder}/{unique_name}"
        return f"{school_id}/{category.value}/{date_folder}/{unique_name}"

    def _validate_file(
        self,
        file: UploadFile,
        category: FileCategory,
        content: bytes
    ) -> Dict[str, Any]:
        """
        Validate file type and size.

        Returns:
            File metadata if valid

        Raises:
            HTTPException if validation fails
        """
        # Check file size
        max_size = MAX_FILE_SIZES.get(category, 10 * 1024 * 1024)
        if len(content) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {max_size // (1024*1024)}MB"
            )

        # Detect MIME type
        mime_type = file.content_type
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(file.filename)

        # Validate MIME type
        allowed_types = ALLOWED_MIME_TYPES.get(category, [])
        if allowed_types and mime_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(allowed_types)}"
            )

        # Calculate hash for deduplication
        file_hash = hashlib.sha256(content).hexdigest()

        return {
            "original_name": file.filename,
            "mime_type": mime_type,
            "size": len(content),
            "hash": file_hash
        }

    def _optimize_image(
        self,
        content: bytes,
        max_width: int = 1920,
        max_height: int = 1080,
        quality: int = 85
    ) -> bytes:
        """Optimize image by resizing and compressing"""
        try:
            img = Image.open(BytesIO(content))

            # Convert to RGB if necessary
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Resize if larger than max dimensions
            if img.width > max_width or img.height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            # Save optimized
            output = BytesIO()
            img.save(output, format="JPEG", quality=quality, optimize=True)
            output.seek(0)
            return output.read()

        except Exception as e:
            logger.warning(f"Image optimization failed: {e}")
            return content

    def _create_thumbnail(
        self,
        content: bytes,
        size: tuple = (200, 200)
    ) -> Optional[bytes]:
        """Create a thumbnail for an image"""
        try:
            img = Image.open(BytesIO(content))

            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            img.thumbnail(size, Image.Resampling.LANCZOS)

            output = BytesIO()
            img.save(output, format="JPEG", quality=80)
            output.seek(0)
            return output.read()

        except Exception as e:
            logger.warning(f"Thumbnail creation failed: {e}")
            return None

    async def upload_file(
        self,
        file: UploadFile,
        school_id: str,
        category: FileCategory,
        user_id: Optional[str] = None,
        optimize_images: bool = True,
        create_thumbnail: bool = False,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to storage.

        Args:
            file: FastAPI UploadFile
            school_id: School UUID
            category: File category
            user_id: Optional user UUID
            optimize_images: Whether to optimize image files
            create_thumbnail: Whether to create thumbnail for images
            metadata: Additional metadata to store

        Returns:
            Upload result with URLs and metadata
        """
        # Read file content
        content = await file.read()

        # Validate file
        file_meta = self._validate_file(file, category, content)

        # Optimize images if requested
        is_image = file_meta["mime_type"].startswith("image/")
        if is_image and optimize_images:
            content = self._optimize_image(content)
            file_meta["size"] = len(content)
            file_meta["optimized"] = True

        # Generate file path
        bucket = self._get_bucket(category)
        file_path = self._generate_file_path(school_id, category, file.filename, user_id)

        try:
            # Upload to Supabase Storage
            self.supabase.storage.from_(bucket).upload(
                path=file_path,
                file=content,
                file_options={
                    "content-type": file_meta["mime_type"],
                    "cache-control": "3600"
                }
            )

            # Get public URL
            url = self.supabase.storage.from_(bucket).get_public_url(file_path)

            result = {
                "success": True,
                "bucket": bucket,
                "path": file_path,
                "url": url,
                "metadata": file_meta,
                "uploaded_at": datetime.utcnow().isoformat()
            }

            # Create thumbnail if requested
            if is_image and create_thumbnail:
                thumbnail_content = self._create_thumbnail(content)
                if thumbnail_content:
                    thumb_path = file_path.replace(".", "_thumb.")
                    self.supabase.storage.from_(bucket).upload(
                        path=thumb_path,
                        file=thumbnail_content,
                        file_options={"content-type": "image/jpeg"}
                    )
                    result["thumbnail_url"] = self.supabase.storage.from_(bucket).get_public_url(thumb_path)

            # Store metadata in database
            if metadata:
                await self._store_file_metadata(
                    school_id=school_id,
                    file_path=file_path,
                    bucket=bucket,
                    metadata={**file_meta, **metadata},
                    user_id=user_id
                )

            logger.info(f"File uploaded: {file_path}")
            return result

        except Exception as e:
            logger.error(f"File upload failed: {e}")
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    async def _store_file_metadata(
        self,
        school_id: str,
        file_path: str,
        bucket: str,
        metadata: Dict,
        user_id: Optional[str] = None
    ):
        """Store file metadata in database for tracking"""
        try:
            self.supabase.table("file_uploads").insert({
                "school_id": school_id,
                "user_id": user_id,
                "bucket": bucket,
                "file_path": file_path,
                "original_name": metadata.get("original_name"),
                "mime_type": metadata.get("mime_type"),
                "size": metadata.get("size"),
                "hash": metadata.get("hash"),
                "metadata": metadata,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
        except Exception as e:
            logger.warning(f"Failed to store file metadata: {e}")

    async def get_signed_url(
        self,
        bucket: str,
        file_path: str,
        expires_in: int = 3600
    ) -> str:
        """
        Get a signed URL for private file access.

        Args:
            bucket: Storage bucket name
            file_path: Path to file
            expires_in: URL expiration in seconds

        Returns:
            Signed URL
        """
        try:
            result = self.supabase.storage.from_(bucket).create_signed_url(
                path=file_path,
                expires_in=expires_in
            )
            return result.get("signedURL")
        except Exception as e:
            logger.error(f"Failed to create signed URL: {e}")
            raise HTTPException(status_code=500, detail="Could not generate download URL")

    async def delete_file(
        self,
        bucket: str,
        file_path: str
    ) -> bool:
        """
        Delete a file from storage.

        Args:
            bucket: Storage bucket name
            file_path: Path to file

        Returns:
            True if successful
        """
        try:
            self.supabase.storage.from_(bucket).remove([file_path])

            # Also delete thumbnail if exists
            thumb_path = file_path.replace(".", "_thumb.")
            try:
                self.supabase.storage.from_(bucket).remove([thumb_path])
            except Exception:
                pass

            # Remove from metadata table
            self.supabase.table("file_uploads").delete().eq(
                "file_path", file_path
            ).execute()

            logger.info(f"File deleted: {file_path}")
            return True

        except Exception as e:
            logger.error(f"File deletion failed: {e}")
            return False

    async def list_files(
        self,
        bucket: str,
        path: str = "",
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """
        List files in a storage path.

        Args:
            bucket: Storage bucket name
            path: Directory path
            limit: Maximum files to return
            offset: Pagination offset

        Returns:
            List of file metadata
        """
        try:
            result = self.supabase.storage.from_(bucket).list(
                path=path,
                options={
                    "limit": limit,
                    "offset": offset
                }
            )
            return result
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []

    async def move_file(
        self,
        bucket: str,
        from_path: str,
        to_path: str
    ) -> bool:
        """Move a file to a new location"""
        try:
            self.supabase.storage.from_(bucket).move(from_path, to_path)
            return True
        except Exception as e:
            logger.error(f"File move failed: {e}")
            return False

    async def copy_file(
        self,
        bucket: str,
        from_path: str,
        to_path: str
    ) -> bool:
        """Copy a file to a new location"""
        try:
            self.supabase.storage.from_(bucket).copy(from_path, to_path)
            return True
        except Exception as e:
            logger.error(f"File copy failed: {e}")
            return False


# Global storage manager instance
storage_manager = StorageManager()


async def upload_avatar(
    file: UploadFile,
    user_id: str,
    school_id: str
) -> Dict[str, Any]:
    """Convenience function for avatar uploads"""
    return await storage_manager.upload_file(
        file=file,
        school_id=school_id,
        category=FileCategory.PROFILE,
        user_id=user_id,
        optimize_images=True,
        create_thumbnail=True
    )


async def upload_document(
    file: UploadFile,
    school_id: str,
    category: FileCategory = FileCategory.STUDENT_DOCUMENT,
    user_id: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> Dict[str, Any]:
    """Convenience function for document uploads"""
    return await storage_manager.upload_file(
        file=file,
        school_id=school_id,
        category=category,
        user_id=user_id,
        optimize_images=False,
        metadata=metadata
    )
