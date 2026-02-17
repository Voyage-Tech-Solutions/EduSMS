"""
EduCore Backend - Announcements API
School-wide and targeted announcements
"""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# MODELS
# ============================================================

class AnnouncementCreate(BaseModel):
    """Create an announcement"""
    title: str
    content: str
    category: str = "general"  # general, academic, event, emergency, reminder
    priority: str = "normal"  # low, normal, high, urgent
    target_audience: List[str] = ["all"]  # all, teachers, parents, students, staff, grades, classes
    target_grade_ids: List[UUID] = []
    target_class_ids: List[UUID] = []
    publish_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    allow_comments: bool = False
    send_notification: bool = True
    send_email: bool = False
    send_sms: bool = False
    attachments: List[str] = []
    pin_to_top: bool = False


class AnnouncementUpdate(BaseModel):
    """Update an announcement"""
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    expires_at: Optional[datetime] = None
    pin_to_top: Optional[bool] = None


# ============================================================
# ANNOUNCEMENT CRUD
# ============================================================

@router.get("")
async def list_announcements(
    category: Optional[str] = None,
    active_only: bool = True,
    limit: int = Query(default=20, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List announcements for current user"""
    school_id = current_user.get("school_id")
    user_role = current_user.get("role")
    now = datetime.utcnow()

    query = supabase.table("announcements").select(
        "*, author:author_id(first_name, last_name)"
    ).eq("school_id", school_id).eq("status", "published")

    if active_only:
        query = query.lte("publish_at", now.isoformat())
        # Also filter out expired
        query = query.or_(f"expires_at.is.null,expires_at.gt.{now.isoformat()}")

    if category:
        query = query.eq("category", category)

    query = query.order("pin_to_top", desc=True).order("publish_at", desc=True)
    query = query.range(offset, offset + limit - 1)

    result = query.execute()

    # Filter by target audience
    announcements = []
    for ann in (result.data or []):
        audience = ann.get("target_audience", ["all"])
        if "all" in audience or user_role in audience:
            announcements.append(ann)

    return {
        "announcements": announcements,
        "limit": limit,
        "offset": offset
    }


@router.get("/manage")
async def list_managed_announcements(
    status: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List announcements for management (admin/principal)"""
    school_id = current_user.get("school_id")
    user_role = current_user.get("role")

    if user_role not in ["principal", "office_admin", "system_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    query = supabase.table("announcements").select(
        "*, author:author_id(first_name, last_name)"
    ).eq("school_id", school_id)

    if status:
        query = query.eq("status", status)

    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

    result = query.execute()

    return {"announcements": result.data or []}


@router.get("/{announcement_id}")
async def get_announcement(
    announcement_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get announcement details"""
    result = supabase.table("announcements").select(
        "*, author:author_id(first_name, last_name, email)"
    ).eq("id", str(announcement_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Announcement not found")

    # Track view
    user_id = current_user.get("id")
    supabase.table("announcement_views").upsert({
        "announcement_id": str(announcement_id),
        "user_id": user_id,
        "viewed_at": datetime.utcnow().isoformat()
    }, on_conflict="announcement_id,user_id").execute()

    # Get comments if enabled
    comments = []
    if result.data.get("allow_comments"):
        comments_result = supabase.table("announcement_comments").select(
            "*, author:author_id(first_name, last_name)"
        ).eq("announcement_id", str(announcement_id)).order("created_at").execute()
        comments = comments_result.data or []

    return {
        **result.data,
        "comments": comments
    }


@router.post("")
async def create_announcement(
    announcement: AnnouncementCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a new announcement"""
    school_id = current_user.get("school_id")
    user_id = current_user.get("id")
    user_role = current_user.get("role")

    if user_role not in ["principal", "office_admin", "system_admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Not authorized to create announcements")

    now = datetime.utcnow()
    publish_at = announcement.publish_at or now

    ann_data = {
        "school_id": school_id,
        "author_id": user_id,
        "title": announcement.title,
        "content": announcement.content,
        "category": announcement.category,
        "priority": announcement.priority,
        "target_audience": announcement.target_audience,
        "target_grade_ids": [str(g) for g in announcement.target_grade_ids],
        "target_class_ids": [str(c) for c in announcement.target_class_ids],
        "publish_at": publish_at.isoformat(),
        "expires_at": announcement.expires_at.isoformat() if announcement.expires_at else None,
        "allow_comments": announcement.allow_comments,
        "attachments": announcement.attachments,
        "pin_to_top": announcement.pin_to_top,
        "status": "published" if publish_at <= now else "scheduled"
    }

    result = supabase.table("announcements").insert(ann_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create announcement")

    ann_id = result.data[0]["id"]

    # Send notifications if enabled
    if announcement.send_notification:
        background_tasks.add_task(
            _send_announcement_notifications,
            ann_id,
            announcement,
            school_id,
            supabase
        )

    return result.data[0]


async def _send_announcement_notifications(ann_id, announcement, school_id, supabase):
    """Background task to send announcement notifications"""
    # Get target users based on audience
    target_users = []

    if "all" in announcement.target_audience:
        # Get all users for school
        users = supabase.table("user_profiles").select("id, email").eq(
            "school_id", school_id
        ).execute()
        target_users = users.data or []
    else:
        # Get specific roles
        for role in announcement.target_audience:
            users = supabase.table("user_profiles").select("id, email").eq(
                "school_id", school_id
            ).eq("role", role).execute()
            target_users.extend(users.data or [])

    # Create notification records
    for user in target_users:
        supabase.table("notifications").insert({
            "school_id": school_id,
            "user_id": user["id"],
            "notification_type": "announcement",
            "title": f"New Announcement: {announcement.title}",
            "message": announcement.content[:200],
            "data": {"announcement_id": ann_id},
            "is_read": False
        }).execute()


@router.put("/{announcement_id}")
async def update_announcement(
    announcement_id: UUID,
    update: AnnouncementUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update an announcement"""
    existing = supabase.table("announcements").select("author_id").eq(
        "id", str(announcement_id)
    ).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Announcement not found")

    update_data = {k: v for k, v in update.dict().items() if v is not None}
    if update.expires_at:
        update_data["expires_at"] = update.expires_at.isoformat()

    result = supabase.table("announcements").update(update_data).eq(
        "id", str(announcement_id)
    ).execute()

    return result.data[0] if result.data else None


@router.delete("/{announcement_id}")
async def delete_announcement(
    announcement_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete an announcement"""
    supabase.table("announcements").delete().eq("id", str(announcement_id)).execute()
    return {"success": True}


# ============================================================
# COMMENTS
# ============================================================

@router.post("/{announcement_id}/comments")
async def add_comment(
    announcement_id: UUID,
    content: str,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Add a comment to an announcement"""
    user_id = current_user.get("id")

    # Verify comments are enabled
    ann = supabase.table("announcements").select("allow_comments").eq(
        "id", str(announcement_id)
    ).single().execute()

    if not ann.data or not ann.data.get("allow_comments"):
        raise HTTPException(status_code=400, detail="Comments not allowed")

    result = supabase.table("announcement_comments").insert({
        "announcement_id": str(announcement_id),
        "author_id": user_id,
        "content": content
    }).execute()

    return result.data[0] if result.data else None


@router.delete("/{announcement_id}/comments/{comment_id}")
async def delete_comment(
    announcement_id: UUID,
    comment_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a comment"""
    user_id = current_user.get("id")
    user_role = current_user.get("role")

    comment = supabase.table("announcement_comments").select("author_id").eq(
        "id", str(comment_id)
    ).single().execute()

    if not comment.data:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Only author or admin can delete
    if comment.data["author_id"] != user_id and user_role not in ["principal", "office_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    supabase.table("announcement_comments").delete().eq("id", str(comment_id)).execute()
    return {"success": True}


# ============================================================
# ANALYTICS
# ============================================================

@router.get("/{announcement_id}/analytics")
async def get_announcement_analytics(
    announcement_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get announcement engagement analytics"""
    # Views
    views = supabase.table("announcement_views").select(
        "id", count="exact"
    ).eq("announcement_id", str(announcement_id)).execute()

    # Comments
    comments = supabase.table("announcement_comments").select(
        "id", count="exact"
    ).eq("announcement_id", str(announcement_id)).execute()

    # View timeline
    view_timeline = supabase.table("announcement_views").select(
        "viewed_at"
    ).eq("announcement_id", str(announcement_id)).order("viewed_at").execute()

    return {
        "total_views": views.count or 0,
        "total_comments": comments.count or 0,
        "view_timeline": [v["viewed_at"] for v in (view_timeline.data or [])]
    }


# ============================================================
# CATEGORIES
# ============================================================

@router.get("/categories/list")
async def get_announcement_categories():
    """Get available announcement categories"""
    return {
        "categories": [
            {"id": "general", "name": "General", "color": "#2196F3", "icon": "info"},
            {"id": "academic", "name": "Academic", "color": "#4CAF50", "icon": "school"},
            {"id": "event", "name": "Event", "color": "#9C27B0", "icon": "event"},
            {"id": "emergency", "name": "Emergency", "color": "#F44336", "icon": "warning"},
            {"id": "reminder", "name": "Reminder", "color": "#FF9800", "icon": "alarm"},
            {"id": "achievement", "name": "Achievement", "color": "#FFEB3B", "icon": "star"},
            {"id": "policy", "name": "Policy Update", "color": "#607D8B", "icon": "policy"}
        ]
    }


# ============================================================
# SCHEDULED ANNOUNCEMENTS
# ============================================================

@router.get("/scheduled")
async def get_scheduled_announcements(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get scheduled announcements"""
    school_id = current_user.get("school_id")

    result = supabase.table("announcements").select(
        "id, title, category, publish_at"
    ).eq("school_id", school_id).eq("status", "scheduled").order("publish_at").execute()

    return {"scheduled": result.data or []}


@router.post("/{announcement_id}/publish-now")
async def publish_now(
    announcement_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Publish a scheduled announcement immediately"""
    now = datetime.utcnow()

    supabase.table("announcements").update({
        "status": "published",
        "publish_at": now.isoformat()
    }).eq("id", str(announcement_id)).execute()

    return {"success": True, "published_at": now.isoformat()}
