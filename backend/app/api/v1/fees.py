from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel
from app.core.auth import get_current_user, get_user_school_id
from app.db.supabase_client import get_supabase_admin

router = APIRouter()

class InvoiceCreate(BaseModel):
    student_id: str
    description: str
    amount: Decimal
    term_id: str
    due_date: date
    notes: Optional[str] = None

class PaymentCreate(BaseModel):
    invoice_id: str
    amount: Decimal
    payment_method: str
    payment_date: date
    reference_number: Optional[str] = None
    proof_url: Optional[str] = None

class FeeStructureCreate(BaseModel):
    grade_id: str
    term_id: str
    name: str
    amount: Decimal
    due_days_after_issue: int = 30

@router.get("/summary")
async def get_fee_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    result = supabase.rpc("get_fee_collection_summary", {
        "p_school_id": school_id,
        "p_start_date": start_date.isoformat() if start_date else None,
        "p_end_date": end_date.isoformat() if end_date else None
    }).execute()
    return result.data[0] if result.data else {}

@router.get("/invoices")
async def get_invoices(
    status: Optional[str] = None,
    student_id: Optional[str] = None,
    term_id: Optional[str] = None,
    overdue_only: bool = False,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    query = supabase.table("invoices").select("*, students(first_name, last_name, admission_number)").eq("school_id", school_id)
    
    if status:
        query = query.eq("status", status)
    if student_id:
        query = query.eq("student_id", student_id)
    if term_id:
        query = query.eq("term_id", term_id)
    if overdue_only:
        query = query.eq("status", "overdue")
    
    result = query.order("created_at", desc=True).execute()
    return result.data

@router.post("/invoices")
async def create_invoice(
    invoice: InvoiceCreate,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    invoice_no = supabase.rpc("generate_invoice_number", {"p_school_id": school_id}).execute().data
    
    data = {
        "school_id": school_id,
        "invoice_number": invoice_no,
        "student_id": invoice.student_id,
        "description": invoice.description,
        "amount": float(invoice.amount),
        "amount_paid": 0,
        "due_date": invoice.due_date.isoformat(),
        "status": "pending",
        "created_by": user["id"]
    }
    
    result = supabase.table("invoices").insert(data).execute()
    return result.data[0]

@router.post("/payments")
async def record_payment(
    payment: PaymentCreate,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    
    invoice = supabase.table("invoices").select("*").eq("id", payment.invoice_id).single().execute().data
    if not invoice:
        raise HTTPException(404, "Invoice not found")
    
    balance = invoice["amount"] - invoice["amount_paid"]
    if float(payment.amount) > balance:
        raise HTTPException(400, "Payment exceeds balance")
    
    payment_ref = f"PAY-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    payment_data = {
        "invoice_id": payment.invoice_id,
        "receipt_number": payment_ref,
        "amount": float(payment.amount),
        "payment_method": payment.payment_method,
        "reference": payment.reference_number,
        "recorded_by": user["id"]
    }
    
    supabase.table("payments").insert(payment_data).execute()
    
    new_paid = invoice["amount_paid"] + float(payment.amount)
    new_status = "paid" if new_paid >= invoice["amount"] else "partial"
    
    supabase.table("invoices").update({
        "amount_paid": new_paid,
        "status": new_status
    }).eq("id", payment.invoice_id).execute()
    
    return {"success": True, "payment_ref": payment_ref}

@router.post("/fee-structures")
async def create_fee_structure(
    structure: FeeStructureCreate,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    data = {**structure.dict(), "school_id": school_id}
    result = supabase.table("fee_structures").insert(data).execute()
    return result.data[0]

@router.post("/auto-generate")
async def auto_generate_invoices(
    grade_id: str,
    term_id: str,
    fee_structure_id: str,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    count = supabase.rpc("auto_generate_invoices", {
        "p_school_id": school_id,
        "p_grade_id": grade_id,
        "p_term_id": term_id,
        "p_fee_structure_id": fee_structure_id,
        "p_created_by": user["id"]
    }).execute().data
    return {"generated": count}
