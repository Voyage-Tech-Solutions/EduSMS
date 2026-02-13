from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from app.db.supabase import get_supabase_admin
from app.core.security import require_office_admin

router = APIRouter()

# ============================================================
# MODELS
# ============================================================

class CreateInvoiceRequest(BaseModel):
    student_id: str
    description: str
    amount: float
    due_date: str
    term_id: Optional[str] = None

class RecordPaymentRequest(BaseModel):
    invoice_id: str
    amount: float
    payment_method: str
    reference: Optional[str] = None

class AddStudentRequest(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str
    gender: str
    grade_id: str
    class_id: str
    admission_number: str

class VerifyDocumentRequest(BaseModel):
    document_id: str
    status: str
    notes: Optional[str] = None

# ============================================================
# DASHBOARD ENDPOINTS
# ============================================================

@router.get("/dashboard/priorities")
async def get_priorities(user: dict = Depends(require_office_admin)):
    """Get today's priority tasks"""
    try:
        supabase = get_supabase_admin()
        school_id = user.get("school_id")
        
        if not school_id:
            return {
                "admissions_pending": 0,
                "missing_documents": 0,
                "payments_to_allocate": 0,
                "proof_uploads": 0,
                "transfer_requests": 0,
                "letters_requested": 0
            }
    
        # Admissions pending verification
        admissions = supabase.table("admission_applications").select("id").eq("school_id", school_id).eq("status", "pending_verification").execute()
        
        # Missing documents
        students = supabase.table("students").select("id").eq("school_id", school_id).eq("status", "active").execute()
        docs = supabase.table("documents").select("student_id").eq("status", "missing").execute()
        missing_docs = len(set([d["student_id"] for d in docs.data])) if docs.data else 0
        
        # Payments to allocate
        payments = supabase.table("payments").select("id").eq("allocated", False).execute()
        
        return {
            "admissions_pending": len(admissions.data) if admissions.data else 0,
            "missing_documents": missing_docs,
            "payments_to_allocate": len(payments.data) if payments.data else 0,
            "proof_uploads": 0,
            "transfer_requests": 0,
            "letters_requested": 0
        }
    except Exception as e:
        print(f"Error in get_priorities: {str(e)}")
        return {
            "admissions_pending": 0,
            "missing_documents": 0,
            "payments_to_allocate": 0,
            "proof_uploads": 0,
            "transfer_requests": 0,
            "letters_requested": 0
        }

@router.get("/fees/snapshot")
async def get_fees_snapshot(user: dict = Depends(require_office_admin)):
    """Get fees overview"""
    try:
        supabase = get_supabase_admin()
        school_id = user.get("school_id")
        
        if not school_id:
            return {
                "collected_this_month": 0,
                "outstanding_balance": 0,
                "overdue_amount": 0,
                "active_payment_plans": 0
            }
    
        # Get all invoices
        invoices = supabase.table("invoices").select("amount, amount_paid, status, created_at, due_date").eq("school_id", school_id).execute()
        
        if not invoices.data:
            return {
                "collected_this_month": 0,
                "outstanding_balance": 0,
                "overdue_amount": 0,
                "active_payment_plans": 0
            }
        
        # Calculate metrics
        this_month = datetime.now().replace(day=1)
        collected_this_month = sum(
            inv["amount_paid"] for inv in invoices.data 
            if datetime.fromisoformat(inv["created_at"]).replace(tzinfo=None) >= this_month
        )
        
        outstanding = sum(inv["amount"] - inv["amount_paid"] for inv in invoices.data)
        
        overdue = sum(
            inv["amount"] - inv["amount_paid"] 
            for inv in invoices.data 
            if inv["status"] == "overdue"
        )
        
        return {
            "collected_this_month": round(collected_this_month, 2),
            "outstanding_balance": round(outstanding, 2),
            "overdue_amount": round(overdue, 2),
            "active_payment_plans": 0
        }
    except Exception as e:
        print(f"Error in get_fees_snapshot: {str(e)}")
        return {
            "collected_this_month": 0,
            "outstanding_balance": 0,
            "overdue_amount": 0,
            "active_payment_plans": 0
        }

@router.get("/students/snapshot")
async def get_students_snapshot(user: dict = Depends(require_office_admin)):
    """Get student admin overview"""
    try:
        supabase = get_supabase_admin()
        school_id = user.get("school_id")
        
        if not school_id:
            return {
                "total_active": 0,
                "new_this_month": 0,
                "pending_transfers": 0,
                "inactive_students": 0
            }
    
        students = supabase.table("students").select("id, status, created_at").eq("school_id", school_id).execute()
        
        if not students.data:
            return {
                "total_active": 0,
                "new_this_month": 0,
                "pending_transfers": 0,
                "inactive_students": 0
            }
        
        this_month = datetime.now().replace(day=1)
        new_this_month = len([
            s for s in students.data 
            if datetime.fromisoformat(s["created_at"]).replace(tzinfo=None) >= this_month
        ])
        
        return {
            "total_active": len([s for s in students.data if s["status"] == "active"]),
            "new_this_month": new_this_month,
            "pending_transfers": 0,
            "inactive_students": len([s for s in students.data if s["status"] == "inactive"])
        }
    except Exception as e:
        print(f"Error in get_students_snapshot: {str(e)}")
        return {
            "total_active": 0,
            "new_this_month": 0,
            "pending_transfers": 0,
            "inactive_students": 0
        }

@router.get("/documents/compliance")
async def get_compliance_status(user: dict = Depends(require_office_admin)):
    """Get document compliance metrics"""
    try:
        supabase = get_supabase_admin()
        school_id = user.get("school_id")
        
        docs = supabase.table("documents").select("document_type, status").execute()
        
        if not docs.data:
            return {
                "missing_birth_certificates": 0,
                "missing_parent_ids": 0,
                "missing_medical_forms": 0
            }
        
        return {
            "missing_birth_certificates": len([d for d in docs.data if d["document_type"] == "birth_certificate" and d["status"] == "missing"]),
            "missing_parent_ids": len([d for d in docs.data if d["document_type"] == "parent_id" and d["status"] == "missing"]),
            "missing_medical_forms": len([d for d in docs.data if d["document_type"] == "medical_form" and d["status"] == "missing"])
        }
    except Exception as e:
        print(f"Error in get_compliance_status: {str(e)}")
        return {
            "missing_birth_certificates": 0,
            "missing_parent_ids": 0,
            "missing_medical_forms": 0
        }

@router.get("/activity/recent")
async def get_recent_activity(user: dict = Depends(require_office_admin)):
    """Get recent admin activity"""
    try:
        supabase = get_supabase_admin()
        school_id = user.get("school_id")
        
        logs = supabase.table("audit_logs").select("action, created_at").eq("school_id", school_id).order("created_at", desc=True).limit(10).execute()
        
        if not logs.data:
            return []
        
        return [{
            "action": log["action"],
            "time": log["created_at"]
        } for log in logs.data]
    except Exception as e:
        print(f"Error in get_recent_activity: {str(e)}")
        return []

@router.get("/exceptions")
async def get_exceptions(user: dict = Depends(require_office_admin)):
    """Get system exceptions and flags"""
    return []

# ============================================================
# STUDENT OPERATIONS
# ============================================================

@router.post("/student/add")
async def add_student(request: AddStudentRequest, user: dict = Depends(require_office_admin)):
    """Add new student"""
    supabase = get_supabase_admin()
    school_id = user.get("school_id")
    
    result = supabase.table("students").insert({
        "school_id": school_id,
        "first_name": request.first_name,
        "last_name": request.last_name,
        "date_of_birth": request.date_of_birth,
        "gender": request.gender,
        "grade_id": request.grade_id,
        "class_id": request.class_id,
        "admission_number": request.admission_number,
        "status": "active"
    }).execute()
    
    return {"message": "Student added successfully", "data": result.data}

@router.patch("/students/{student_id}/status")
async def change_student_status(student_id: str, status: str, reason: str, user: dict = Depends(require_office_admin)):
    """Change student status"""
    supabase = get_supabase_admin()
    
    result = supabase.table("students").update({
        "status": status
    }).eq("id", student_id).execute()
    
    # Log the change
    supabase.table("audit_logs").insert({
        "action": f"Student status changed to {status}",
        "entity_type": "student",
        "entity_id": student_id,
        "notes": reason
    }).execute()
    
    return {"message": "Status updated successfully"}

# ============================================================
# ADMISSIONS OPERATIONS
# ============================================================

@router.get("/admissions")
async def get_admissions(status: Optional[str] = None, user: dict = Depends(require_office_admin)):
    """Get admission applications"""
    supabase = get_supabase_admin()
    
    query = supabase.table("admission_applications").select("*")
    
    if status:
        query = query.eq("status", status)
    
    result = query.execute()
    return result.data

@router.post("/admissions/{application_id}/verify")
async def verify_admission(application_id: str, approved: bool, notes: str, user: dict = Depends(require_office_admin)):
    """Verify admission application"""
    supabase = get_supabase_admin()
    
    new_status = "approved" if approved else "rejected"
    
    result = supabase.table("admission_applications").update({
        "status": new_status,
        "notes": notes
    }).eq("id", application_id).execute()
    
    return {"message": f"Application {new_status}"}

# ============================================================
# FEES OPERATIONS
# ============================================================

@router.post("/fees/invoices")
async def create_invoice(request: CreateInvoiceRequest, user: dict = Depends(require_office_admin)):
    """Create new invoice"""
    supabase = get_supabase_admin()
    
    # Generate invoice number
    count = supabase.table("invoices").select("id", count="exact").execute()
    invoice_number = f"INV-{datetime.now().year}-{count.count + 1:04d}"
    
    result = supabase.table("invoices").insert({
        "student_id": request.student_id,
        "invoice_number": invoice_number,
        "description": request.description,
        "amount": request.amount,
        "amount_paid": 0,
        "due_date": request.due_date,
        "term_id": request.term_id,
        "status": "pending"
    }).execute()
    
    return {"message": "Invoice created", "invoice_number": invoice_number, "data": result.data}

@router.post("/fees/payments")
async def record_payment(request: RecordPaymentRequest, user: dict = Depends(require_office_admin)):
    """Record payment"""
    supabase = get_supabase_admin()
    
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
        "reference": request.reference,
        "payment_date": datetime.now().isoformat()
    }).execute()
    
    # Update invoice
    new_amount_paid = invoice.data["amount_paid"] + request.amount
    new_status = "paid" if new_amount_paid >= invoice.data["amount"] else "partial"
    
    supabase.table("invoices").update({
        "amount_paid": new_amount_paid,
        "status": new_status
    }).eq("id", request.invoice_id).execute()
    
    return {"message": "Payment recorded", "data": payment.data}

# ============================================================
# ATTENDANCE OPERATIONS
# ============================================================

@router.post("/attendance/record")
async def record_attendance(class_id: str, date: str, records: list, user: dict = Depends(require_office_admin)):
    """Record attendance for a class"""
    supabase = get_supabase_admin()
    
    # Create session
    session = supabase.table("attendance_sessions").insert({
        "class_id": class_id,
        "date": date
    }).execute()
    
    session_id = session.data[0]["id"]
    
    # Create records
    attendance_records = [{
        "session_id": session_id,
        "student_id": record["student_id"],
        "date": date,
        "status": record["status"]
    } for record in records]
    
    result = supabase.table("attendance_records").insert(attendance_records).execute()
    
    return {"message": "Attendance recorded", "count": len(result.data)}

@router.patch("/attendance/{record_id}")
async def edit_attendance(record_id: str, status: str, reason: str, user: dict = Depends(require_office_admin)):
    """Edit attendance record"""
    supabase = get_supabase_admin()
    
    result = supabase.table("attendance_records").update({
        "status": status,
        "notes": reason
    }).eq("id", record_id).execute()
    
    # Log correction
    supabase.table("audit_logs").insert({
        "action": f"Attendance corrected to {status}",
        "entity_type": "attendance",
        "entity_id": record_id,
        "notes": reason
    }).execute()
    
    return {"message": "Attendance updated"}

# ============================================================
# DOCUMENT OPERATIONS
# ============================================================

@router.get("/documents/verification-queue")
async def get_verification_queue(user: dict = Depends(require_office_admin)):
    """Get documents awaiting verification"""
    supabase = get_supabase_admin()
    
    docs = supabase.table("documents").select("*, students(first_name, last_name)").eq("status", "pending").execute()
    
    return docs.data

@router.post("/documents/verify")
async def verify_document(request: VerifyDocumentRequest, user: dict = Depends(require_office_admin)):
    """Verify document"""
    supabase = get_supabase_admin()
    
    result = supabase.table("documents").update({
        "status": request.status,
        "verified_at": datetime.now().isoformat(),
        "notes": request.notes
    }).eq("id", request.document_id).execute()
    
    return {"message": "Document verified"}

# ============================================================
# REPORTS
# ============================================================

@router.get("/reports/student-directory")
async def get_student_directory(user: dict = Depends(require_office_admin)):
    """Generate student directory report"""
    supabase = get_supabase_admin()
    
    students = supabase.table("students").select("*, grades(name), classes(name)").eq("status", "active").execute()
    
    return students.data

@router.get("/reports/fee-statement")
async def get_fee_statement(student_id: Optional[str] = None, user: dict = Depends(require_office_admin)):
    """Generate fee statement"""
    supabase = get_supabase_admin()
    
    query = supabase.table("invoices").select("*, students(first_name, last_name)")
    
    if student_id:
        query = query.eq("student_id", student_id)
    
    result = query.execute()
    return result.data
