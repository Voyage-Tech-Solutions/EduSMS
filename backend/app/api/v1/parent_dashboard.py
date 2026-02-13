from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel
from app.db.supabase import get_supabase_admin

router = APIRouter()

# ============================================================
# MODELS
# ============================================================

class ReportAbsenceRequest(BaseModel):
    student_id: str
    absence_date: str
    reason: str
    document_url: Optional[str] = None

class SubmitAssignmentRequest(BaseModel):
    assignment_id: str
    student_id: str
    submission_url: str
    notes: Optional[str] = None

class PaymentRequest(BaseModel):
    invoice_id: str
    amount: float
    payment_method: str

class UploadDocumentRequest(BaseModel):
    student_id: str
    document_type: str
    document_url: str
    expiry_date: Optional[str] = None

class SendMessageRequest(BaseModel):
    recipient_id: str
    subject: str
    message: str

class UpdateProfileRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    emergency_contact: Optional[str] = None
    notification_preferences: Optional[dict] = None

# ============================================================
# PAGE 1: PARENT HOME (OVERVIEW DASHBOARD)
# ============================================================

@router.get("/dashboard")
async def get_parent_dashboard(
    student_id: Optional[str] = Query(None),
    supabase = Depends(get_supabase_admin)
):
    """Parent home dashboard with daily status, academic snapshot, financial summary, alerts"""
    
    # Get parent's children
    children_response = supabase.table("students").select(
        "id, first_name, last_name, admission_number, grades(name), classes(name)"
    ).execute()
    
    children = [{
        "student_id": child["id"],
        "student_name": f"{child['first_name']} {child['last_name']}",
        "grade_name": child["grades"]["name"] if child.get("grades") else "N/A"
    } for child in children_response.data]
    
    # Select first child if not specified
    selected_student = student_id or (children[0]["student_id"] if children else None)
    
    if not selected_student:
        return {"children": [], "message": "No children found"}
    
    # Daily Status
    today = datetime.now().date()
    attendance_today = supabase.table("attendance_records").select("status").eq(
        "student_id", selected_student
    ).eq("date", str(today)).execute()
    
    daily_status = {
        "attendance_status": attendance_today.data[0]["status"] if attendance_today.data else "not_recorded",
        "next_class": "Mathematics - 10:00 AM",  # TODO: Get from timetable
        "alerts_count": 0
    }
    
    # Academic Snapshot
    assessments = supabase.table("assessment_scores").select(
        "score, assessments(total_marks)"
    ).eq("student_id", selected_student).order("created_at", desc=True).limit(10).execute()
    
    if assessments.data:
        scores = [(s["score"] / s["assessments"]["total_marks"] * 100) for s in assessments.data if s.get("assessments")]
        avg = sum(scores) / len(scores) if scores else 0
        status = "good" if avg >= 70 else "at_risk" if avg >= 50 else "failing"
        latest_score = f"{assessments.data[0]['score']}/{assessments.data[0]['assessments']['total_marks']}" if assessments.data[0].get("assessments") else "N/A"
    else:
        avg, status, latest_score = 0, "N/A", "N/A"
    
    academic_snapshot = {
        "current_average": round(avg, 1),
        "status": status,
        "latest_score": latest_score,
        "missing_assignments": 0  # TODO: Calculate from assignments
    }
    
    # Financial Summary
    invoices = supabase.table("invoices").select("amount, amount_paid, due_date, status").eq(
        "student_id", selected_student
    ).execute()
    
    outstanding = sum(inv["amount"] - inv["amount_paid"] for inv in invoices.data)
    overdue = any(inv["status"] == "overdue" for inv in invoices.data)
    next_due = min([inv["due_date"] for inv in invoices.data if inv["status"] != "paid"], default=None)
    
    financial_summary = {
        "outstanding_balance": round(outstanding, 2),
        "overdue": overdue,
        "next_due_date": next_due
    }
    
    # Alerts
    alerts = []
    if overdue:
        alerts.append({"alert_message": "Payment overdue", "severity": "high"})
    if avg < 50:
        alerts.append({"alert_message": "Low academic performance", "severity": "high"})
    
    return {
        "children": children,
        "selected_student": selected_student,
        "daily_status": daily_status,
        "academic_snapshot": academic_snapshot,
        "financial_summary": financial_summary,
        "alerts": alerts,
        "unread_messages": 0
    }

# ============================================================
# PAGE 2: MY CHILDREN
# ============================================================

@router.get("/children")
async def get_children(supabase = Depends(get_supabase_admin)):
    """List all children with overview stats"""
    
    children_response = supabase.table("students").select(
        "id, first_name, last_name, admission_number, status, grades(name)"
    ).execute()
    
    children_data = []
    for child in children_response.data:
        # Get attendance rate
        attendance = supabase.table("attendance_records").select("status").eq(
            "student_id", child["id"]
        ).execute()
        total = len(attendance.data)
        present = len([a for a in attendance.data if a["status"] == "present"])
        attendance_rate = round((present / total * 100) if total > 0 else 0, 1)
        
        # Get academic average
        assessments = supabase.table("assessment_scores").select(
            "score, assessments(total_marks)"
        ).eq("student_id", child["id"]).execute()
        
        if assessments.data:
            scores = [(s["score"] / s["assessments"]["total_marks"] * 100) for s in assessments.data if s.get("assessments")]
            academic_avg = round(sum(scores) / len(scores) if scores else 0, 1)
        else:
            academic_avg = 0
        
        # Get outstanding fees
        invoices = supabase.table("invoices").select("amount, amount_paid").eq(
            "student_id", child["id"]
        ).execute()
        outstanding_fees = sum(inv["amount"] - inv["amount_paid"] for inv in invoices.data)
        
        children_data.append({
            "student_id": child["id"],
            "student_name": f"{child['first_name']} {child['last_name']}",
            "grade_name": child["grades"]["name"] if child.get("grades") else "N/A",
            "attendance_rate": attendance_rate,
            "academic_average": academic_avg,
            "outstanding_fees": round(outstanding_fees, 2),
            "status": child["status"]
        })
    
    return {"children": children_data}

# ============================================================
# PAGE 3: ATTENDANCE
# ============================================================

@router.get("/attendance")
async def get_attendance(
    student_id: str = Query(...),
    supabase = Depends(get_supabase_admin)
):
    """Get attendance records and statistics"""
    
    attendance_records = supabase.table("attendance_records").select(
        "id, date, status, notes"
    ).eq("student_id", student_id).order("date", desc=True).execute()
    
    # Calculate stats
    total = len(attendance_records.data)
    present = len([a for a in attendance_records.data if a["status"] == "present"])
    absent = len([a for a in attendance_records.data if a["status"] == "absent"])
    late = len([a for a in attendance_records.data if a["status"] == "late"])
    percentage = round((present / total * 100) if total > 0 else 0, 1)
    
    return {
        "attendance": attendance_records.data,
        "stats": {
            "total": total,
            "present": present,
            "absent": absent,
            "late": late,
            "percentage": percentage
        }
    }

@router.post("/attendance/report-absence")
async def report_absence(
    request: ReportAbsenceRequest,
    supabase = Depends(get_supabase_admin)
):
    """Report student absence"""
    
    # Create absence record or update existing
    result = supabase.table("attendance_records").insert({
        "student_id": request.student_id,
        "date": request.absence_date,
        "status": "excused",
        "notes": request.reason
    }).execute()
    
    return {"message": "Absence reported successfully", "data": result.data}

# ============================================================
# PAGE 4: ACADEMICS
# ============================================================

@router.get("/academics")
async def get_academics(
    student_id: str = Query(...),
    supabase = Depends(get_supabase_admin)
):
    """Get academic performance by subject"""
    
    # Get all assessment scores
    assessments = supabase.table("assessment_scores").select(
        "score, assessments(id, title, total_marks, subjects(name))"
    ).eq("student_id", student_id).execute()
    
    # Group by subject
    subject_scores = {}
    for assessment in assessments.data:
        if not assessment.get("assessments"):
            continue
        subject = assessment["assessments"]["subjects"]["name"]
        score_pct = (assessment["score"] / assessment["assessments"]["total_marks"]) * 100
        
        if subject not in subject_scores:
            subject_scores[subject] = []
        subject_scores[subject].append(score_pct)
    
    # Calculate subject averages
    subjects = []
    for subject, scores in subject_scores.items():
        avg = sum(scores) / len(scores)
        status = "good" if avg >= 70 else "at_risk" if avg >= 50 else "failing"
        subjects.append({
            "subject": subject,
            "average": round(avg, 1),
            "status": status
        })
    
    # Overall average
    all_scores = [s for scores in subject_scores.values() for s in scores]
    overall_avg = round(sum(all_scores) / len(all_scores) if all_scores else 0, 1)
    
    return {
        "overall_average": overall_avg,
        "subjects": subjects,
        "assessments": assessments.data
    }

# ============================================================
# PAGE 5: ASSIGNMENTS & HOMEWORK
# ============================================================

@router.get("/assignments")
async def get_assignments(
    student_id: str = Query(...),
    supabase = Depends(get_supabase_admin)
):
    """Get all assignments for student"""
    
    # Get student's class
    student = supabase.table("students").select("class_id").eq("id", student_id).single().execute()
    
    if not student.data:
        return {"assignments": []}
    
    # Get assignments for class
    assignments = supabase.table("assignments").select(
        "*, subjects(name), assignment_submissions(status, score, feedback, submitted_at)"
    ).eq("class_id", student.data["class_id"]).order("due_date", desc=True).execute()
    
    return {"assignments": assignments.data}

@router.post("/assignments/upload")
async def submit_assignment(
    request: SubmitAssignmentRequest,
    supabase = Depends(get_supabase_admin)
):
    """Submit assignment"""
    
    result = supabase.table("assignment_submissions").insert({
        "assignment_id": request.assignment_id,
        "student_id": request.student_id,
        "submission_url": request.submission_url,
        "notes": request.notes,
        "status": "submitted",
        "submitted_at": datetime.now().isoformat()
    }).execute()
    
    return {"message": "Assignment submitted successfully", "data": result.data}

# ============================================================
# PAGE 6: FEES & PAYMENTS
# ============================================================

@router.get("/invoices")
async def get_invoices(
    student_id: str = Query(...),
    supabase = Depends(get_supabase_admin)
):
    """Get all invoices and payment history"""
    
    invoices = supabase.table("invoices").select(
        "id, invoice_number, description, amount, amount_paid, due_date, status, created_at"
    ).eq("student_id", student_id).order("created_at", desc=True).execute()
    
    # Get payments
    payments = supabase.table("payments").select(
        "id, amount, payment_method, payment_date, invoices(invoice_number)"
    ).eq("student_id", student_id).order("payment_date", desc=True).execute()
    
    # Calculate totals
    total_billed = sum(inv["amount"] for inv in invoices.data)
    total_paid = sum(inv["amount_paid"] for inv in invoices.data)
    balance = total_billed - total_paid
    overdue = sum(inv["amount"] - inv["amount_paid"] for inv in invoices.data if inv["status"] == "overdue")
    
    return {
        "invoices": invoices.data,
        "payments": payments.data,
        "summary": {
            "total_billed": round(total_billed, 2),
            "total_paid": round(total_paid, 2),
            "balance": round(balance, 2),
            "overdue_amount": round(overdue, 2)
        }
    }

@router.post("/payments")
async def make_payment(
    request: PaymentRequest,
    supabase = Depends(get_supabase_admin)
):
    """Process payment"""
    
    # Get invoice
    invoice = supabase.table("invoices").select("*").eq("id", request.invoice_id).single().execute()
    
    if not invoice.data:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Create payment record
    payment = supabase.table("payments").insert({
        "invoice_id": request.invoice_id,
        "student_id": invoice.data["student_id"],
        "amount": request.amount,
        "payment_method": request.payment_method,
        "payment_date": datetime.now().isoformat()
    }).execute()
    
    # Update invoice
    new_amount_paid = invoice.data["amount_paid"] + request.amount
    new_status = "paid" if new_amount_paid >= invoice.data["amount"] else "partial"
    
    supabase.table("invoices").update({
        "amount_paid": new_amount_paid,
        "status": new_status
    }).eq("id", request.invoice_id).execute()
    
    return {"message": "Payment processed successfully", "payment": payment.data}

# ============================================================
# PAGE 7: DOCUMENTS
# ============================================================

@router.get("/documents")
async def get_documents(
    student_id: str = Query(...),
    supabase = Depends(get_supabase_admin)
):
    """Get all documents for student"""
    
    documents = supabase.table("documents").select(
        "id, document_type, document_url, status, expiry_date, uploaded_at"
    ).eq("student_id", student_id).order("uploaded_at", desc=True).execute()
    
    return {"documents": documents.data}

@router.post("/documents/upload")
async def upload_document(
    request: UploadDocumentRequest,
    supabase = Depends(get_supabase_admin)
):
    """Upload document"""
    
    result = supabase.table("documents").insert({
        "student_id": request.student_id,
        "document_type": request.document_type,
        "document_url": request.document_url,
        "expiry_date": request.expiry_date,
        "status": "pending",
        "uploaded_at": datetime.now().isoformat()
    }).execute()
    
    return {"message": "Document uploaded successfully", "data": result.data}

# ============================================================
# PAGE 8: MESSAGES
# ============================================================

@router.get("/messages")
async def get_messages(supabase = Depends(get_supabase_admin)):
    """Get all messages"""
    
    messages = supabase.table("messages").select(
        "id, subject, message, sender_id, recipient_id, read, created_at, user_profiles!sender_id(first_name, last_name)"
    ).order("created_at", desc=True).execute()
    
    return {"messages": messages.data}

@router.post("/messages")
async def send_message(
    request: SendMessageRequest,
    supabase = Depends(get_supabase_admin)
):
    """Send message"""
    
    result = supabase.table("messages").insert({
        "recipient_id": request.recipient_id,
        "subject": request.subject,
        "message": request.message,
        "read": False,
        "created_at": datetime.now().isoformat()
    }).execute()
    
    return {"message": "Message sent successfully", "data": result.data}

# ============================================================
# PAGE 9: SCHOOL NOTICES
# ============================================================

@router.get("/notices")
async def get_notices(supabase = Depends(get_supabase_admin)):
    """Get all school notices"""
    
    notices = supabase.table("announcements").select(
        "id, title, content, priority, published_at"
    ).eq("published", True).order("published_at", desc=True).execute()
    
    return {"notices": notices.data}

@router.post("/notices/{notice_id}/acknowledge")
async def acknowledge_notice(
    notice_id: str,
    supabase = Depends(get_supabase_admin)
):
    """Acknowledge a school notice"""

    # Upsert to avoid duplicate acknowledgements
    result = supabase.table("notice_acknowledgements").upsert({
        "notice_id": notice_id,
        "acknowledged_at": datetime.now().isoformat()
    }, on_conflict="notice_id").execute()

    return {"message": "Notice acknowledged", "data": result.data}

# ============================================================
# PAGE 10: PARENT PROFILE
# ============================================================

@router.get("/profile")
async def get_profile(supabase = Depends(get_supabase_admin)):
    """Get parent profile"""
    
    profile = supabase.table("user_profiles").select(
        "first_name, last_name, email, phone, notification_preferences"
    ).single().execute()
    
    return profile.data

@router.patch("/profile")
async def update_profile(
    request: UpdateProfileRequest,
    supabase = Depends(get_supabase_admin)
):
    """Update parent profile"""
    
    update_data = {k: v for k, v in request.dict().items() if v is not None}
    
    result = supabase.table("user_profiles").update(update_data).execute()
    
    return {"message": "Profile updated successfully", "data": result.data}
