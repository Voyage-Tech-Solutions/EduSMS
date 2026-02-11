"""
EduCore Backend - Fees & Billing API Endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional, List
from datetime import datetime, date
import uuid

from app.models import (
    FeeStructureCreate,
    FeeStructureResponse,
    InvoiceCreate,
    InvoiceResponse,
    PaymentCreate,
    PaymentResponse,
    PaymentStatus,
)
from app.core.security import get_current_user, require_office_admin, require_authenticated
from app.db.supabase import supabase_admin


router = APIRouter(prefix="/fees", tags=["Fees & Billing"])


def generate_invoice_number() -> str:
    """Generate unique invoice number"""
    year = datetime.now().year
    month = datetime.now().month
    short_id = str(uuid.uuid4())[:6].upper()
    return f"INV-{year}{month:02d}-{short_id}"


def generate_receipt_number() -> str:
    """Generate unique receipt number"""
    year = datetime.now().year
    short_id = str(uuid.uuid4())[:6].upper()
    return f"RCP-{year}-{short_id}"


# ============== FEE STRUCTURES ==============

@router.get("/structures", response_model=List[FeeStructureResponse])
async def list_fee_structures(
    grade_id: Optional[str] = None,
    year: Optional[int] = None,
    current_user: dict = Depends(require_office_admin),
):
    """List all fee structures for the school"""
    school_id = current_user.get("school_id")
    
    if supabase_admin:
        query = supabase_admin.table("fee_structures").select("*").eq("school_id", school_id)
        
        if grade_id:
            query = query.eq("grade_id", grade_id)
        if year:
            query = query.eq("year", year)
        
        result = query.order("created_at", desc=True).execute()
        return result.data
    else:
        return [
            {
                "id": "mock-fee-1",
                "school_id": school_id,
                "name": "Tuition Fee",
                "amount": 5000.00,
                "grade_id": None,
                "term": "Term 1",
                "year": 2024,
                "created_at": datetime.now().isoformat(),
            }
        ]


@router.post("/structures", response_model=FeeStructureResponse, status_code=status.HTTP_201_CREATED)
async def create_fee_structure(
    fee_data: FeeStructureCreate,
    current_user: dict = Depends(require_office_admin),
):
    """Create a new fee structure"""
    school_id = current_user.get("school_id")
    
    fee_dict = {
        "school_id": school_id,
        "name": fee_data.name,
        "amount": fee_data.amount,
        "grade_id": fee_data.grade_id,
        "term": fee_data.term,
        "year": fee_data.year,
    }
    
    if supabase_admin:
        result = supabase_admin.table("fee_structures").insert(fee_dict).execute()
        return result.data[0]
    else:
        return {**fee_dict, "id": "mock-new-fee", "created_at": datetime.now().isoformat()}


# ============== INVOICES ==============

@router.get("/invoices", response_model=List[InvoiceResponse])
async def list_invoices(
    student_id: Optional[str] = None,
    status_filter: Optional[PaymentStatus] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(require_office_admin),
):
    """List all invoices for the school"""
    school_id = current_user.get("school_id")
    
    if supabase_admin:
        query = supabase_admin.table("invoices").select("*").eq("school_id", school_id)
        
        if student_id:
            query = query.eq("student_id", student_id)
        if status_filter:
            query = query.eq("status", status_filter.value)
        
        result = query.range(skip, skip + limit - 1).order("created_at", desc=True).execute()
        return result.data
    else:
        return [
            {
                "id": "mock-invoice-1",
                "school_id": school_id,
                "student_id": "mock-student-1",
                "invoice_number": "INV-202401-ABC123",
                "amount": 5000.00,
                "amount_paid": 0,
                "due_date": "2024-02-28",
                "description": "Term 1 Tuition",
                "status": "pending",
                "created_at": datetime.now().isoformat(),
            }
        ]


@router.post("/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_data: InvoiceCreate,
    current_user: dict = Depends(require_office_admin),
):
    """Create a new invoice for a student"""
    school_id = current_user.get("school_id")
    
    invoice_dict = {
        "school_id": school_id,
        "student_id": invoice_data.student_id,
        "fee_structure_id": invoice_data.fee_structure_id,
        "invoice_number": generate_invoice_number(),
        "amount": invoice_data.amount,
        "amount_paid": 0,
        "due_date": invoice_data.due_date.isoformat(),
        "description": invoice_data.description,
        "status": PaymentStatus.PENDING.value,
    }
    
    if supabase_admin:
        # Verify student belongs to school
        student = supabase_admin.table("students").select("id").eq("id", invoice_data.student_id).eq("school_id", school_id).execute()
        
        if not student.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        result = supabase_admin.table("invoices").insert(invoice_dict).execute()
        return result.data[0]
    else:
        return {**invoice_dict, "id": "mock-new-invoice", "created_at": datetime.now().isoformat()}


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
    current_user: dict = Depends(require_authenticated),
):
    """Get a specific invoice"""
    school_id = current_user.get("school_id")
    
    if supabase_admin:
        result = supabase_admin.table("invoices").select("*").eq("id", invoice_id).eq("school_id", school_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        return result.data[0]
    else:
        return {
            "id": invoice_id,
            "school_id": school_id,
            "student_id": "mock-student-1",
            "invoice_number": "INV-202401-ABC123",
            "amount": 5000.00,
            "amount_paid": 0,
            "due_date": "2024-02-28",
            "status": "pending",
        }


# ============== PAYMENTS ==============

@router.get("/payments", response_model=List[PaymentResponse])
async def list_payments(
    invoice_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(require_office_admin),
):
    """List all payments"""
    school_id = current_user.get("school_id")
    
    if supabase_admin:
        query = supabase_admin.table("payments").select("*, invoices!inner(school_id)").eq("invoices.school_id", school_id)
        
        if invoice_id:
            query = query.eq("invoice_id", invoice_id)
        
        result = query.range(skip, skip + limit - 1).order("created_at", desc=True).execute()
        return result.data
    else:
        return [
            {
                "id": "mock-payment-1",
                "invoice_id": "mock-invoice-1",
                "receipt_number": "RCP-2024-ABC123",
                "amount": 2500.00,
                "payment_method": "cash",
                "reference": None,
                "created_at": datetime.now().isoformat(),
            }
        ]


@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def record_payment(
    payment_data: PaymentCreate,
    current_user: dict = Depends(require_office_admin),
):
    """Record a payment for an invoice"""
    school_id = current_user.get("school_id")
    
    if supabase_admin:
        # Get and verify invoice
        invoice_result = supabase_admin.table("invoices").select("*").eq("id", payment_data.invoice_id).eq("school_id", school_id).execute()
        
        if not invoice_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        invoice = invoice_result.data[0]
        remaining = invoice["amount"] - invoice["amount_paid"]
        
        if payment_data.amount > remaining:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment amount exceeds remaining balance of {remaining}"
            )
        
        # Create payment
        payment_dict = {
            "invoice_id": payment_data.invoice_id,
            "receipt_number": generate_receipt_number(),
            "amount": payment_data.amount,
            "payment_method": payment_data.payment_method,
            "reference": payment_data.reference,
        }
        
        result = supabase_admin.table("payments").insert(payment_dict).execute()
        
        # Update invoice
        new_amount_paid = invoice["amount_paid"] + payment_data.amount
        new_status = PaymentStatus.PAID.value if new_amount_paid >= invoice["amount"] else PaymentStatus.PARTIAL.value
        
        supabase_admin.table("invoices").update({
            "amount_paid": new_amount_paid,
            "status": new_status,
        }).eq("id", payment_data.invoice_id).execute()
        
        return result.data[0]
    else:
        return {
            "id": "mock-new-payment",
            "invoice_id": payment_data.invoice_id,
            "receipt_number": generate_receipt_number(),
            "amount": payment_data.amount,
            "payment_method": payment_data.payment_method,
            "reference": payment_data.reference,
            "created_at": datetime.now().isoformat(),
        }


# ============== PARENT VIEW ==============

@router.get("/my-invoices", response_model=List[InvoiceResponse])
async def get_my_invoices(
    current_user: dict = Depends(require_authenticated),
):
    """Get invoices for the parent's children (for parent role)"""
    user_id = current_user.get("id")
    school_id = current_user.get("school_id")
    role = current_user.get("role")
    
    if role not in ["parent", "student"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is for parents and students only"
        )
    
    if supabase_admin:
        if role == "student":
            # Get student's own invoices
            student = supabase_admin.table("students").select("id").eq("user_id", user_id).execute()
            if student.data:
                result = supabase_admin.table("invoices").select("*").eq("student_id", student.data[0]["id"]).execute()
                return result.data
        else:
            # Get invoices for parent's children
            guardians = supabase_admin.table("guardians").select("student_id").eq("user_id", user_id).execute()
            if guardians.data:
                student_ids = [g["student_id"] for g in guardians.data]
                result = supabase_admin.table("invoices").select("*").in_("student_id", student_ids).execute()
                return result.data
    
    return []
