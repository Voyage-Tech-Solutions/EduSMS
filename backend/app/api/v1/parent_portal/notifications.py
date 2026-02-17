"""
EduCore Backend - Parent Notification Preferences API
Manage notification settings and preferences
"""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import time, datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# MODELS
# ============================================================

class NotificationPreferencesUpdate(BaseModel):
    """Update notification preferences"""
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None

    # Category preferences
    grade_notifications: Optional[bool] = None
    attendance_notifications: Optional[bool] = None
    fee_notifications: Optional[bool] = None
    announcement_notifications: Optional[bool] = None
    assignment_notifications: Optional[bool] = None
    behavior_notifications: Optional[bool] = None
    event_notifications: Optional[bool] = None
    report_card_notifications: Optional[bool] = None

    # Timing preferences
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None  # HH:MM format
    quiet_hours_end: Optional[str] = None

    # Digest preferences
    daily_digest_enabled: Optional[bool] = None
    weekly_digest_enabled: Optional[bool] = None
    digest_time: Optional[str] = None  # HH:MM format

    # Language
    language_preference: Optional[str] = None


class NotificationChannelUpdate(BaseModel):
    """Update specific notification channel settings"""
    notification_type: str
    email: bool = True
    sms: bool = False
    push: bool = True


# ============================================================
# PREFERENCES ENDPOINTS
# ============================================================

@router.get("/preferences")
async def get_notification_preferences(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get notification preferences"""
    parent_id = current_user.get("id")

    result = supabase.table("parent_notification_preferences").select("*").eq(
        "parent_id", parent_id
    ).single().execute()

    if not result.data:
        # Return defaults
        return {
            "preferences": {
                "email_enabled": True,
                "sms_enabled": True,
                "push_enabled": True,
                "grade_notifications": True,
                "attendance_notifications": True,
                "fee_notifications": True,
                "announcement_notifications": True,
                "assignment_notifications": True,
                "behavior_notifications": True,
                "event_notifications": True,
                "report_card_notifications": True,
                "quiet_hours_enabled": False,
                "quiet_hours_start": None,
                "quiet_hours_end": None,
                "daily_digest_enabled": False,
                "weekly_digest_enabled": True,
                "digest_time": "18:00",
                "language_preference": "en"
            }
        }

    return {"preferences": result.data}


@router.put("/preferences")
async def update_notification_preferences(
    update: NotificationPreferencesUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update notification preferences"""
    parent_id = current_user.get("id")

    # Check if preferences exist
    existing = supabase.table("parent_notification_preferences").select("id").eq(
        "parent_id", parent_id
    ).single().execute()

    update_data = {k: v for k, v in update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow().isoformat()

    if existing.data:
        result = supabase.table("parent_notification_preferences").update(
            update_data
        ).eq("parent_id", parent_id).execute()
    else:
        update_data["parent_id"] = parent_id
        result = supabase.table("parent_notification_preferences").insert(
            update_data
        ).execute()

    return {"preferences": result.data[0] if result.data else None}


@router.get("/channels")
async def get_channel_preferences(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get per-notification-type channel preferences"""
    parent_id = current_user.get("id")

    result = supabase.table("parent_notification_channels").select("*").eq(
        "parent_id", parent_id
    ).execute()

    # Build response with defaults
    defaults = [
        {"type": "grade_posted", "name": "Grade Posted", "email": True, "sms": False, "push": True},
        {"type": "low_grade", "name": "Low Grade Alert", "email": True, "sms": True, "push": True},
        {"type": "attendance_absent", "name": "Absence Recorded", "email": True, "sms": True, "push": True},
        {"type": "attendance_late", "name": "Late Arrival", "email": False, "sms": False, "push": True},
        {"type": "fee_due", "name": "Fee Due Reminder", "email": True, "sms": True, "push": True},
        {"type": "fee_overdue", "name": "Fee Overdue", "email": True, "sms": True, "push": True},
        {"type": "payment_received", "name": "Payment Received", "email": True, "sms": False, "push": True},
        {"type": "announcement", "name": "School Announcement", "email": True, "sms": False, "push": True},
        {"type": "assignment_posted", "name": "New Assignment", "email": False, "sms": False, "push": True},
        {"type": "assignment_due", "name": "Assignment Due Soon", "email": True, "sms": False, "push": True},
        {"type": "behavior_incident", "name": "Behavior Report", "email": True, "sms": True, "push": True},
        {"type": "event_reminder", "name": "Event Reminder", "email": True, "sms": False, "push": True},
        {"type": "report_card", "name": "Report Card Ready", "email": True, "sms": True, "push": True},
        {"type": "conference_reminder", "name": "Conference Reminder", "email": True, "sms": True, "push": True}
    ]

    # Merge with saved preferences
    saved = {c["notification_type"]: c for c in (result.data or [])}

    channels = []
    for default in defaults:
        if default["type"] in saved:
            s = saved[default["type"]]
            channels.append({
                "type": default["type"],
                "name": default["name"],
                "email": s.get("email", default["email"]),
                "sms": s.get("sms", default["sms"]),
                "push": s.get("push", default["push"])
            })
        else:
            channels.append(default)

    return {"channels": channels}


@router.put("/channels/{notification_type}")
async def update_channel_preference(
    notification_type: str,
    update: NotificationChannelUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update channel preference for a notification type"""
    parent_id = current_user.get("id")

    existing = supabase.table("parent_notification_channels").select("id").eq(
        "parent_id", parent_id
    ).eq("notification_type", notification_type).single().execute()

    channel_data = {
        "email": update.email,
        "sms": update.sms,
        "push": update.push,
        "updated_at": datetime.utcnow().isoformat()
    }

    if existing.data:
        result = supabase.table("parent_notification_channels").update(
            channel_data
        ).eq("parent_id", parent_id).eq("notification_type", notification_type).execute()
    else:
        channel_data["parent_id"] = parent_id
        channel_data["notification_type"] = notification_type
        result = supabase.table("parent_notification_channels").insert(
            channel_data
        ).execute()

    return {"channel": result.data[0] if result.data else None}


# ============================================================
# NOTIFICATION HISTORY
# ============================================================

@router.get("/history")
async def get_notification_history(
    notification_type: Optional[str] = None,
    is_read: Optional[bool] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get notification history"""
    parent_id = current_user.get("id")

    query = supabase.table("notifications").select("*").eq("user_id", parent_id)

    if notification_type:
        query = query.eq("notification_type", notification_type)
    if is_read is not None:
        query = query.eq("is_read", is_read)

    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

    result = query.execute()

    # Get unread count
    unread = supabase.table("notifications").select(
        "id", count="exact"
    ).eq("user_id", parent_id).eq("is_read", False).execute()

    return {
        "notifications": result.data or [],
        "unread_count": unread.count or 0,
        "limit": limit,
        "offset": offset
    }


@router.post("/mark-read")
async def mark_notifications_read(
    notification_ids: List[UUID],
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Mark notifications as read"""
    parent_id = current_user.get("id")

    supabase.table("notifications").update({
        "is_read": True,
        "read_at": datetime.utcnow().isoformat()
    }).eq("user_id", parent_id).in_(
        "id", [str(nid) for nid in notification_ids]
    ).execute()

    return {"success": True, "marked_count": len(notification_ids)}


@router.post("/mark-all-read")
async def mark_all_notifications_read(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Mark all notifications as read"""
    parent_id = current_user.get("id")

    result = supabase.table("notifications").update({
        "is_read": True,
        "read_at": datetime.utcnow().isoformat()
    }).eq("user_id", parent_id).eq("is_read", False).execute()

    return {"success": True, "marked_count": len(result.data) if result.data else 0}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a notification"""
    parent_id = current_user.get("id")

    supabase.table("notifications").delete().eq(
        "id", str(notification_id)
    ).eq("user_id", parent_id).execute()

    return {"success": True}


# ============================================================
# CONTACT INFORMATION
# ============================================================

@router.get("/contact-info")
async def get_contact_info(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get parent's contact information for notifications"""
    parent_id = current_user.get("id")

    result = supabase.table("user_profiles").select(
        "email, phone_number"
    ).eq("id", parent_id).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="User profile not found")

    return {
        "email": result.data.get("email"),
        "phone": result.data.get("phone_number"),
        "email_verified": True,  # Would come from auth provider
        "phone_verified": False  # Would need SMS verification
    }


@router.put("/contact-info")
async def update_contact_info(
    email: Optional[str] = None,
    phone: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update contact information"""
    parent_id = current_user.get("id")

    update_data = {}
    if email is not None:
        update_data["email"] = email
    if phone is not None:
        update_data["phone_number"] = phone

    if update_data:
        supabase.table("user_profiles").update(update_data).eq(
            "id", parent_id
        ).execute()

    return {"success": True}


# ============================================================
# DEVICE TOKENS (FOR PUSH NOTIFICATIONS)
# ============================================================

@router.post("/devices/register")
async def register_device(
    device_token: str,
    device_type: str = "web",  # web, ios, android
    device_name: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Register a device for push notifications"""
    parent_id = current_user.get("id")

    # Check if token already exists
    existing = supabase.table("push_device_tokens").select("id").eq(
        "token", device_token
    ).single().execute()

    if existing.data:
        # Update existing
        supabase.table("push_device_tokens").update({
            "user_id": parent_id,
            "device_type": device_type,
            "device_name": device_name,
            "is_active": True,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", existing.data["id"]).execute()
    else:
        # Create new
        supabase.table("push_device_tokens").insert({
            "user_id": parent_id,
            "token": device_token,
            "device_type": device_type,
            "device_name": device_name,
            "is_active": True
        }).execute()

    return {"success": True}


@router.delete("/devices/{device_token}")
async def unregister_device(
    device_token: str,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Unregister a device from push notifications"""
    parent_id = current_user.get("id")

    supabase.table("push_device_tokens").update({
        "is_active": False
    }).eq("token", device_token).eq("user_id", parent_id).execute()

    return {"success": True}
