"""
EduCore Backend - Refunds API
Process and manage fee refunds
"""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
import secrets

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# MODELS
# ============================================================

class RefundRequest(BaseModel):
    """Request a refund"""
    student_id: UUID
    payment_id: UUID
    reason: str
    amount: float
    notes: Optional[str] = None
    supporting_documents: List[str] = []


class RefundApproval(BaseModel):
    """Approve/reject a refund"""
    status: str  # approved, rejected
    approved_amount: Optional[float] = None
    notes: Optional[str] = None


class RefundProcess(BaseModel):
    """Process an approved refund"""
    refund_method: str  # bank_transfer, cash, check, credit_to_account
    reference_number: Optional[str] = None
    bank_details: Optional[dict] = None
    notes: Optional[str] = None


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("")
async def list_refunds(
    student_id: Optional[UUID] = None,
    status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List refund requests"""
    school_id = current_user.get("school_id")

    query = supabase.table("refunds").select(
        "*, students(first_name, last_name, student_number), fee_payments(amount, payment_date)"
    ).eq("school_id", school_id)

    if student_id:
        query = query.eq("student_id", str(student_id))
    if status:
        query = query.eq("status", status)
    if date_from:
        query = query.gte("requested_at", date_from.isoformat())
    if date_to:
        query = query.lte("requested_at", date_to.isoformat())

    query = query.order("requested_at", desc=True).range(offset, offset + limit - 1)

    result = query.execute()

    return {
        "refunds": result.data or [],
        "total": len(result.data) if result.data else 0,
        "limit": limit,
        "offset": offset
    }


@router.get("/pending")
async def list_pending_refunds(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List pending refund requests for approval"""
    school_id = current_user.get("school_id")

    result = supabase.table("refunds").select(
        "*, students(first_name, last_name, student_number), fee_payments(amount, payment_date, fee_structures(name))"
    ).eq("school_id", school_id).eq("status", "pending").order("requested_at").execute()

    return {
        "pending_refunds": result.data or [],
        "count": len(result.data) if result.data else 0
    }


@router.get("/{refund_id}")
async def get_refund(
    refund_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get refund details"""
    result = supabase.table("refunds").select(
        "*, students(first_name, last_name, student_number, class_id, classes(name)), fee_payments(amount, payment_date, payment_method, fee_structures(name))"
    ).eq("id", str(refund_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Refund not found")

    return result.data


@router.post("")
async def request_refund(
    refund: RefundRequest,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Submit a refund request"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    # Verify payment exists
    payment = supabase.table("fee_payments").select(
        "amount, student_id"
    ).eq("id", str(refund.payment_id)).single().execute()

    if not payment.data:
        raise HTTPException(status_code=404, detail="Payment not found")

    if str(payment.data["student_id"]) != str(refund.student_id):
        raise HTTPException(status_code=400, detail="Payment does not belong to this student")

    if refund.amount > payment.data["amount"]:
        raise HTTPException(status_code=400, detail="Refund amount exceeds payment amount")

    # Check for existing refund request
    existing = supabase.table("refunds").select("id, status").eq(
        "payment_id", str(refund.payment_id)
    ).not_.in_("status", ["rejected", "cancelled"]).execute()

    if existing.data:
        raise HTTPException(status_code=400, detail="A refund request already exists for this payment")

    # Generate refund reference
    refund_reference = f"REF-{secrets.token_hex(4).upper()}"

    refund_data = {
        "school_id": school_id,
        "student_id": str(refund.student_id),
        "payment_id": str(refund.payment_id),
        "refund_reference": refund_reference,
        "requested_amount": refund.amount,
        "reason": refund.reason,
        "notes": refund.notes,
        "supporting_documents": refund.supporting_documents,
        "requested_by": user_id,
        "requested_at": datetime.utcnow().isoformat(),
        "status": "pending"
    }

    result = supabase.table("refunds").insert(refund_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create refund request")

    return result.data[0]


@router.post("/{refund_id}/approve")
async def approve_refund(
    refund_id: UUID,
    approval: RefundApproval,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Approve or reject a refund request"""
    user_id = current_user["id"]

    refund = supabase.table("refunds").select(
        "status, requested_amount"
    ).eq("id", str(refund_id)).single().execute()

    if not refund.data:
        raise HTTPException(status_code=404, detail="Refund not found")

    if refund.data["status"] != "pending":
        raise HTTPException(status_code=400, detail="Refund is not pending approval")

    update_data = {
        "status": approval.status,
        "reviewed_by": user_id,
        "reviewed_at": datetime.utcnow().isoformat(),
        "review_notes": approval.notes
    }

    if approval.status == "approved":
        update_data["approved_amount"] = approval.approved_amount or refund.data["requested_amount"]
        update_data["status"] = "approved"
    else:
        update_data["status"] = "rejected"

    supabase.table("refunds").update(update_data).eq("id", str(refund_id)).execute()

    return {
        "success": True,
        "status": update_data["status"],
        "approved_amount": update_data.get("approved_amount")
    }


@router.post("/{refund_id}/process")
async def process_refund(
    refund_id: UUID,
    process: RefundProcess,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Process an approved refund"""
    user_id = current_user["id"]

    refund = supabase.table("refunds").select(
        "status, approved_amount, student_id"
    ).eq("id", str(refund_id)).single().execute()

    if not refund.data:
        raise HTTPException(status_code=404, detail="Refund not found")

    if refund.data["status"] != "approved":
        raise HTTPException(status_code=400, detail="Refund is not approved")

    update_data = {
        "status": "processed",
        "refund_method": process.refund_method,
        "refund_reference_number": process.reference_number,
        "bank_details": process.bank_details,
        "process_notes": process.notes,
        "processed_by": user_id,
        "processed_at": datetime.utcnow().isoformat()
    }

    supabase.table("refunds").update(update_data).eq("id", str(refund_id)).execute()

    # If credit to account, create a credit record
    if process.refund_method == "credit_to_account":
        credit_data = {
            "student_id": refund.data["student_id"],
            "amount": refund.data["approved_amount"],
            "reason": "Refund credit",
            "refund_id": str(refund_id),
            "created_by": user_id,
            "created_at": datetime.utcnow().isoformat()
        }
        supabase.table("student_credits").insert(credit_data).execute()

    return {
        "success": True,
        "status": "processed",
        "refund_amount": refund.data["approved_amount"],
        "method": process.refund_method
    }


@router.post("/{refund_id}/cancel")
async def cancel_refund(
    refund_id: UUID,
    reason: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Cancel a refund request"""
    user_id = current_user["id"]

    refund = supabase.table("refunds").select("status").eq(
        "id", str(refund_id)
    ).single().execute()

    if not refund.data:
        raise HTTPException(status_code=404, detail="Refund not found")

    if refund.data["status"] == "processed":
        raise HTTPException(status_code=400, detail="Cannot cancel a processed refund")

    supabase.table("refunds").update({
        "status": "cancelled",
        "cancellation_reason": reason,
        "cancelled_by": user_id,
        "cancelled_at": datetime.utcnow().isoformat()
    }).eq("id", str(refund_id)).execute()

    return {"success": True}


@router.get("/stats")
async def get_refund_stats(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get refund statistics"""
    school_id = current_user.get("school_id")

    query = supabase.table("refunds").select(
        "status, requested_amount, approved_amount, requested_at"
    ).eq("school_id", school_id)

    if date_from:
        query = query.gte("requested_at", date_from.isoformat())
    if date_to:
        query = query.lte("requested_at", date_to.isoformat())

    result = query.execute()

    refunds = result.data or []

    stats = {
        "total_requests": len(refunds),
        "by_status": {},
        "total_requested": 0,
        "total_approved": 0,
        "total_processed": 0,
        "average_processing_time_days": 0
    }

    for refund in refunds:
        status = refund.get("status", "pending")
        stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
        stats["total_requested"] += refund.get("requested_amount") or 0

        if status == "approved":
            stats["total_approved"] += refund.get("approved_amount") or 0
        elif status == "processed":
            stats["total_processed"] += refund.get("approved_amount") or 0

    return stats
