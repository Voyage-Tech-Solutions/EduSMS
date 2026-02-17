"""
EduCore Backend - Teaching Resources API
Resource library for lesson planning
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

class ResourceCreate(BaseModel):
    """Create a teaching resource"""
    title: str
    description: Optional[str] = None
    resource_type: str  # document, video, link, worksheet, presentation, image, audio
    subject_id: Optional[UUID] = None
    grade_ids: Optional[List[UUID]] = None
    file_url: Optional[str] = None
    external_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    tags: List[str] = []
    standard_ids: Optional[List[UUID]] = None
    is_shared: bool = False
    metadata: Optional[dict] = None  # Duration, pages, file size, etc.


class ResourceUpdate(BaseModel):
    """Update a teaching resource"""
    title: Optional[str] = None
    description: Optional[str] = None
    resource_type: Optional[str] = None
    file_url: Optional[str] = None
    external_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    tags: Optional[List[str]] = None
    standard_ids: Optional[List[UUID]] = None
    is_shared: Optional[bool] = None
    is_active: Optional[bool] = None
    metadata: Optional[dict] = None


class ResourceCollectionCreate(BaseModel):
    """Create a resource collection"""
    name: str
    description: Optional[str] = None
    subject_id: Optional[UUID] = None
    resource_ids: List[UUID] = []
    is_shared: bool = False


# ============================================================
# RESOURCE ENDPOINTS
# ============================================================

@router.get("")
async def list_resources(
    resource_type: Optional[str] = None,
    subject_id: Optional[UUID] = None,
    grade_id: Optional[UUID] = None,
    tag: Optional[str] = None,
    standard_id: Optional[UUID] = None,
    include_shared: bool = True,
    search: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List teaching resources with filters"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    query = supabase.table("teaching_resources").select(
        "*, subjects(name)"
    ).eq("school_id", school_id).eq("is_active", True)

    # Ownership filter
    if not include_shared:
        query = query.eq("created_by", user_id)
    else:
        query = query.or_(f"created_by.eq.{user_id},is_shared.eq.true")

    if resource_type:
        query = query.eq("resource_type", resource_type)
    if subject_id:
        query = query.eq("subject_id", str(subject_id))
    if grade_id:
        query = query.contains("grade_ids", [str(grade_id)])
    if tag:
        query = query.contains("tags", [tag])
    if standard_id:
        query = query.contains("standard_ids", [str(standard_id)])
    if search:
        query = query.or_(f"title.ilike.%{search}%,description.ilike.%{search}%")

    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

    result = query.execute()

    return {
        "resources": result.data or [],
        "total": len(result.data) if result.data else 0,
        "limit": limit,
        "offset": offset
    }


@router.get("/tags")
async def get_resource_tags(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get all unique tags used in resources"""
    school_id = current_user.get("school_id")

    result = supabase.table("teaching_resources").select("tags").eq(
        "school_id", school_id
    ).eq("is_active", True).execute()

    all_tags = set()
    for resource in (result.data or []):
        tags = resource.get("tags") or []
        all_tags.update(tags)

    return {"tags": sorted(list(all_tags))}


@router.get("/types")
async def get_resource_types(
    current_user: dict = Depends(get_current_user)
):
    """Get available resource types"""
    return {
        "types": [
            {"id": "document", "name": "Document", "extensions": [".pdf", ".doc", ".docx"]},
            {"id": "video", "name": "Video", "extensions": [".mp4", ".mov", ".webm"]},
            {"id": "link", "name": "External Link", "extensions": []},
            {"id": "worksheet", "name": "Worksheet", "extensions": [".pdf", ".doc", ".docx"]},
            {"id": "presentation", "name": "Presentation", "extensions": [".ppt", ".pptx", ".pdf"]},
            {"id": "image", "name": "Image", "extensions": [".jpg", ".png", ".gif", ".svg"]},
            {"id": "audio", "name": "Audio", "extensions": [".mp3", ".wav", ".m4a"]},
            {"id": "interactive", "name": "Interactive", "extensions": [".html"]},
            {"id": "spreadsheet", "name": "Spreadsheet", "extensions": [".xls", ".xlsx", ".csv"]}
        ]
    }


@router.get("/{resource_id}")
async def get_resource(
    resource_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get a specific resource"""
    result = supabase.table("teaching_resources").select(
        "*, subjects(name)"
    ).eq("id", str(resource_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Resource not found")

    # Get standards if present
    resource = result.data
    if resource.get("standard_ids"):
        standards = supabase.table("learning_standards").select(
            "id, code, description"
        ).in_("id", resource["standard_ids"]).execute()
        resource["standards"] = standards.data or []

    # Track view (increment usage count)
    supabase.table("teaching_resources").update({
        "usage_count": (resource.get("usage_count") or 0) + 1
    }).eq("id", str(resource_id)).execute()

    return resource


@router.post("")
async def create_resource(
    resource: ResourceCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a new teaching resource"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    resource_data = {
        "school_id": school_id,
        "created_by": user_id,
        "title": resource.title,
        "description": resource.description,
        "resource_type": resource.resource_type,
        "subject_id": str(resource.subject_id) if resource.subject_id else None,
        "grade_ids": [str(g) for g in resource.grade_ids] if resource.grade_ids else None,
        "file_url": resource.file_url,
        "external_url": resource.external_url,
        "thumbnail_url": resource.thumbnail_url,
        "tags": resource.tags,
        "standard_ids": [str(s) for s in resource.standard_ids] if resource.standard_ids else None,
        "is_shared": resource.is_shared,
        "metadata": resource.metadata,
        "usage_count": 0,
        "is_active": True
    }

    result = supabase.table("teaching_resources").insert(resource_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create resource")

    return result.data[0]


@router.put("/{resource_id}")
async def update_resource(
    resource_id: UUID,
    update: ResourceUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update a teaching resource"""
    user_id = current_user["id"]

    existing = supabase.table("teaching_resources").select(
        "created_by"
    ).eq("id", str(resource_id)).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Resource not found")

    if existing.data["created_by"] != user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own resources")

    update_data = {}
    if update.title is not None:
        update_data["title"] = update.title
    if update.description is not None:
        update_data["description"] = update.description
    if update.resource_type is not None:
        update_data["resource_type"] = update.resource_type
    if update.file_url is not None:
        update_data["file_url"] = update.file_url
    if update.external_url is not None:
        update_data["external_url"] = update.external_url
    if update.thumbnail_url is not None:
        update_data["thumbnail_url"] = update.thumbnail_url
    if update.tags is not None:
        update_data["tags"] = update.tags
    if update.standard_ids is not None:
        update_data["standard_ids"] = [str(s) for s in update.standard_ids]
    if update.is_shared is not None:
        update_data["is_shared"] = update.is_shared
    if update.is_active is not None:
        update_data["is_active"] = update.is_active
    if update.metadata is not None:
        update_data["metadata"] = update.metadata

    result = supabase.table("teaching_resources").update(update_data).eq(
        "id", str(resource_id)
    ).execute()

    return result.data[0] if result.data else None


@router.delete("/{resource_id}")
async def delete_resource(
    resource_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a teaching resource"""
    user_id = current_user["id"]

    existing = supabase.table("teaching_resources").select(
        "created_by"
    ).eq("id", str(resource_id)).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Resource not found")

    if existing.data["created_by"] != user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own resources")

    supabase.table("teaching_resources").update({
        "is_active": False
    }).eq("id", str(resource_id)).execute()

    return {"success": True}


@router.post("/{resource_id}/duplicate")
async def duplicate_resource(
    resource_id: UUID,
    new_title: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a copy of a resource"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    original = supabase.table("teaching_resources").select("*").eq(
        "id", str(resource_id)
    ).single().execute()

    if not original.data:
        raise HTTPException(status_code=404, detail="Resource not found")

    new_resource = {**original.data}
    del new_resource["id"]
    del new_resource["created_at"]
    del new_resource["updated_at"]
    new_resource["created_by"] = user_id
    new_resource["school_id"] = school_id
    new_resource["title"] = new_title or f"(Copy) {new_resource['title']}"
    new_resource["is_shared"] = False
    new_resource["usage_count"] = 0

    result = supabase.table("teaching_resources").insert(new_resource).execute()

    return result.data[0] if result.data else None


# ============================================================
# RESOURCE COLLECTION ENDPOINTS
# ============================================================

@router.get("/collections")
async def list_collections(
    subject_id: Optional[UUID] = None,
    include_shared: bool = True,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List resource collections"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    query = supabase.table("resource_collections").select(
        "*, subjects(name)"
    ).eq("school_id", school_id).eq("is_active", True)

    if not include_shared:
        query = query.eq("created_by", user_id)
    else:
        query = query.or_(f"created_by.eq.{user_id},is_shared.eq.true")

    if subject_id:
        query = query.eq("subject_id", str(subject_id))

    query = query.order("name").range(offset, offset + limit - 1)

    result = query.execute()

    # Add resource count
    collections = result.data or []
    for collection in collections:
        resource_ids = collection.get("resource_ids") or []
        collection["resource_count"] = len(resource_ids)

    return {
        "collections": collections,
        "total": len(collections),
        "limit": limit,
        "offset": offset
    }


@router.get("/collections/{collection_id}")
async def get_collection(
    collection_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get a collection with its resources"""
    result = supabase.table("resource_collections").select(
        "*, subjects(name)"
    ).eq("id", str(collection_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Collection not found")

    collection = result.data
    resource_ids = collection.get("resource_ids") or []

    if resource_ids:
        resources = supabase.table("teaching_resources").select(
            "id, title, resource_type, thumbnail_url"
        ).in_("id", resource_ids).eq("is_active", True).execute()
        collection["resources"] = resources.data or []
    else:
        collection["resources"] = []

    return collection


@router.post("/collections")
async def create_collection(
    collection: ResourceCollectionCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a resource collection"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    collection_data = {
        "school_id": school_id,
        "created_by": user_id,
        "name": collection.name,
        "description": collection.description,
        "subject_id": str(collection.subject_id) if collection.subject_id else None,
        "resource_ids": [str(r) for r in collection.resource_ids],
        "is_shared": collection.is_shared,
        "is_active": True
    }

    result = supabase.table("resource_collections").insert(collection_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create collection")

    return result.data[0]


@router.put("/collections/{collection_id}")
async def update_collection(
    collection_id: UUID,
    name: Optional[str] = None,
    description: Optional[str] = None,
    resource_ids: Optional[List[UUID]] = None,
    is_shared: Optional[bool] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update a resource collection"""
    user_id = current_user["id"]

    existing = supabase.table("resource_collections").select(
        "created_by"
    ).eq("id", str(collection_id)).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Collection not found")

    if existing.data["created_by"] != user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own collections")

    update_data = {}
    if name is not None:
        update_data["name"] = name
    if description is not None:
        update_data["description"] = description
    if resource_ids is not None:
        update_data["resource_ids"] = [str(r) for r in resource_ids]
    if is_shared is not None:
        update_data["is_shared"] = is_shared

    result = supabase.table("resource_collections").update(update_data).eq(
        "id", str(collection_id)
    ).execute()

    return result.data[0] if result.data else None


@router.post("/collections/{collection_id}/add")
async def add_to_collection(
    collection_id: UUID,
    resource_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Add a resource to a collection"""
    user_id = current_user["id"]

    collection = supabase.table("resource_collections").select(
        "created_by, resource_ids"
    ).eq("id", str(collection_id)).single().execute()

    if not collection.data:
        raise HTTPException(status_code=404, detail="Collection not found")

    if collection.data["created_by"] != user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own collections")

    resource_ids = collection.data.get("resource_ids") or []
    if str(resource_id) not in resource_ids:
        resource_ids.append(str(resource_id))

        supabase.table("resource_collections").update({
            "resource_ids": resource_ids
        }).eq("id", str(collection_id)).execute()

    return {"success": True}


@router.post("/collections/{collection_id}/remove")
async def remove_from_collection(
    collection_id: UUID,
    resource_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Remove a resource from a collection"""
    user_id = current_user["id"]

    collection = supabase.table("resource_collections").select(
        "created_by, resource_ids"
    ).eq("id", str(collection_id)).single().execute()

    if not collection.data:
        raise HTTPException(status_code=404, detail="Collection not found")

    if collection.data["created_by"] != user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own collections")

    resource_ids = collection.data.get("resource_ids") or []
    if str(resource_id) in resource_ids:
        resource_ids.remove(str(resource_id))

        supabase.table("resource_collections").update({
            "resource_ids": resource_ids
        }).eq("id", str(collection_id)).execute()

    return {"success": True}


@router.delete("/collections/{collection_id}")
async def delete_collection(
    collection_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a resource collection"""
    user_id = current_user["id"]

    existing = supabase.table("resource_collections").select(
        "created_by"
    ).eq("id", str(collection_id)).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Collection not found")

    if existing.data["created_by"] != user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own collections")

    supabase.table("resource_collections").update({
        "is_active": False
    }).eq("id", str(collection_id)).execute()

    return {"success": True}
