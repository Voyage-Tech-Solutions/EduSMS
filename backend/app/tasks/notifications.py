"""
EduCore Backend - Notification Tasks
Background tasks for sending emails, SMS, and push notifications
"""
from celery import shared_task
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email(
    self,
    to_email: str,
    subject: str,
    body: str,
    template_id: Optional[str] = None,
    template_data: Optional[Dict] = None,
    attachments: Optional[List[Dict]] = None,
) -> Dict:
    """
    Send an email notification

    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body (HTML or plain text)
        template_id: Optional SendGrid template ID
        template_data: Optional template substitution data
        attachments: Optional list of attachments [{filename, content, type}]
    """
    try:
        from app.integrations.communications.sendgrid_provider import send_email as sg_send

        result = sg_send(
            to_email=to_email,
            subject=subject,
            body=body,
            template_id=template_id,
            template_data=template_data,
            attachments=attachments,
        )

        logger.info(f"Email sent successfully to {to_email}")
        return {"success": True, "message_id": result.get("message_id")}

    except ImportError:
        # SendGrid not configured, log and continue
        logger.warning(f"SendGrid not configured. Would send email to {to_email}: {subject}")
        return {"success": True, "message": "Email queued (SendGrid not configured)"}

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_sms(
    self,
    to_phone: str,
    message: str,
    school_id: Optional[str] = None,
) -> Dict:
    """
    Send an SMS notification

    Args:
        to_phone: Recipient phone number (E.164 format)
        message: SMS message content
        school_id: Optional school ID for tracking
    """
    try:
        from app.integrations.communications.twilio_provider import send_sms as tw_send

        result = tw_send(to_phone=to_phone, message=message)

        logger.info(f"SMS sent successfully to {to_phone}")
        return {"success": True, "message_sid": result.get("sid")}

    except ImportError:
        logger.warning(f"Twilio not configured. Would send SMS to {to_phone}: {message[:50]}...")
        return {"success": True, "message": "SMS queued (Twilio not configured)"}

    except Exception as e:
        logger.error(f"Failed to send SMS to {to_phone}: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_whatsapp(
    self,
    to_phone: str,
    message: str,
    template_name: Optional[str] = None,
    template_params: Optional[List[str]] = None,
) -> Dict:
    """
    Send a WhatsApp message

    Args:
        to_phone: Recipient phone number (E.164 format)
        message: Message content (for non-template messages)
        template_name: Optional approved template name
        template_params: Optional template parameters
    """
    try:
        from app.integrations.communications.whatsapp_provider import send_whatsapp as wa_send

        result = wa_send(
            to_phone=to_phone,
            message=message,
            template_name=template_name,
            template_params=template_params,
        )

        logger.info(f"WhatsApp message sent successfully to {to_phone}")
        return {"success": True, "message_sid": result.get("sid")}

    except ImportError:
        logger.warning(f"WhatsApp not configured. Would send to {to_phone}")
        return {"success": True, "message": "WhatsApp queued (not configured)"}

    except Exception as e:
        logger.error(f"Failed to send WhatsApp to {to_phone}: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_push_notification(
    self,
    user_id: str,
    title: str,
    body: str,
    data: Optional[Dict] = None,
    action_url: Optional[str] = None,
) -> Dict:
    """
    Send a push notification to a user's devices

    Args:
        user_id: Target user ID
        title: Notification title
        body: Notification body
        data: Optional additional data payload
        action_url: Optional URL to open on click
    """
    try:
        from app.integrations.push.fcm import send_push as fcm_send

        result = fcm_send(
            user_id=user_id,
            title=title,
            body=body,
            data=data,
            action_url=action_url,
        )

        logger.info(f"Push notification sent to user {user_id}")
        return {"success": True, "sent_count": result.get("sent_count", 0)}

    except ImportError:
        logger.warning(f"FCM not configured. Would send push to user {user_id}")
        return {"success": True, "message": "Push queued (FCM not configured)"}

    except Exception as e:
        logger.error(f"Failed to send push notification to user {user_id}: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True)
def send_bulk_notifications(
    self,
    recipients: List[Dict],
    notification_type: str,
    subject: str,
    message: str,
    template_id: Optional[str] = None,
    template_data: Optional[Dict] = None,
) -> Dict:
    """
    Send bulk notifications to multiple recipients

    Args:
        recipients: List of {email, phone, user_id, preferences}
        notification_type: Type of notification (announcement, reminder, alert)
        subject: Notification subject
        message: Notification message
        template_id: Optional template ID
        template_data: Optional template data
    """
    results = {"email": 0, "sms": 0, "push": 0, "failed": 0}

    for recipient in recipients:
        prefs = recipient.get("preferences", {})

        try:
            # Send email if enabled
            if prefs.get("email_enabled", True) and recipient.get("email"):
                send_email.delay(
                    to_email=recipient["email"],
                    subject=subject,
                    body=message,
                    template_id=template_id,
                    template_data=template_data,
                )
                results["email"] += 1

            # Send SMS if enabled
            if prefs.get("sms_enabled", False) and recipient.get("phone"):
                send_sms.delay(to_phone=recipient["phone"], message=message)
                results["sms"] += 1

            # Send push if enabled
            if prefs.get("push_enabled", True) and recipient.get("user_id"):
                send_push_notification.delay(
                    user_id=recipient["user_id"],
                    title=subject,
                    body=message[:200],
                )
                results["push"] += 1

        except Exception as e:
            logger.error(f"Failed to queue notification for {recipient}: {e}")
            results["failed"] += 1

    logger.info(f"Bulk notification queued: {results}")
    return results


@shared_task(bind=True)
def send_attendance_alert(
    self,
    student_id: str,
    student_name: str,
    parent_email: str,
    parent_phone: Optional[str],
    status: str,
    date: str,
) -> Dict:
    """Send attendance alert to parent"""
    subject = f"Attendance Alert: {student_name}"
    message = f"Your child {student_name} was marked {status} on {date}."

    # Send email
    send_email.delay(to_email=parent_email, subject=subject, body=message)

    # Send SMS if phone available
    if parent_phone:
        send_sms.delay(to_phone=parent_phone, message=message)

    return {"success": True, "student_id": student_id}


@shared_task(bind=True)
def send_grade_notification(
    self,
    student_id: str,
    student_name: str,
    parent_email: str,
    subject_name: str,
    assessment_title: str,
    score: float,
    max_score: float,
) -> Dict:
    """Send grade notification to parent"""
    percentage = (score / max_score * 100) if max_score > 0 else 0

    email_subject = f"New Grade Posted: {assessment_title}"
    message = f"{student_name} received {score}/{max_score} ({percentage:.1f}%) on {assessment_title} in {subject_name}."

    send_email.delay(to_email=parent_email, subject=email_subject, body=message)

    return {"success": True, "student_id": student_id, "percentage": percentage}


@shared_task(bind=True)
def send_fee_reminder(
    self,
    student_id: str,
    student_name: str,
    parent_email: str,
    parent_phone: Optional[str],
    amount_due: float,
    due_date: str,
    invoice_number: str,
) -> Dict:
    """Send fee reminder to parent"""
    subject = f"Fee Payment Reminder - {student_name}"
    message = (
        f"This is a reminder that a fee payment of ${amount_due:.2f} is due on {due_date}. "
        f"Invoice: {invoice_number}. Please log in to your parent portal to make a payment."
    )

    send_email.delay(to_email=parent_email, subject=subject, body=message)

    if parent_phone:
        sms_message = f"EduSMS: Fee reminder for {student_name}. ${amount_due:.2f} due by {due_date}."
        send_sms.delay(to_phone=parent_phone, message=sms_message)

    return {"success": True, "student_id": student_id, "amount": amount_due}
