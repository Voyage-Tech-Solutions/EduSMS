"""
EduCore Backend - Notification Service API
Unified notification delivery (push, email, SMS)
"""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


class NotificationChannel(str, Enum):
    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"


class NotificationType(str, Enum):
    GRADE = "grade"
    ATTENDANCE = "attendance"
    FEE = "fee"
    ANNOUNCEMENT = "announcement"
    MESSAGE = "message"
    REMINDER = "reminder"
    ALERT = "alert"
    SYSTEM = "system"


class SendNotificationRequest(BaseModel):
    """Send notification request"""
    user_ids: List[UUID]
    notification_type: NotificationType
    title: str
    message: str
    data: Optional[dict] = None
    channels: List[NotificationChannel] = [NotificationChannel.IN_APP, NotificationChannel.PUSH]
    priority: str = "normal"  # low, normal, high, urgent


class BulkNotificationRequest(BaseModel):
    """Bulk notification request"""
    target: str  # all, role, grade, class
    target_ids: List[UUID] = []
    notification_type: NotificationType
    title: str
    message: str
    channels: List[NotificationChannel] = [NotificationChannel.IN_APP]


# ============================================================
# SEND NOTIFICATIONS
# ============================================================

@router.post("/send")
async def send_notification(
    request: SendNotificationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Send notification to specific users"""
    school_id = current_user.get("school_id")

    # Queue notification delivery
    background_tasks.add_task(
        _deliver_notifications,
        request.user_ids,
        request,
        school_id,
        supabase
    )

    return {
        "status": "queued",
        "recipients": len(request.user_ids),
        "channels": [c.value for c in request.channels]
    }


@router.post("/send-bulk")
async def send_bulk_notification(
    request: BulkNotificationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Send bulk notifications based on target"""
    school_id = current_user.get("school_id")
    user_role = current_user.get("role")

    if user_role not in ["principal", "office_admin", "system_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Get target users
    user_ids = await _get_target_users(request.target, request.target_ids, school_id, supabase)

    # Queue delivery
    notification_request = SendNotificationRequest(
        user_ids=user_ids,
        notification_type=request.notification_type,
        title=request.title,
        message=request.message,
        channels=request.channels
    )

    background_tasks.add_task(
        _deliver_notifications,
        user_ids,
        notification_request,
        school_id,
        supabase
    )

    return {
        "status": "queued",
        "recipients": len(user_ids),
        "target": request.target
    }


async def _get_target_users(target, target_ids, school_id, supabase):
    """Get user IDs based on target criteria"""
    user_ids = []

    if target == "all":
        users = supabase.table("user_profiles").select("id").eq(
            "school_id", school_id
        ).execute()
        user_ids = [u["id"] for u in (users.data or [])]

    elif target == "role":
        for role in target_ids:
            users = supabase.table("user_profiles").select("id").eq(
                "school_id", school_id
            ).eq("role", str(role)).execute()
            user_ids.extend([u["id"] for u in (users.data or [])])

    elif target == "grade":
        # Get students in grades, then their parents
        students = supabase.table("students").select("id").eq(
            "school_id", school_id
        ).in_("grade_id", [str(g) for g in target_ids]).execute()

        student_ids = [s["id"] for s in (students.data or [])]

        # Get parent IDs
        relations = supabase.table("parent_student_relations").select(
            "parent_id"
        ).in_("student_id", student_ids).execute()

        user_ids = list(set(r["parent_id"] for r in (relations.data or [])))

    elif target == "class":
        students = supabase.table("students").select("id").eq(
            "school_id", school_id
        ).in_("class_id", [str(c) for c in target_ids]).execute()

        student_ids = [s["id"] for s in (students.data or [])]

        relations = supabase.table("parent_student_relations").select(
            "parent_id"
        ).in_("student_id", student_ids).execute()

        user_ids = list(set(r["parent_id"] for r in (relations.data or [])))

    return [UUID(uid) if isinstance(uid, str) else uid for uid in user_ids]


async def _deliver_notifications(user_ids, request, school_id, supabase):
    """Background task to deliver notifications"""
    for user_id in user_ids:
        try:
            # Create in-app notification
            if NotificationChannel.IN_APP in request.channels:
                supabase.table("notifications").insert({
                    "school_id": school_id,
                    "user_id": str(user_id),
                    "notification_type": request.notification_type.value,
                    "title": request.title,
                    "message": request.message,
                    "data": request.data,
                    "is_read": False
                }).execute()

            # Send push notification
            if NotificationChannel.PUSH in request.channels:
                await _send_push_notification(user_id, request, supabase)

            # Send email
            if NotificationChannel.EMAIL in request.channels:
                await _send_email_notification(user_id, request, supabase)

            # Send SMS
            if NotificationChannel.SMS in request.channels:
                await _send_sms_notification(user_id, request, supabase)

        except Exception as e:
            logger.error(f"Failed to send notification to {user_id}: {e}")


async def _send_push_notification(user_id, request, supabase):
    """Send push notification"""
    # Get device tokens
    tokens = supabase.table("push_device_tokens").select("token, device_type").eq(
        "user_id", str(user_id)
    ).eq("is_active", True).execute()

    for token_data in (tokens.data or []):
        # In production, send to FCM/APNS
        logger.info(f"Push to {token_data['device_type']}: {request.title}")


async def _send_email_notification(user_id, request, supabase):
    """Send email notification"""
    # Get user email
    user = supabase.table("user_profiles").select("email, first_name").eq(
        "id", str(user_id)
    ).single().execute()

    if user.data and user.data.get("email"):
        # In production, send via SendGrid/SES
        logger.info(f"Email to {user.data['email']}: {request.title}")


async def _send_sms_notification(user_id, request, supabase):
    """Send SMS notification"""
    # Get user phone
    user = supabase.table("user_profiles").select("phone_number").eq(
        "id", str(user_id)
    ).single().execute()

    if user.data and user.data.get("phone_number"):
        # In production, send via Twilio
        logger.info(f"SMS to {user.data['phone_number']}: {request.title}")


# ============================================================
# NOTIFICATION HISTORY
# ============================================================

@router.get("/sent")
async def get_sent_notifications(
    notification_type: Optional[NotificationType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get sent notification history (admin only)"""
    school_id = current_user.get("school_id")
    user_role = current_user.get("role")

    if user_role not in ["principal", "office_admin", "system_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    query = supabase.table("notification_log").select("*").eq("school_id", school_id)

    if notification_type:
        query = query.eq("notification_type", notification_type.value)
    if start_date:
        query = query.gte("created_at", start_date.isoformat())
    if end_date:
        query = query.lte("created_at", end_date.isoformat())

    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

    result = query.execute()

    return {"notifications": result.data or []}


@router.get("/delivery-stats")
async def get_delivery_stats(
    days: int = 7,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get notification delivery statistics"""
    school_id = current_user.get("school_id")

    # In production, would query delivery stats
    return {
        "period_days": days,
        "total_sent": 1250,
        "by_channel": {
            "in_app": {"sent": 1250, "delivered": 1250},
            "push": {"sent": 980, "delivered": 945},
            "email": {"sent": 450, "delivered": 442},
            "sms": {"sent": 120, "delivered": 118}
        },
        "by_type": {
            "grade": 320,
            "attendance": 280,
            "fee": 150,
            "announcement": 200,
            "message": 180,
            "reminder": 120
        }
    }


# ============================================================
# NOTIFICATION TEMPLATES
# ============================================================

@router.get("/defaults")
async def get_notification_defaults():
    """Get default notification configurations"""
    return {
        "defaults": [
            {
                "type": "grade_posted",
                "title": "New Grade Posted",
                "message_template": "{{student_name}} received a grade of {{score}} in {{subject}}",
                "channels": ["in_app", "push"],
                "can_disable": True
            },
            {
                "type": "attendance_absent",
                "title": "Absence Recorded",
                "message_template": "{{student_name}} was marked absent on {{date}}",
                "channels": ["in_app", "push", "sms"],
                "can_disable": False
            },
            {
                "type": "fee_due",
                "title": "Fee Payment Reminder",
                "message_template": "Fee payment of {{amount}} is due on {{due_date}}",
                "channels": ["in_app", "email"],
                "can_disable": True
            },
            {
                "type": "fee_overdue",
                "title": "Overdue Fee Notice",
                "message_template": "Fee payment of {{amount}} is overdue since {{due_date}}",
                "channels": ["in_app", "email", "sms"],
                "can_disable": False
            },
            {
                "type": "announcement",
                "title": "New Announcement",
                "message_template": "{{announcement_title}}",
                "channels": ["in_app", "push"],
                "can_disable": True
            },
            {
                "type": "message_received",
                "title": "New Message",
                "message_template": "You have a new message from {{sender_name}}",
                "channels": ["in_app", "push"],
                "can_disable": True
            },
            {
                "type": "event_reminder",
                "title": "Event Reminder",
                "message_template": "{{event_name}} is scheduled for {{event_date}}",
                "channels": ["in_app", "push"],
                "can_disable": True
            }
        ]
    }


# ============================================================
# TRIGGER NOTIFICATIONS
# ============================================================

@router.post("/trigger/grade-posted")
async def trigger_grade_notification(
    student_id: UUID,
    subject_name: str,
    score: float,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Trigger notification when grade is posted"""
    school_id = current_user.get("school_id")

    # Get student info
    student = supabase.table("students").select("first_name, last_name").eq(
        "id", str(student_id)
    ).single().execute()

    student_name = f"{student.data['first_name']} {student.data['last_name']}" if student.data else "Student"

    # Get parents
    relations = supabase.table("parent_student_relations").select(
        "parent_id"
    ).eq("student_id", str(student_id)).execute()

    parent_ids = [UUID(r["parent_id"]) for r in (relations.data or [])]

    if parent_ids:
        request = SendNotificationRequest(
            user_ids=parent_ids,
            notification_type=NotificationType.GRADE,
            title="New Grade Posted",
            message=f"{student_name} received a grade of {score} in {subject_name}",
            data={"student_id": str(student_id), "score": score, "subject": subject_name},
            channels=[NotificationChannel.IN_APP, NotificationChannel.PUSH]
        )

        background_tasks.add_task(
            _deliver_notifications,
            parent_ids,
            request,
            school_id,
            supabase
        )

    return {"status": "triggered", "parents_notified": len(parent_ids)}


@router.post("/trigger/attendance-alert")
async def trigger_attendance_notification(
    student_id: UUID,
    status: str,
    date: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Trigger notification for attendance alert"""
    school_id = current_user.get("school_id")

    # Get student info
    student = supabase.table("students").select("first_name, last_name").eq(
        "id", str(student_id)
    ).single().execute()

    student_name = f"{student.data['first_name']} {student.data['last_name']}" if student.data else "Student"

    # Get parents
    relations = supabase.table("parent_student_relations").select(
        "parent_id"
    ).eq("student_id", str(student_id)).execute()

    parent_ids = [UUID(r["parent_id"]) for r in (relations.data or [])]

    if parent_ids:
        channels = [NotificationChannel.IN_APP, NotificationChannel.PUSH]
        if status in ["absent", "unexcused"]:
            channels.append(NotificationChannel.SMS)

        request = SendNotificationRequest(
            user_ids=parent_ids,
            notification_type=NotificationType.ATTENDANCE,
            title="Attendance Alert",
            message=f"{student_name} was marked {status} on {date}",
            data={"student_id": str(student_id), "status": status, "date": date},
            channels=channels
        )

        background_tasks.add_task(
            _deliver_notifications,
            parent_ids,
            request,
            school_id,
            supabase
        )

    return {"status": "triggered", "parents_notified": len(parent_ids)}
