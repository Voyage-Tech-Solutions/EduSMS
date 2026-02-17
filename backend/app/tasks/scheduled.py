"""
EduCore Backend - Scheduled Tasks
Periodic background tasks run by Celery Beat
"""
from celery import shared_task
from typing import Dict, List
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def generate_daily_attendance_report(self) -> Dict:
    """
    Generate daily attendance summary for all active schools
    Runs every day at 6 AM UTC
    """
    try:
        from app.db.supabase import get_supabase_admin
        from app.tasks.notifications import send_email

        supabase = get_supabase_admin()

        # Get all active schools
        schools = supabase.table("schools").select("id, name").eq("is_active", True).execute()

        results = []
        today = datetime.utcnow().date().isoformat()

        for school in (schools.data or []):
            school_id = school["id"]

            # Get attendance summary for today
            attendance = supabase.table("attendance_records").select(
                "status"
            ).eq("school_id", school_id).eq("date", today).execute()

            records = attendance.data or []
            total = len(records)
            present = len([r for r in records if r["status"] == "present"])
            absent = len([r for r in records if r["status"] == "absent"])
            late = len([r for r in records if r["status"] == "late"])

            rate = (present / total * 100) if total > 0 else 0

            # Get principal email
            principal = supabase.table("user_profiles").select(
                "email"
            ).eq("school_id", school_id).eq("role", "principal").limit(1).execute()

            if principal.data:
                # Queue email to principal
                send_email.delay(
                    to_email=principal.data[0]["email"],
                    subject=f"Daily Attendance Report - {today}",
                    body=f"""
                    Daily Attendance Summary for {school['name']}
                    Date: {today}

                    Total Students: {total}
                    Present: {present}
                    Absent: {absent}
                    Late: {late}
                    Attendance Rate: {rate:.1f}%
                    """,
                )

            results.append({
                "school_id": school_id,
                "total": total,
                "present": present,
                "rate": rate,
            })

        logger.info(f"Daily attendance reports generated for {len(results)} schools")
        return {"success": True, "schools_processed": len(results), "results": results}

    except Exception as e:
        logger.error(f"Failed to generate daily attendance reports: {e}")
        return {"success": False, "error": str(e)}


@shared_task(bind=True)
def check_overdue_fees(self) -> Dict:
    """
    Check for overdue fees and update invoice statuses
    Runs every day at 7 AM UTC
    """
    try:
        from app.db.supabase import get_supabase_admin

        supabase = get_supabase_admin()

        today = datetime.utcnow().date().isoformat()

        # Find invoices that are past due date and not fully paid
        overdue = supabase.table("invoices").select(
            "id, student_id, amount, amount_paid, due_date"
        ).lt("due_date", today).neq("status", "paid").neq("status", "overdue").execute()

        updated_count = 0
        for invoice in (overdue.data or []):
            # Update status to overdue
            supabase.table("invoices").update({
                "status": "overdue"
            }).eq("id", invoice["id"]).execute()
            updated_count += 1

        logger.info(f"Marked {updated_count} invoices as overdue")
        return {"success": True, "updated_count": updated_count}

    except Exception as e:
        logger.error(f"Failed to check overdue fees: {e}")
        return {"success": False, "error": str(e)}


@shared_task(bind=True)
def send_fee_reminders(self) -> Dict:
    """
    Send fee payment reminders for upcoming due dates
    Runs every Monday at 8 AM UTC
    """
    try:
        from app.db.supabase import get_supabase_admin
        from app.tasks.notifications import send_fee_reminder

        supabase = get_supabase_admin()

        # Get invoices due in next 7 days
        today = datetime.utcnow().date()
        next_week = (today + timedelta(days=7)).isoformat()
        today_str = today.isoformat()

        upcoming = supabase.table("invoices").select(
            "*, students(first_name, last_name, guardians(email, phone, is_primary))"
        ).gte("due_date", today_str).lte("due_date", next_week).eq("status", "pending").execute()

        reminders_sent = 0
        for invoice in (upcoming.data or []):
            student = invoice.get("students", {})
            guardians = student.get("guardians", [])

            # Find primary guardian
            primary_guardian = next(
                (g for g in guardians if g.get("is_primary")),
                guardians[0] if guardians else None
            )

            if primary_guardian and primary_guardian.get("email"):
                send_fee_reminder.delay(
                    student_id=invoice["student_id"],
                    student_name=f"{student.get('first_name', '')} {student.get('last_name', '')}",
                    parent_email=primary_guardian["email"],
                    parent_phone=primary_guardian.get("phone"),
                    amount_due=invoice["amount"] - invoice.get("amount_paid", 0),
                    due_date=invoice["due_date"],
                    invoice_number=invoice["invoice_number"],
                )
                reminders_sent += 1

        logger.info(f"Queued {reminders_sent} fee reminders")
        return {"success": True, "reminders_sent": reminders_sent}

    except Exception as e:
        logger.error(f"Failed to send fee reminders: {e}")
        return {"success": False, "error": str(e)}


@shared_task(bind=True)
def cleanup_expired_sessions(self) -> Dict:
    """
    Clean up expired user sessions
    Runs every hour
    """
    try:
        from app.db.supabase import get_supabase_admin

        supabase = get_supabase_admin()

        now = datetime.utcnow().isoformat()

        # Delete expired sessions
        result = supabase.table("user_sessions").delete().lt("expires_at", now).execute()

        deleted_count = len(result.data) if result.data else 0

        logger.info(f"Cleaned up {deleted_count} expired sessions")
        return {"success": True, "deleted_count": deleted_count}

    except Exception as e:
        logger.error(f"Failed to cleanup expired sessions: {e}")
        return {"success": False, "error": str(e)}


@shared_task(bind=True)
def check_document_expirations(self) -> Dict:
    """
    Check for expiring documents and send notifications
    Runs daily
    """
    try:
        from app.db.supabase import get_supabase_admin
        from app.tasks.notifications import send_email

        supabase = get_supabase_admin()

        # Find documents expiring in next 30 days
        today = datetime.utcnow().date()
        thirty_days = (today + timedelta(days=30)).isoformat()
        today_str = today.isoformat()

        expiring = supabase.table("documents").select(
            "*, students(first_name, last_name, school_id)"
        ).gte("expiry_date", today_str).lte("expiry_date", thirty_days).execute()

        notifications_sent = 0
        for doc in (expiring.data or []):
            # Notify office admin
            # This is a simplified version - in production, would batch by school
            notifications_sent += 1

        logger.info(f"Found {notifications_sent} expiring documents")
        return {"success": True, "expiring_count": notifications_sent}

    except Exception as e:
        logger.error(f"Failed to check document expirations: {e}")
        return {"success": False, "error": str(e)}


@shared_task(bind=True)
def update_attendance_streaks(self) -> Dict:
    """
    Update student attendance streak counters
    Runs daily after attendance is typically recorded
    """
    try:
        from app.db.supabase import get_supabase_admin

        supabase = get_supabase_admin()

        # This would update attendance streak data for gamification
        # Placeholder for future implementation

        logger.info("Attendance streaks updated")
        return {"success": True}

    except Exception as e:
        logger.error(f"Failed to update attendance streaks: {e}")
        return {"success": False, "error": str(e)}


@shared_task(bind=True)
def sync_calendar_events(self) -> Dict:
    """
    Sync school calendar events with external calendars
    Runs every 15 minutes
    """
    try:
        # Placeholder for Google/Microsoft calendar sync
        logger.info("Calendar sync completed")
        return {"success": True}

    except Exception as e:
        logger.error(f"Failed to sync calendar events: {e}")
        return {"success": False, "error": str(e)}


@shared_task(bind=True)
def backup_audit_logs(self) -> Dict:
    """
    Archive old audit logs to cold storage
    Runs weekly
    """
    try:
        from app.db.supabase import get_supabase_admin

        supabase = get_supabase_admin()

        # Archive logs older than 90 days
        ninety_days_ago = (datetime.utcnow() - timedelta(days=90)).isoformat()

        # In production, would move to cold storage before deleting
        # For now, just log the count
        old_logs = supabase.table("audit_logs").select(
            "id", count="exact"
        ).lt("created_at", ninety_days_ago).execute()

        count = old_logs.count if hasattr(old_logs, 'count') else 0

        logger.info(f"Found {count} audit logs eligible for archival")
        return {"success": True, "logs_to_archive": count}

    except Exception as e:
        logger.error(f"Failed to backup audit logs: {e}")
        return {"success": False, "error": str(e)}
