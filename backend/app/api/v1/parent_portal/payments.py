"""
EduCore Backend - Parent Payment Portal API
Enhanced payment management for parents
"""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# MODELS
# ============================================================

class PaymentCreate(BaseModel):
    """Create a payment"""
    fee_record_id: UUID
    amount: float
    payment_method: str  # card, bank_transfer, cash, check
    reference_number: Optional[str] = None
    notes: Optional[str] = None


class PaymentMethodSave(BaseModel):
    """Save a payment method"""
    method_type: str  # card, bank_account
    last_four: str
    card_brand: Optional[str] = None
    expiry_month: Optional[int] = None
    expiry_year: Optional[int] = None
    is_default: bool = False
    nickname: Optional[str] = None


# ============================================================
# FEE OVERVIEW
# ============================================================

@router.get("/overview")
async def get_payment_overview(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get payment overview for all children"""
    parent_id = current_user.get("id")

    # Get parent's children
    relations = supabase.table("parent_student_relations").select(
        "student_id, students(id, first_name, last_name)"
    ).eq("parent_id", parent_id).execute()

    children = []
    total_outstanding = 0
    total_paid = 0

    for rel in (relations.data or []):
        if rel.get("students"):
            student = rel["students"]
            student_id = student["id"]

            # Get fee records for this student
            fees = supabase.table("fee_records").select(
                "amount, amount_paid, status, due_date"
            ).eq("student_id", student_id).execute()

            student_total = sum(f.get("amount", 0) for f in (fees.data or []))
            student_paid = sum(f.get("amount_paid", 0) for f in (fees.data or []))
            student_outstanding = student_total - student_paid

            overdue_count = sum(
                1 for f in (fees.data or [])
                if f.get("status") == "overdue" or (
                    f.get("due_date") and f["due_date"] < date.today().isoformat() and
                    f.get("amount", 0) > f.get("amount_paid", 0)
                )
            )

            children.append({
                "student_id": student_id,
                "student_name": f"{student['first_name']} {student['last_name']}",
                "total_fees": student_total,
                "total_paid": student_paid,
                "outstanding": student_outstanding,
                "overdue_count": overdue_count
            })

            total_outstanding += student_outstanding
            total_paid += student_paid

    return {
        "children": children,
        "total_outstanding": total_outstanding,
        "total_paid": total_paid,
        "total_fees": total_outstanding + total_paid
    }


@router.get("/fees/{student_id}")
async def get_student_fees(
    student_id: UUID,
    status: Optional[str] = None,
    academic_year_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get fee records for a specific child"""
    parent_id = current_user.get("id")

    # Verify parent owns student
    relation = supabase.table("parent_student_relations").select("id").eq(
        "parent_id", parent_id
    ).eq("student_id", str(student_id)).execute()

    if not relation.data:
        raise HTTPException(status_code=403, detail="You can only view fees for your own children")

    query = supabase.table("fee_records").select(
        "*, fee_types(name, category)"
    ).eq("student_id", str(student_id))

    if status:
        query = query.eq("status", status)
    if academic_year_id:
        query = query.eq("academic_year_id", str(academic_year_id))

    result = query.order("due_date").execute()

    return {"fees": result.data or []}


@router.get("/fees/{student_id}/outstanding")
async def get_outstanding_fees(
    student_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get outstanding fees for a child"""
    parent_id = current_user.get("id")

    # Verify parent owns student
    relation = supabase.table("parent_student_relations").select("id").eq(
        "parent_id", parent_id
    ).eq("student_id", str(student_id)).execute()

    if not relation.data:
        raise HTTPException(status_code=403, detail="Access denied")

    result = supabase.table("fee_records").select(
        "*, fee_types(name, category)"
    ).eq("student_id", str(student_id)).neq("status", "paid").order("due_date").execute()

    fees = result.data or []

    # Calculate totals
    total = sum(f.get("amount", 0) - f.get("amount_paid", 0) for f in fees)

    return {
        "outstanding_fees": fees,
        "total_outstanding": total
    }


# ============================================================
# PAYMENT HISTORY
# ============================================================

@router.get("/history")
async def get_payment_history(
    student_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get payment history"""
    parent_id = current_user.get("id")

    # Get parent's children
    relations = supabase.table("parent_student_relations").select(
        "student_id"
    ).eq("parent_id", parent_id).execute()

    student_ids = [r["student_id"] for r in (relations.data or [])]

    if not student_ids:
        return {"payments": [], "total": 0}

    if student_id:
        if str(student_id) not in student_ids:
            raise HTTPException(status_code=403, detail="Access denied")
        student_ids = [str(student_id)]

    query = supabase.table("payments").select(
        "*, fee_record:fee_record_id(fee_types(name), student:student_id(first_name, last_name))"
    ).in_("student_id", student_ids)

    if start_date:
        query = query.gte("payment_date", start_date.isoformat())
    if end_date:
        query = query.lte("payment_date", end_date.isoformat())

    query = query.order("payment_date", desc=True).range(offset, offset + limit - 1)

    result = query.execute()

    return {
        "payments": result.data or [],
        "total": len(result.data) if result.data else 0,
        "limit": limit,
        "offset": offset
    }


@router.get("/receipts/{payment_id}")
async def get_payment_receipt(
    payment_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get payment receipt details"""
    parent_id = current_user.get("id")

    result = supabase.table("payments").select(
        "*, fee_record:fee_record_id(*, fee_types(name, category), student:student_id(first_name, last_name, student_number))"
    ).eq("id", str(payment_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Verify parent owns this payment
    student_id = result.data.get("student_id")
    relation = supabase.table("parent_student_relations").select("id").eq(
        "parent_id", parent_id
    ).eq("student_id", student_id).execute()

    if not relation.data:
        raise HTTPException(status_code=403, detail="Access denied")

    return result.data


# ============================================================
# MAKE PAYMENTS
# ============================================================

@router.post("/pay")
async def make_payment(
    payment: PaymentCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Make a payment towards a fee"""
    parent_id = current_user.get("id")
    school_id = current_user.get("school_id")

    # Get fee record
    fee = supabase.table("fee_records").select(
        "student_id, amount, amount_paid, status"
    ).eq("id", str(payment.fee_record_id)).single().execute()

    if not fee.data:
        raise HTTPException(status_code=404, detail="Fee record not found")

    # Verify parent owns student
    relation = supabase.table("parent_student_relations").select("id").eq(
        "parent_id", parent_id
    ).eq("student_id", fee.data["student_id"]).execute()

    if not relation.data:
        raise HTTPException(status_code=403, detail="Access denied")

    # Calculate remaining balance
    remaining = fee.data["amount"] - (fee.data["amount_paid"] or 0)
    if payment.amount > remaining:
        raise HTTPException(
            status_code=400,
            detail=f"Payment amount exceeds remaining balance of {remaining}"
        )

    # Create payment record
    payment_data = {
        "school_id": school_id,
        "fee_record_id": str(payment.fee_record_id),
        "student_id": fee.data["student_id"],
        "amount": payment.amount,
        "payment_method": payment.payment_method,
        "payment_date": date.today().isoformat(),
        "reference_number": payment.reference_number,
        "notes": payment.notes,
        "status": "completed",
        "paid_by": parent_id
    }

    result = supabase.table("payments").insert(payment_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to process payment")

    # Update fee record
    new_amount_paid = (fee.data["amount_paid"] or 0) + payment.amount
    new_status = "paid" if new_amount_paid >= fee.data["amount"] else "partial"

    supabase.table("fee_records").update({
        "amount_paid": new_amount_paid,
        "status": new_status
    }).eq("id", str(payment.fee_record_id)).execute()

    return {
        "payment": result.data[0],
        "fee_status": new_status,
        "remaining_balance": fee.data["amount"] - new_amount_paid
    }


# ============================================================
# PAYMENT PLANS
# ============================================================

@router.get("/plans")
async def get_payment_plans(
    student_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get active payment plans"""
    parent_id = current_user.get("id")

    # Get parent's children
    relations = supabase.table("parent_student_relations").select(
        "student_id"
    ).eq("parent_id", parent_id).execute()

    student_ids = [r["student_id"] for r in (relations.data or [])]

    if student_id:
        if str(student_id) not in student_ids:
            raise HTTPException(status_code=403, detail="Access denied")
        student_ids = [str(student_id)]

    result = supabase.table("payment_plans").select(
        "*, student:student_id(first_name, last_name), installments:payment_plan_installments(*)"
    ).in_("student_id", student_ids).eq("status", "active").execute()

    return {"payment_plans": result.data or []}


@router.get("/plans/{plan_id}/installments")
async def get_plan_installments(
    plan_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get installments for a payment plan"""
    parent_id = current_user.get("id")

    # Get plan
    plan = supabase.table("payment_plans").select("student_id").eq(
        "id", str(plan_id)
    ).single().execute()

    if not plan.data:
        raise HTTPException(status_code=404, detail="Payment plan not found")

    # Verify ownership
    relation = supabase.table("parent_student_relations").select("id").eq(
        "parent_id", parent_id
    ).eq("student_id", plan.data["student_id"]).execute()

    if not relation.data:
        raise HTTPException(status_code=403, detail="Access denied")

    installments = supabase.table("payment_plan_installments").select("*").eq(
        "plan_id", str(plan_id)
    ).order("due_date").execute()

    return {"installments": installments.data or []}


# ============================================================
# SAVED PAYMENT METHODS
# ============================================================

@router.get("/methods")
async def get_saved_payment_methods(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get saved payment methods"""
    parent_id = current_user.get("id")

    result = supabase.table("parent_payment_methods").select("*").eq(
        "parent_id", parent_id
    ).eq("is_active", True).execute()

    return {"payment_methods": result.data or []}


@router.post("/methods")
async def save_payment_method(
    method: PaymentMethodSave,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Save a payment method"""
    parent_id = current_user.get("id")

    # If setting as default, unset other defaults
    if method.is_default:
        supabase.table("parent_payment_methods").update({
            "is_default": False
        }).eq("parent_id", parent_id).execute()

    method_data = {
        "parent_id": parent_id,
        "method_type": method.method_type,
        "last_four": method.last_four,
        "card_brand": method.card_brand,
        "expiry_month": method.expiry_month,
        "expiry_year": method.expiry_year,
        "is_default": method.is_default,
        "nickname": method.nickname,
        "is_active": True
    }

    result = supabase.table("parent_payment_methods").insert(method_data).execute()

    return result.data[0] if result.data else None


@router.delete("/methods/{method_id}")
async def delete_payment_method(
    method_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a saved payment method"""
    parent_id = current_user.get("id")

    supabase.table("parent_payment_methods").update({
        "is_active": False
    }).eq("id", str(method_id)).eq("parent_id", parent_id).execute()

    return {"success": True}


# ============================================================
# STATEMENTS & INVOICES
# ============================================================

@router.get("/statements/{student_id}")
async def get_account_statement(
    student_id: UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get account statement for a student"""
    parent_id = current_user.get("id")

    # Verify ownership
    relation = supabase.table("parent_student_relations").select("id").eq(
        "parent_id", parent_id
    ).eq("student_id", str(student_id)).execute()

    if not relation.data:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get student info
    student = supabase.table("students").select(
        "first_name, last_name, student_number"
    ).eq("id", str(student_id)).single().execute()

    # Get fees
    fees_query = supabase.table("fee_records").select(
        "*, fee_types(name)"
    ).eq("student_id", str(student_id))

    if start_date:
        fees_query = fees_query.gte("created_at", start_date.isoformat())
    if end_date:
        fees_query = fees_query.lte("created_at", end_date.isoformat())

    fees_result = fees_query.order("created_at").execute()

    # Get payments
    payments_query = supabase.table("payments").select("*").eq(
        "student_id", str(student_id)
    )

    if start_date:
        payments_query = payments_query.gte("payment_date", start_date.isoformat())
    if end_date:
        payments_query = payments_query.lte("payment_date", end_date.isoformat())

    payments_result = payments_query.order("payment_date").execute()

    # Calculate totals
    total_charges = sum(f.get("amount", 0) for f in (fees_result.data or []))
    total_payments = sum(p.get("amount", 0) for p in (payments_result.data or []))

    return {
        "student": student.data,
        "period": {
            "start": start_date.isoformat() if start_date else None,
            "end": end_date.isoformat() if end_date else None
        },
        "fees": fees_result.data or [],
        "payments": payments_result.data or [],
        "summary": {
            "total_charges": total_charges,
            "total_payments": total_payments,
            "balance": total_charges - total_payments
        },
        "generated_at": datetime.utcnow().isoformat()
    }
