from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Dict, Any
from datetime import datetime, timedelta, date
from pydantic import BaseModel
from app.core.auth import get_current_user, get_user_school_id
from app.db.supabase_client import get_supabase_admin

router = APIRouter()

# ============================================================
# PYDANTIC MODELS
# ============================================================

class AttendanceRecord(BaseModel):
    student_id: str
    status: str
    notes: str = ""

class SaveAttendanceRequest(BaseModel):
    date: date
    class_id: str
    subject_id: str = None
    records: List[AttendanceRecord]

class CreateInvoiceRequest(BaseModel):
    student_id: str
    fee_type: str
    description: str
    amount: float
    due_date: date
    allow_payment_plan: bool = False
    notes: str = ""

class AddStudentRequest(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    admission_date: date
    grade_id: str
    class_id: str = None
    parent_name: str
    parent_id_number: str
    parent_phone: str
    parent_email: str = ""
    parent_address: str = ""
    medical_conditions: str = ""
    allergies: str = ""
    emergency_contact: str

class AddStaffRequest(BaseModel):
    full_name: str
    role: str
    department: str
    email: str
    phone: str
    employment_type: str
    salary: float = None

class BulkReminderRequest(BaseModel):
    target_type: str
    delivery_method: str
    message: str

class AllocatePaymentRequest(BaseModel):
    payment_id: str
    invoice_id: str
    amount: float

# ============================================================
# DASHBOARD ENDPOINTS
# ============================================================

@router.get("/dashboard/priorities")
async def get_today_priorities(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["office_admin", "principal"]:
        raise HTTPException(status_code=403, detail="Office admin access required")
    
    supabase = get_supabase_admin()
    school_id = get_user_school_id(current_user)
    
    # 1. Admissions awaiting document verification
    admissions_pending = supabase.table("user_profiles")\
        .select("id", count="exact")\
        .eq("school_id", school_id)\
        .eq("role", "student")\
        .eq("is_approved", False)\
        .execute()
    
    # 2. Students with missing documents
    missing_docs = supabase.table("student_documents")\
        .select("student_id", count="exact")\
        .eq("uploaded", False)\
        .execute()
    
    # 3. Payments to allocate (payments without invoice link)
    payments_to_allocate = supabase.table("payments")\
        .select("id", count="exact")\
        .is_("invoice_id", "null")\
        .execute()
    
    # 4. Proof of payment uploads
    proof_uploads = supabase.rpc("count_unverified_payments", {"p_school_id": school_id}).execute()
    
    # 5. Transfer requests pending
    transfers = supabase.table("transfer_requests")\
        .select("id", count="exact")\
        .eq("school_id", school_id)\
        .eq("status", "pending")\
        .execute()
    
    # 6. Letters requested
    letters = supabase.table("letter_requests")\
        .select("id", count="exact")\
        .eq("school_id", school_id)\
        .eq("status", "pending")\
        .execute()
    
    return {
        "admissions_pending": admissions_pending.count or 0,
        "missing_documents": missing_docs.count or 0,
        "payments_to_allocate": payments_to_allocate.count or 0,
        "proof_uploads": proof_uploads.data if proof_uploads.data else 0,
        "transfer_requests": transfers.count or 0,
        "letters_requested": letters.count or 0
    }

@router.get("/fees/snapshot")
async def get_fees_snapshot(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["office_admin", "principal"]:
        raise HTTPException(status_code=403, detail="Office admin access required")
    
    supabase = get_supabase_admin()
    school_id = get_user_school_id(current_user)
    
    # Collected this month
    first_day = datetime.now().replace(day=1).date().isoformat()
    payments = supabase.table("payments")\
        .select("amount")\
        .gte("created_at", first_day)\
        .execute()
    collected_this_month = sum(float(p["amount"]) for p in payments.data) if payments.data else 0
    
    # Outstanding balance
    invoices = supabase.table("invoices")\
        .select("amount, amount_paid")\
        .eq("school_id", school_id)\
        .execute()
    outstanding = sum(float(i["amount"]) - float(i["amount_paid"]) for i in invoices.data) if invoices.data else 0
    
    # Overdue (30+ days)
    thirty_days_ago = (datetime.now() - timedelta(days=30)).date().isoformat()
    overdue_invoices = supabase.table("invoices")\
        .select("amount, amount_paid")\
        .eq("school_id", school_id)\
        .lt("due_date", thirty_days_ago)\
        .neq("status", "paid")\
        .execute()
    overdue = sum(float(i["amount"]) - float(i["amount_paid"]) for i in overdue_invoices.data) if overdue_invoices.data else 0
    
    # Payment plans active
    payment_plans = supabase.table("payment_plans")\
        .select("id", count="exact")\
        .eq("school_id", school_id)\
        .eq("status", "active")\
        .execute()
    
    return {
        "collected_this_month": round(collected_this_month, 2),
        "outstanding_balance": round(outstanding, 2),
        "overdue_amount": round(overdue, 2),
        "active_payment_plans": payment_plans.count or 0
    }

@router.get("/students/snapshot")
async def get_students_snapshot(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["office_admin", "principal"]:
        raise HTTPException(status_code=403, detail="Office admin access required")
    
    supabase = get_supabase_admin()
    school_id = get_user_school_id(current_user)
    
    # Active students
    active = supabase.table("students")\
        .select("id", count="exact")\
        .eq("school_id", school_id)\
        .eq("status", "active")\
        .execute()
    
    # New admissions this month
    first_day = datetime.now().replace(day=1).date().isoformat()
    new_admissions = supabase.table("students")\
        .select("id", count="exact")\
        .eq("school_id", school_id)\
        .gte("admission_date", first_day)\
        .execute()
    
    # Pending transfers
    transfers = supabase.table("transfer_requests")\
        .select("id", count="exact")\
        .eq("school_id", school_id)\
        .eq("status", "pending")\
        .execute()
    
    # Inactive students
    inactive = supabase.table("students")\
        .select("id", count="exact")\
        .eq("school_id", school_id)\
        .eq("status", "inactive")\
        .execute()
    
    return {
        "total_active": active.count or 0,
        "new_this_month": new_admissions.count or 0,
        "pending_transfers": transfers.count or 0,
        "inactive_students": inactive.count or 0
    }

@router.get("/documents/compliance")
async def get_documents_compliance(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["office_admin", "principal"]:
        raise HTTPException(status_code=403, detail="Office admin access required")
    
    supabase = get_supabase_admin()
    school_id = get_user_school_id(current_user)
    
    # Missing birth certificates
    birth_certs = supabase.table("student_documents")\
        .select("id", count="exact")\
        .eq("document_type", "birth_certificate")\
        .eq("uploaded", False)\
        .execute()
    
    # Missing parent IDs
    parent_ids = supabase.table("student_documents")\
        .select("id", count="exact")\
        .eq("document_type", "parent_id")\
        .eq("uploaded", False)\
        .execute()
    
    # Missing medical forms
    medical_forms = supabase.table("student_documents")\
        .select("id", count="exact")\
        .eq("document_type", "medical_form")\
        .eq("uploaded", False)\
        .execute()
    
    return {
        "missing_birth_certificates": birth_certs.count or 0,
        "missing_parent_ids": parent_ids.count or 0,
        "missing_medical_forms": medical_forms.count or 0
    }

@router.get("/activity/recent")
async def get_recent_activity(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["office_admin", "principal"]:
        raise HTTPException(status_code=403, detail="Office admin access required")
    
    supabase = get_supabase_admin()
    school_id = get_user_school_id(current_user)
    
    logs = supabase.table("audit_logs")\
        .select("action, entity_type, created_at")\
        .eq("school_id", school_id)\
        .order("created_at", desc=True)\
        .limit(10)\
        .execute()
    
    activities = []
    for log in logs.data if logs.data else []:
        if log["entity_type"] in ["student", "payment", "invoice", "attendance"]:
            activities.append({
                "action": log["action"],
                "time": log["created_at"]
            })
    
    return activities

@router.get("/exceptions")
async def get_exceptions(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["office_admin", "principal"]:
        raise HTTPException(status_code=403, detail="Office admin access required")
    
    supabase = get_supabase_admin()
    school_id = get_user_school_id(current_user)
    
    exceptions = []
    
    # Check for students without invoices
    students_no_invoice = supabase.rpc("get_students_without_invoices", {"p_school_id": school_id}).execute()
    if students_no_invoice.data and len(students_no_invoice.data) > 0:
        exceptions.append({
            "type": "missing_invoice",
            "message": "Students enrolled but not invoiced",
            "count": len(students_no_invoice.data)
        })
    
    # Check for overdue fees > threshold
    overdue_high = supabase.table("invoices")\
        .select("id", count="exact")\
        .eq("school_id", school_id)\
        .lt("due_date", (datetime.now() - timedelta(days=60)).date().isoformat())\
        .neq("status", "paid")\
        .execute()
    
    if overdue_high.count and overdue_high.count > 20:
        exceptions.append({
            "type": "high_overdue",
            "message": "High number of overdue invoices (60+ days)",
            "count": overdue_high.count
        })
    
    return exceptions

# ============================================================
# ACTION ENDPOINTS
# ============================================================

@router.post("/attendance/save")
async def save_attendance(
    request: SaveAttendanceRequest,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] not in ["office_admin", "teacher", "principal"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    supabase = get_supabase_admin()
    school_id = get_user_school_id(current_user)
    
    # Create attendance session
    session = supabase.table("attendance_sessions").insert({
        "school_id": school_id,
        "class_id": request.class_id,
        "subject_id": request.subject_id,
        "date": request.date.isoformat(),
        "teacher_id": current_user["id"],
        "created_by": current_user["id"]
    }).execute()
    
    session_id = session.data[0]["id"]
    
    # Insert attendance records
    records = []
    for record in request.records:
        records.append({
            "school_id": school_id,
            "session_id": session_id,
            "student_id": record.student_id,
            "date": request.date.isoformat(),
            "status": record.status,
            "notes": record.notes,
            "recorded_by": current_user["id"]
        })
    
    supabase.table("attendance_records").insert(records).execute()
    
    # Audit log
    supabase.table("audit_logs").insert({
        "school_id": school_id,
        "user_id": current_user["id"],
        "action": f"Saved attendance for class {request.class_id}",
        "entity_type": "attendance",
        "entity_id": session_id
    }).execute()
    
    return {"success": True, "session_id": session_id}

@router.post("/invoice/create")
async def create_invoice(
    request: CreateInvoiceRequest,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] not in ["office_admin", "principal"]:
        raise HTTPException(status_code=403, detail="Office admin access required")
    
    supabase = get_supabase_admin()
    school_id = get_user_school_id(current_user)
    
    # Generate invoice number
    invoice_count = supabase.table("invoices")\
        .select("id", count="exact")\
        .eq("school_id", school_id)\
        .execute()
    invoice_number = f"INV-{datetime.now().year}-{(invoice_count.count or 0) + 1:05d}"
    
    # Create invoice
    invoice = supabase.table("invoices").insert({
        "school_id": school_id,
        "student_id": request.student_id,
        "invoice_number": invoice_number,
        "amount": request.amount,
        "amount_paid": 0,
        "due_date": request.due_date.isoformat(),
        "description": request.description,
        "status": "pending"
    }).execute()
    
    invoice_id = invoice.data[0]["id"]
    
    # Create payment plan if requested
    if request.allow_payment_plan:
        supabase.table("payment_plans").insert({
            "school_id": school_id,
            "student_id": request.student_id,
            "invoice_id": invoice_id,
            "total_amount": request.amount,
            "installment_amount": request.amount / 3,
            "frequency": "monthly",
            "start_date": datetime.now().date().isoformat(),
            "end_date": (datetime.now() + timedelta(days=90)).date().isoformat(),
            "status": "active",
            "created_by": current_user["id"]
        }).execute()
    
    # Audit log
    supabase.table("audit_logs").insert({
        "school_id": school_id,
        "user_id": current_user["id"],
        "action": f"Created invoice {invoice_number}",
        "entity_type": "invoice",
        "entity_id": invoice_id
    }).execute()
    
    return {"success": True, "invoice_id": invoice_id, "invoice_number": invoice_number}

@router.post("/student/add")
async def add_student(
    request: AddStudentRequest,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] not in ["office_admin", "principal"]:
        raise HTTPException(status_code=403, detail="Office admin access required")
    
    supabase = get_supabase_admin()
    school_id = get_user_school_id(current_user)
    
    # Generate admission number
    student_count = supabase.table("students")\
        .select("id", count="exact")\
        .eq("school_id", school_id)\
        .execute()
    admission_number = f"STU-{datetime.now().year}-{(student_count.count or 0) + 1:05d}"
    
    # Create student
    student = supabase.table("students").insert({
        "school_id": school_id,
        "admission_number": admission_number,
        "first_name": request.first_name,
        "last_name": request.last_name,
        "date_of_birth": request.date_of_birth.isoformat(),
        "gender": request.gender,
        "grade_id": request.grade_id,
        "class_id": request.class_id,
        "admission_date": request.admission_date.isoformat(),
        "medical_notes": f"{request.medical_conditions}\nAllergies: {request.allergies}",
        "status": "active"
    }).execute()
    
    student_id = student.data[0]["id"]
    
    # Create guardian
    supabase.table("guardians").insert({
        "student_id": student_id,
        "first_name": request.parent_name.split()[0],
        "last_name": " ".join(request.parent_name.split()[1:]) if len(request.parent_name.split()) > 1 else "",
        "relationship": "parent",
        "phone": request.parent_phone,
        "email": request.parent_email,
        "address": request.parent_address,
        "is_primary": True,
        "is_emergency_contact": True
    }).execute()
    
    # Initialize document checklist
    doc_types = ["birth_certificate", "parent_id", "medical_form"]
    for doc_type in doc_types:
        supabase.table("student_documents").insert({
            "student_id": student_id,
            "document_type": doc_type,
            "uploaded": False,
            "status": "missing"
        }).execute()
    
    # Audit log
    supabase.table("audit_logs").insert({
        "school_id": school_id,
        "user_id": current_user["id"],
        "action": f"Added student {admission_number}",
        "entity_type": "student",
        "entity_id": student_id
    }).execute()
    
    return {"success": True, "student_id": student_id, "admission_number": admission_number}

@router.post("/staff/add")
async def add_staff(
    request: AddStaffRequest,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] not in ["principal"]:
        raise HTTPException(status_code=403, detail="Principal access required")
    
    supabase = get_supabase_admin()
    school_id = get_user_school_id(current_user)
    
    # Create invitation
    import secrets
    token = secrets.token_urlsafe(32)
    
    invitation = supabase.table("invitations").insert({
        "school_id": school_id,
        "email": request.email,
        "role": request.role,
        "invited_by": current_user["id"],
        "token": token,
        "expires_at": (datetime.now() + timedelta(days=7)).isoformat()
    }).execute()
    
    # Audit log
    supabase.table("audit_logs").insert({
        "school_id": school_id,
        "user_id": current_user["id"],
        "action": f"Invited staff {request.email}",
        "entity_type": "invitation",
        "entity_id": invitation.data[0]["id"]
    }).execute()
    
    return {"success": True, "invitation_token": token}

@router.post("/notifications/bulk")
async def send_bulk_reminder(
    request: BulkReminderRequest,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] not in ["office_admin", "principal"]:
        raise HTTPException(status_code=403, detail="Office admin access required")
    
    supabase = get_supabase_admin()
    school_id = get_user_school_id(current_user)
    
    # Get target recipients based on type
    recipients = []
    if request.target_type == "missing_birth_certificates":
        docs = supabase.table("student_documents")\
            .select("student_id")\
            .eq("document_type", "birth_certificate")\
            .eq("uploaded", False)\
            .execute()
        student_ids = [d["student_id"] for d in docs.data] if docs.data else []
        guardians = supabase.table("guardians")\
            .select("user_id, email")\
            .in_("student_id", student_ids)\
            .eq("is_primary", True)\
            .execute()
        recipients = guardians.data if guardians.data else []
    
    # Queue notifications
    for recipient in recipients:
        if recipient.get("user_id"):
            supabase.table("notifications_log").insert({
                "school_id": school_id,
                "recipient_type": "parent",
                "recipient_id": recipient["user_id"],
                "delivery_method": request.delivery_method,
                "message_type": "document_reminder",
                "subject": "Missing Documents",
                "message": request.message,
                "status": "pending",
                "sent_by": current_user["id"]
            }).execute()
    
    # Audit log
    supabase.table("audit_logs").insert({
        "school_id": school_id,
        "user_id": current_user["id"],
        "action": f"Sent bulk reminder to {len(recipients)} recipients",
        "entity_type": "notification",
        "entity_id": None
    }).execute()
    
    return {"success": True, "recipients_count": len(recipients)}

@router.post("/payment/allocate")
async def allocate_payment(
    request: AllocatePaymentRequest,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] not in ["office_admin", "principal"]:
        raise HTTPException(status_code=403, detail="Office admin access required")
    
    supabase = get_supabase_admin()
    school_id = get_user_school_id(current_user)
    
    # Update payment with invoice link
    supabase.table("payments")\
        .update({"invoice_id": request.invoice_id})\
        .eq("id", request.payment_id)\
        .execute()
    
    # Update invoice amount_paid
    invoice = supabase.table("invoices")\
        .select("amount, amount_paid")\
        .eq("id", request.invoice_id)\
        .single()\
        .execute()
    
    new_amount_paid = float(invoice.data["amount_paid"]) + request.amount
    new_status = "paid" if new_amount_paid >= float(invoice.data["amount"]) else "partial"
    
    supabase.table("invoices")\
        .update({
            "amount_paid": new_amount_paid,
            "status": new_status
        })\
        .eq("id", request.invoice_id)\
        .execute()
    
    # Audit log
    supabase.table("audit_logs").insert({
        "school_id": school_id,
        "user_id": current_user["id"],
        "action": f"Allocated payment to invoice",
        "entity_type": "payment",
        "entity_id": request.payment_id
    }).execute()
    
    return {"success": True, "new_status": new_status}
