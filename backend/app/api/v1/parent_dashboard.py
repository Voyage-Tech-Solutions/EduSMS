from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from uuid import UUID
from datetime import date
from app.models.parent_dashboard import *
from app.core.auth import get_current_user
from app.db.supabase import get_supabase_client

router = APIRouter(prefix="/parent", tags=["parent-dashboard"])

@router.get("/dashboard")
async def get_parent_dashboard(
    student_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get parent dashboard overview"""
    supabase = get_supabase_client()
    parent_id = current_user["id"]
    
    # Get children
    children = supabase.rpc("get_parent_children", {"p_parent_id": parent_id}).execute()
    
    if not children.data:
        return {"error": "No children linked to this account"}
    
    # Use first child if not specified
    selected_student = student_id or children.data[0]["student_id"]
    
    # Daily status
    today_attendance = supabase.rpc("get_student_today_attendance", {"p_student_id": str(selected_student)}).execute()
    
    # Academic snapshot
    academic_avg = supabase.rpc("get_student_academic_average", {"p_student_id": str(selected_student)}).execute()
    missing_assignments = supabase.rpc("get_student_missing_assignments", {"p_student_id": str(selected_student)}).execute()
    
    # Financial summary
    invoices = supabase.table("invoices").select("*").eq("student_id", str(selected_student)).eq("status", "pending").execute()
    outstanding = sum(inv["amount"] - inv["paid_amount"] for inv in invoices.data)
    overdue = any(inv["due_date"] < str(date.today()) for inv in invoices.data)
    
    # Alerts
    alerts = supabase.rpc("get_student_alerts", {"p_student_id": str(selected_student)}).execute()
    
    # Unread messages
    unread_messages = supabase.rpc("get_parent_unread_messages", {"p_parent_id": parent_id}).execute()
    
    return {
        "children": children.data,
        "selected_student": selected_student,
        "daily_status": {
            "attendance_status": today_attendance.data or "not_recorded",
            "next_class": None,
            "alerts_count": len(alerts.data) if alerts.data else 0
        },
        "academic_snapshot": {
            "current_average": academic_avg.data or 0,
            "status": "good" if (academic_avg.data or 0) >= 70 else "at_risk" if (academic_avg.data or 0) >= 50 else "failing",
            "latest_score": None,
            "missing_assignments": missing_assignments.data or 0
        },
        "financial_summary": {
            "outstanding_balance": outstanding,
            "overdue": overdue,
            "next_due_date": invoices.data[0]["due_date"] if invoices.data else None
        },
        "alerts": alerts.data or [],
        "unread_messages": unread_messages.data or 0
    }

@router.get("/children")
async def get_children(current_user: dict = Depends(get_current_user)):
    """Get all children linked to parent"""
    supabase = get_supabase_client()
    children = supabase.rpc("get_parent_children", {"p_parent_id": current_user["id"]}).execute()
    return {"children": children.data or []}

@router.get("/attendance")
async def get_attendance(
    student_id: UUID,
    month: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get student attendance history"""
    supabase = get_supabase_client()
    
    query = supabase.table("attendance").select("*").eq("student_id", str(student_id)).order("date", desc=True)
    
    if month:
        query = query.gte("date", f"{month}-01").lte("date", f"{month}-31")
    
    attendance = query.execute()
    
    # Calculate stats
    total = len(attendance.data)
    present = len([a for a in attendance.data if a["status"] == "present"])
    absent = len([a for a in attendance.data if a["status"] == "absent"])
    late = len([a for a in attendance.data if a["status"] == "late"])
    
    return {
        "attendance": attendance.data,
        "stats": {
            "total": total,
            "present": present,
            "absent": absent,
            "late": late,
            "percentage": round((present / total * 100) if total > 0 else 0, 2)
        }
    }

@router.post("/attendance/report-absence")
async def report_absence(
    request: ReportAbsenceRequest,
    current_user: dict = Depends(get_current_user)
):
    """Report student absence"""
    supabase = get_supabase_client()
    
    # Get school_id from student
    student = supabase.table("students").select("school_id").eq("id", str(request.student_id)).single().execute()
    
    result = supabase.table("absence_reports").insert({
        "school_id": student.data["school_id"],
        "student_id": str(request.student_id),
        "reported_by": current_user["id"],
        "absence_date": str(request.absence_date),
        "reason": request.reason,
        "supporting_document_url": request.supporting_document_url,
        "status": "pending"
    }).execute()
    
    return {"message": "Absence reported successfully", "report_id": result.data[0]["id"]}

@router.get("/academics")
async def get_academics(
    student_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """Get student academic performance"""
    supabase = get_supabase_client()
    
    # Overall average
    overall_avg = supabase.rpc("get_student_academic_average", {"p_student_id": str(student_id)}).execute()
    
    # Subject averages
    subjects = supabase.table("assessment_scores").select("""
        *, assessments(subject_id, subjects(name))
    """).eq("student_id", str(student_id)).execute()
    
    # Group by subject
    subject_avgs = {}
    for score in subjects.data:
        if score["assessments"] and score["assessments"]["subjects"]:
            subject_name = score["assessments"]["subjects"]["name"]
            if subject_name not in subject_avgs:
                subject_avgs[subject_name] = []
            if score["percentage"]:
                subject_avgs[subject_name].append(score["percentage"])
    
    subject_summary = [
        {
            "subject": name,
            "average": round(sum(scores) / len(scores), 2) if scores else 0,
            "status": "good" if (sum(scores) / len(scores) if scores else 0) >= 70 else "at_risk"
        }
        for name, scores in subject_avgs.items()
    ]
    
    return {
        "overall_average": overall_avg.data or 0,
        "subjects": subject_summary,
        "assessments": subjects.data
    }

@router.get("/assignments")
async def get_assignments(
    student_id: UUID,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get student assignments"""
    supabase = get_supabase_client()
    
    # Get student's class
    student = supabase.table("students").select("class_id").eq("id", str(student_id)).single().execute()
    
    # Get assignments
    query = supabase.table("assignments").select("""
        *, subjects(name), assignment_submissions(*)
    """).eq("class_id", student.data["class_id"])
    
    if status:
        query = query.eq("status", status)
    
    assignments = query.execute()
    
    return {"assignments": assignments.data}

@router.post("/assignments/submit")
async def submit_assignment(
    request: SubmitAssignmentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Submit assignment"""
    supabase = get_supabase_client()
    
    result = supabase.table("assignment_submissions").upsert({
        "assignment_id": str(request.assignment_id),
        "student_id": str(request.student_id),
        "submission_url": request.submission_url,
        "submitted_at": "now()",
        "status": "submitted"
    }).execute()
    
    return {"message": "Assignment submitted successfully"}

@router.get("/invoices")
async def get_invoices(
    student_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """Get student invoices"""
    supabase = get_supabase_client()
    
    invoices = supabase.table("invoices").select("*").eq("student_id", str(student_id)).order("created_at", desc=True).execute()
    
    total_billed = sum(inv["amount"] for inv in invoices.data)
    total_paid = sum(inv["paid_amount"] for inv in invoices.data)
    balance = total_billed - total_paid
    
    return {
        "invoices": invoices.data,
        "summary": {
            "total_billed": total_billed,
            "total_paid": total_paid,
            "balance": balance
        }
    }

@router.post("/payments")
async def make_payment(
    request: PaymentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Process payment"""
    supabase = get_supabase_client()
    
    # Get invoice
    invoice = supabase.table("invoices").select("*").eq("id", str(request.invoice_id)).single().execute()
    
    # Create payment record
    payment = supabase.table("payments").insert({
        "invoice_id": str(request.invoice_id),
        "amount": request.amount,
        "payment_method": request.payment_method,
        "transaction_reference": request.transaction_reference,
        "paid_by": current_user["id"],
        "status": "completed"
    }).execute()
    
    # Update invoice
    new_paid = invoice.data["paid_amount"] + request.amount
    supabase.table("invoices").update({
        "paid_amount": new_paid,
        "status": "paid" if new_paid >= invoice.data["amount"] else "partial"
    }).eq("id", str(request.invoice_id)).execute()
    
    return {"message": "Payment processed successfully", "payment_id": payment.data[0]["id"]}

@router.get("/documents")
async def get_documents(
    student_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """Get student documents"""
    supabase = get_supabase_client()
    
    documents = supabase.table("student_documents").select("*").eq("student_id", str(student_id)).execute()
    
    return {"documents": documents.data}

@router.post("/documents/upload")
async def upload_document(
    request: UploadDocumentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Upload document"""
    supabase = get_supabase_client()
    
    result = supabase.table("student_documents").insert({
        "student_id": str(request.student_id),
        "document_type": request.document_type,
        "file_url": request.file_url,
        "expiry_date": str(request.expiry_date) if request.expiry_date else None,
        "status": "pending",
        "uploaded_by": current_user["id"]
    }).execute()
    
    return {"message": "Document uploaded successfully", "document_id": result.data[0]["id"]}

@router.get("/messages")
async def get_messages(
    current_user: dict = Depends(get_current_user)
):
    """Get parent messages"""
    supabase = get_supabase_client()
    
    messages = supabase.table("messages").select("""
        *, sender:user_profiles!messages_sender_id_fkey(first_name, last_name)
    """).eq("recipient_id", current_user["id"]).order("created_at", desc=True).execute()
    
    return {"messages": messages.data}

@router.post("/messages")
async def send_message(
    request: SendMessageRequest,
    current_user: dict = Depends(get_current_user)
):
    """Send message"""
    supabase = get_supabase_client()
    
    # Get school_id
    user = supabase.table("user_profiles").select("school_id").eq("id", current_user["id"]).single().execute()
    
    result = supabase.table("messages").insert({
        "school_id": user.data["school_id"],
        "sender_id": current_user["id"],
        "recipient_id": str(request.recipient_id),
        "subject": request.subject,
        "message": request.message,
        "attachment_url": request.attachment_url,
        "thread_id": str(request.thread_id) if request.thread_id else None
    }).execute()
    
    return {"message": "Message sent successfully", "message_id": result.data[0]["id"]}

@router.get("/notices")
async def get_notices(
    current_user: dict = Depends(get_current_user)
):
    """Get school notices"""
    supabase = get_supabase_client()
    
    # Get user's school
    user = supabase.table("user_profiles").select("school_id").eq("id", current_user["id"]).single().execute()
    
    notices = supabase.table("school_notices").select("*").eq(
        "school_id", user.data["school_id"]
    ).eq("is_active", True).order("published_at", desc=True).execute()
    
    return {"notices": notices.data}

@router.post("/notices/{notice_id}/acknowledge")
async def acknowledge_notice(
    notice_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """Acknowledge notice"""
    supabase = get_supabase_client()
    
    result = supabase.table("notice_acknowledgments").insert({
        "notice_id": str(notice_id),
        "user_id": current_user["id"]
    }).execute()
    
    return {"message": "Notice acknowledged"}

@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get parent profile"""
    supabase = get_supabase_client()
    
    profile = supabase.table("user_profiles").select("*").eq("id", current_user["id"]).single().execute()
    
    return {"profile": profile.data}

@router.patch("/profile")
async def update_profile(
    data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update parent profile"""
    supabase = get_supabase_client()
    
    result = supabase.table("user_profiles").update(data).eq("id", current_user["id"]).execute()
    
    return {"message": "Profile updated successfully"}
