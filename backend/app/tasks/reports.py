"""
EduCore Backend - Report Generation Tasks
Background tasks for generating PDF/Excel reports
"""
from celery import shared_task
from typing import Dict, Optional, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def generate_report_card(
    self,
    student_id: str,
    term_id: str,
    school_id: str,
    format: str = "pdf",
) -> Dict:
    """
    Generate student report card

    Args:
        student_id: Student UUID
        term_id: Academic term UUID
        school_id: School UUID
        format: Output format (pdf, html)
    """
    try:
        from app.db.supabase import get_supabase_admin

        supabase = get_supabase_admin()

        # Fetch student data
        student = supabase.table("students").select(
            "*, grades(name), classes(name)"
        ).eq("id", student_id).single().execute()

        if not student.data:
            return {"success": False, "error": "Student not found"}

        # Fetch assessment scores for the term
        scores = supabase.table("assessment_scores").select(
            "*, assessments(title, subject_id, total_marks, type)"
        ).eq("student_id", student_id).execute()

        # Fetch attendance summary
        attendance = supabase.table("attendance_records").select(
            "status"
        ).eq("student_id", student_id).execute()

        # Calculate statistics
        attendance_data = attendance.data or []
        total_days = len(attendance_data)
        present_days = len([a for a in attendance_data if a["status"] == "present"])
        attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0

        # Build report data
        report_data = {
            "student": student.data,
            "scores": scores.data or [],
            "attendance": {
                "total_days": total_days,
                "present_days": present_days,
                "attendance_rate": round(attendance_rate, 1),
            },
            "generated_at": datetime.utcnow().isoformat(),
        }

        # Generate PDF (placeholder - would use a PDF library)
        file_url = f"/reports/report-cards/{student_id}-{term_id}.pdf"

        # Store report record
        supabase.table("generated_reports").insert({
            "school_id": school_id,
            "report_type": "report_card",
            "entity_type": "student",
            "entity_id": student_id,
            "file_url": file_url,
            "parameters": {"term_id": term_id},
            "generated_at": datetime.utcnow().isoformat(),
        }).execute()

        logger.info(f"Report card generated for student {student_id}")
        return {"success": True, "file_url": file_url, "data": report_data}

    except Exception as e:
        logger.error(f"Failed to generate report card for student {student_id}: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def generate_class_report(
    self,
    class_id: str,
    school_id: str,
    report_type: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    format: str = "pdf",
) -> Dict:
    """
    Generate class-level report (attendance, grades, etc.)

    Args:
        class_id: Class UUID
        school_id: School UUID
        report_type: Type of report (attendance, grades, performance)
        date_from: Start date filter
        date_to: End date filter
        format: Output format
    """
    try:
        from app.db.supabase import get_supabase_admin

        supabase = get_supabase_admin()

        # Fetch class info
        class_info = supabase.table("classes").select(
            "*, grades(name)"
        ).eq("id", class_id).single().execute()

        if not class_info.data:
            return {"success": False, "error": "Class not found"}

        # Fetch students in class
        students = supabase.table("students").select(
            "id, first_name, last_name, admission_number"
        ).eq("class_id", class_id).execute()

        report_data = {
            "class": class_info.data,
            "students": students.data or [],
            "report_type": report_type,
            "date_range": {"from": date_from, "to": date_to},
            "generated_at": datetime.utcnow().isoformat(),
        }

        file_url = f"/reports/class/{class_id}-{report_type}-{datetime.utcnow().strftime('%Y%m%d')}.pdf"

        logger.info(f"Class report generated for class {class_id}, type: {report_type}")
        return {"success": True, "file_url": file_url, "data": report_data}

    except Exception as e:
        logger.error(f"Failed to generate class report for {class_id}: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def generate_financial_report(
    self,
    school_id: str,
    report_type: str,
    date_from: str,
    date_to: str,
    format: str = "excel",
) -> Dict:
    """
    Generate financial report

    Args:
        school_id: School UUID
        report_type: Type (collection, outstanding, arrears, summary)
        date_from: Start date
        date_to: End date
        format: Output format (excel, pdf, csv)
    """
    try:
        from app.db.supabase import get_supabase_admin

        supabase = get_supabase_admin()

        # Fetch financial data
        invoices = supabase.table("invoices").select(
            "*, students(first_name, last_name, admission_number)"
        ).eq("school_id", school_id).gte(
            "created_at", date_from
        ).lte("created_at", date_to).execute()

        payments = supabase.table("payments").select(
            "*"
        ).eq("school_id", school_id).gte(
            "payment_date", date_from
        ).lte("payment_date", date_to).execute()

        # Calculate summaries
        invoice_data = invoices.data or []
        payment_data = payments.data or []

        total_invoiced = sum(inv.get("amount", 0) for inv in invoice_data)
        total_collected = sum(pay.get("amount", 0) for pay in payment_data)
        total_outstanding = total_invoiced - total_collected
        collection_rate = (total_collected / total_invoiced * 100) if total_invoiced > 0 else 0

        report_data = {
            "school_id": school_id,
            "report_type": report_type,
            "period": {"from": date_from, "to": date_to},
            "summary": {
                "total_invoiced": total_invoiced,
                "total_collected": total_collected,
                "total_outstanding": total_outstanding,
                "collection_rate": round(collection_rate, 1),
                "invoice_count": len(invoice_data),
                "payment_count": len(payment_data),
            },
            "invoices": invoice_data,
            "payments": payment_data,
            "generated_at": datetime.utcnow().isoformat(),
        }

        file_url = f"/reports/financial/{school_id}-{report_type}-{datetime.utcnow().strftime('%Y%m%d')}.xlsx"

        logger.info(f"Financial report generated for school {school_id}, type: {report_type}")
        return {"success": True, "file_url": file_url, "data": report_data}

    except Exception as e:
        logger.error(f"Failed to generate financial report for {school_id}: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def generate_attendance_report(
    self,
    school_id: str,
    date_from: str,
    date_to: str,
    class_id: Optional[str] = None,
    grade_id: Optional[str] = None,
    format: str = "excel",
) -> Dict:
    """
    Generate attendance report

    Args:
        school_id: School UUID
        date_from: Start date
        date_to: End date
        class_id: Optional class filter
        grade_id: Optional grade filter
        format: Output format
    """
    try:
        from app.db.supabase import get_supabase_admin

        supabase = get_supabase_admin()

        # Build query
        query = supabase.table("attendance_records").select(
            "*, students(first_name, last_name, admission_number, classes(name), grades(name))"
        ).eq("school_id", school_id).gte("date", date_from).lte("date", date_to)

        if class_id:
            query = query.eq("students.class_id", class_id)

        records = query.execute()
        record_data = records.data or []

        # Calculate statistics
        total_records = len(record_data)
        present_count = len([r for r in record_data if r["status"] == "present"])
        absent_count = len([r for r in record_data if r["status"] == "absent"])
        late_count = len([r for r in record_data if r["status"] == "late"])

        report_data = {
            "school_id": school_id,
            "period": {"from": date_from, "to": date_to},
            "filters": {"class_id": class_id, "grade_id": grade_id},
            "summary": {
                "total_records": total_records,
                "present": present_count,
                "absent": absent_count,
                "late": late_count,
                "attendance_rate": round((present_count / total_records * 100), 1) if total_records > 0 else 0,
            },
            "records": record_data,
            "generated_at": datetime.utcnow().isoformat(),
        }

        file_url = f"/reports/attendance/{school_id}-{datetime.utcnow().strftime('%Y%m%d')}.xlsx"

        logger.info(f"Attendance report generated for school {school_id}")
        return {"success": True, "file_url": file_url, "data": report_data}

    except Exception as e:
        logger.error(f"Failed to generate attendance report for {school_id}: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True)
def generate_bulk_report_cards(
    self,
    school_id: str,
    term_id: str,
    class_ids: Optional[List[str]] = None,
    grade_ids: Optional[List[str]] = None,
) -> Dict:
    """
    Generate report cards for multiple students

    Args:
        school_id: School UUID
        term_id: Term UUID
        class_ids: Optional list of class IDs to include
        grade_ids: Optional list of grade IDs to include
    """
    try:
        from app.db.supabase import get_supabase_admin

        supabase = get_supabase_admin()

        # Fetch students based on filters
        query = supabase.table("students").select("id").eq("school_id", school_id).eq("status", "active")

        if class_ids:
            query = query.in_("class_id", class_ids)
        if grade_ids:
            query = query.in_("grade_id", grade_ids)

        students = query.execute()
        student_ids = [s["id"] for s in (students.data or [])]

        # Queue individual report card generation
        queued = 0
        for student_id in student_ids:
            generate_report_card.delay(
                student_id=student_id,
                term_id=term_id,
                school_id=school_id,
            )
            queued += 1

        logger.info(f"Bulk report card generation queued for {queued} students")
        return {"success": True, "queued": queued, "student_ids": student_ids}

    except Exception as e:
        logger.error(f"Failed to queue bulk report cards for {school_id}: {e}")
        return {"success": False, "error": str(e)}
