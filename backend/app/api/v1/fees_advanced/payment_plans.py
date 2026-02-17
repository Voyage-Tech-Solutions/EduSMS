"""
EduCore Backend - Payment Plans API
Flexible payment plans and installment management
"""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# MODELS
# ============================================================

class InstallmentSchedule(BaseModel):
    """Single installment in a payment plan"""
    due_date: date
    amount: float
    description: Optional[str] = None


class PaymentPlanTemplateCreate(BaseModel):
    """Create a payment plan template"""
    name: str
    description: Optional[str] = None
    number_of_installments: int
    installment_frequency: str = "monthly"  # monthly, bi_weekly, quarterly, custom
    down_payment_percent: float = 0
    late_fee_percent: float = 0
    late_fee_fixed: float = 0
    grace_period_days: int = 0
    auto_calculate_amounts: bool = True


class PaymentPlanCreate(BaseModel):
    """Create a payment plan for a student"""
    student_id: UUID
    fee_id: UUID
    template_id: Optional[UUID] = None
    total_amount: float
    start_date: date
    installments: Optional[List[InstallmentSchedule]] = None
    notes: Optional[str] = None


class InstallmentPayment(BaseModel):
    """Record payment for an installment"""
    amount: float
    payment_method: str  # cash, bank_transfer, card, mobile_money
    reference_number: Optional[str] = None
    notes: Optional[str] = None


# ============================================================
# TEMPLATE ENDPOINTS
# ============================================================

@router.get("/templates")
async def list_templates(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List available payment plan templates"""
    school_id = current_user.get("school_id")

    result = supabase.table("payment_plan_templates").select("*").eq(
        "school_id", school_id
    ).eq("is_active", True).order("name").execute()

    return {"templates": result.data or []}


@router.post("/templates")
async def create_template(
    template: PaymentPlanTemplateCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a payment plan template"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    template_data = {
        "school_id": school_id,
        "created_by": user_id,
        "name": template.name,
        "description": template.description,
        "number_of_installments": template.number_of_installments,
        "installment_frequency": template.installment_frequency,
        "down_payment_percent": template.down_payment_percent,
        "late_fee_percent": template.late_fee_percent,
        "late_fee_fixed": template.late_fee_fixed,
        "grace_period_days": template.grace_period_days,
        "auto_calculate_amounts": template.auto_calculate_amounts,
        "is_active": True
    }

    result = supabase.table("payment_plan_templates").insert(template_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create template")

    return result.data[0]


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a payment plan template"""
    supabase.table("payment_plan_templates").update({
        "is_active": False
    }).eq("id", str(template_id)).execute()

    return {"success": True}


# ============================================================
# PAYMENT PLAN ENDPOINTS
# ============================================================

@router.get("")
async def list_payment_plans(
    student_id: Optional[UUID] = None,
    status: Optional[str] = None,
    overdue_only: bool = False,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List payment plans with filters"""
    school_id = current_user.get("school_id")

    query = supabase.table("payment_plans").select(
        "*, students(first_name, last_name, student_number), fee_structures(name)"
    ).eq("school_id", school_id)

    if student_id:
        query = query.eq("student_id", str(student_id))
    if status:
        query = query.eq("status", status)

    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

    result = query.execute()

    plans = result.data or []

    # Get overdue installments
    for plan in plans:
        installments = supabase.table("payment_plan_installments").select(
            "id, due_date, amount, paid_amount, status"
        ).eq("payment_plan_id", plan["id"]).execute()

        plan["installments"] = installments.data or []

        # Calculate overdue
        today = date.today()
        overdue_count = 0
        overdue_amount = 0

        for inst in plan["installments"]:
            if inst["status"] != "paid" and inst["due_date"] < today.isoformat():
                overdue_count += 1
                overdue_amount += (inst["amount"] - (inst["paid_amount"] or 0))

        plan["overdue_count"] = overdue_count
        plan["overdue_amount"] = overdue_amount

    # Filter by overdue if requested
    if overdue_only:
        plans = [p for p in plans if p["overdue_count"] > 0]

    return {
        "payment_plans": plans,
        "total": len(plans),
        "limit": limit,
        "offset": offset
    }


@router.get("/{plan_id}")
async def get_payment_plan(
    plan_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get payment plan with full details"""
    result = supabase.table("payment_plans").select(
        "*, students(first_name, last_name, student_number), fee_structures(name), payment_plan_templates(name)"
    ).eq("id", str(plan_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Payment plan not found")

    plan = result.data

    # Get installments
    installments = supabase.table("payment_plan_installments").select(
        "*, payment_transactions(amount, payment_date, payment_method)"
    ).eq("payment_plan_id", str(plan_id)).order("due_date").execute()

    plan["installments"] = installments.data or []

    # Calculate totals
    total_paid = sum(
        inst.get("paid_amount") or 0 for inst in plan["installments"]
    )
    plan["total_paid"] = total_paid
    plan["remaining_balance"] = plan["total_amount"] - total_paid

    return plan


@router.post("")
async def create_payment_plan(
    plan: PaymentPlanCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a payment plan for a student"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    # Get template settings if provided
    template_settings = None
    if plan.template_id:
        template = supabase.table("payment_plan_templates").select("*").eq(
            "id", str(plan.template_id)
        ).single().execute()
        template_settings = template.data

    # Create payment plan
    plan_data = {
        "school_id": school_id,
        "created_by": user_id,
        "student_id": str(plan.student_id),
        "fee_id": str(plan.fee_id),
        "template_id": str(plan.template_id) if plan.template_id else None,
        "total_amount": plan.total_amount,
        "start_date": plan.start_date.isoformat(),
        "notes": plan.notes,
        "status": "active"
    }

    result = supabase.table("payment_plans").insert(plan_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create payment plan")

    payment_plan = result.data[0]
    plan_id = payment_plan["id"]

    # Create installments
    installments_to_create = []

    if plan.installments:
        # Use provided installments
        for idx, inst in enumerate(plan.installments):
            installments_to_create.append({
                "payment_plan_id": plan_id,
                "installment_number": idx + 1,
                "due_date": inst.due_date.isoformat(),
                "amount": inst.amount,
                "description": inst.description,
                "paid_amount": 0,
                "status": "pending"
            })
    elif template_settings and template_settings.get("auto_calculate_amounts"):
        # Auto-generate installments from template
        num_installments = template_settings["number_of_installments"]
        frequency = template_settings["installment_frequency"]
        down_payment_pct = template_settings.get("down_payment_percent", 0)

        # Calculate down payment
        down_payment = plan.total_amount * (down_payment_pct / 100)
        remaining = plan.total_amount - down_payment

        # Add down payment as first installment
        if down_payment > 0:
            installments_to_create.append({
                "payment_plan_id": plan_id,
                "installment_number": 1,
                "due_date": plan.start_date.isoformat(),
                "amount": down_payment,
                "description": "Down payment",
                "paid_amount": 0,
                "status": "pending"
            })
            num_installments -= 1

        # Calculate regular installment amount
        installment_amount = remaining / num_installments if num_installments > 0 else 0

        # Calculate dates based on frequency
        current_date = plan.start_date
        for i in range(num_installments):
            if frequency == "monthly":
                current_date = current_date + timedelta(days=30)
            elif frequency == "bi_weekly":
                current_date = current_date + timedelta(days=14)
            elif frequency == "quarterly":
                current_date = current_date + timedelta(days=90)
            else:
                current_date = current_date + timedelta(days=30)

            installments_to_create.append({
                "payment_plan_id": plan_id,
                "installment_number": len(installments_to_create) + 1,
                "due_date": current_date.isoformat(),
                "amount": round(installment_amount, 2),
                "description": f"Installment {len(installments_to_create) + 1}",
                "paid_amount": 0,
                "status": "pending"
            })

    if installments_to_create:
        supabase.table("payment_plan_installments").insert(installments_to_create).execute()

    return await get_payment_plan(UUID(plan_id), current_user, supabase)


@router.post("/{plan_id}/installments/{installment_id}/pay")
async def pay_installment(
    plan_id: UUID,
    installment_id: UUID,
    payment: InstallmentPayment,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Record payment for an installment"""
    user_id = current_user["id"]

    # Get installment
    installment = supabase.table("payment_plan_installments").select(
        "amount, paid_amount, status"
    ).eq("id", str(installment_id)).eq("payment_plan_id", str(plan_id)).single().execute()

    if not installment.data:
        raise HTTPException(status_code=404, detail="Installment not found")

    current_paid = installment.data.get("paid_amount") or 0
    remaining = installment.data["amount"] - current_paid

    if payment.amount > remaining:
        raise HTTPException(status_code=400, detail=f"Payment amount exceeds remaining balance ({remaining})")

    # Create transaction record
    transaction_data = {
        "installment_id": str(installment_id),
        "amount": payment.amount,
        "payment_method": payment.payment_method,
        "reference_number": payment.reference_number,
        "payment_date": datetime.utcnow().isoformat(),
        "recorded_by": user_id,
        "notes": payment.notes
    }

    supabase.table("payment_transactions").insert(transaction_data).execute()

    # Update installment
    new_paid = current_paid + payment.amount
    new_status = "paid" if new_paid >= installment.data["amount"] else "partial"

    supabase.table("payment_plan_installments").update({
        "paid_amount": new_paid,
        "status": new_status,
        "last_payment_date": datetime.utcnow().isoformat()
    }).eq("id", str(installment_id)).execute()

    # Check if plan is fully paid
    plan_installments = supabase.table("payment_plan_installments").select(
        "status"
    ).eq("payment_plan_id", str(plan_id)).execute()

    all_paid = all(i["status"] == "paid" for i in (plan_installments.data or []))

    if all_paid:
        supabase.table("payment_plans").update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat()
        }).eq("id", str(plan_id)).execute()

    return {
        "success": True,
        "amount_paid": payment.amount,
        "installment_status": new_status,
        "remaining_on_installment": installment.data["amount"] - new_paid
    }


@router.post("/{plan_id}/apply-late-fees")
async def apply_late_fees(
    plan_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Apply late fees to overdue installments"""
    # Get plan with template
    plan = supabase.table("payment_plans").select(
        "template_id, payment_plan_templates(late_fee_percent, late_fee_fixed, grace_period_days)"
    ).eq("id", str(plan_id)).single().execute()

    if not plan.data:
        raise HTTPException(status_code=404, detail="Payment plan not found")

    template = plan.data.get("payment_plan_templates", {})
    late_fee_percent = template.get("late_fee_percent", 0)
    late_fee_fixed = template.get("late_fee_fixed", 0)
    grace_period = template.get("grace_period_days", 0)

    if late_fee_percent == 0 and late_fee_fixed == 0:
        return {"success": True, "message": "No late fees configured", "fees_applied": 0}

    # Get overdue installments
    grace_date = date.today() - timedelta(days=grace_period)

    installments = supabase.table("payment_plan_installments").select(
        "id, amount, paid_amount, late_fee_applied"
    ).eq("payment_plan_id", str(plan_id)).neq("status", "paid").lt(
        "due_date", grace_date.isoformat()
    ).execute()

    fees_applied = 0
    for inst in (installments.data or []):
        if inst.get("late_fee_applied"):
            continue

        remaining = inst["amount"] - (inst["paid_amount"] or 0)
        late_fee = (remaining * late_fee_percent / 100) + late_fee_fixed

        supabase.table("payment_plan_installments").update({
            "amount": inst["amount"] + late_fee,
            "late_fee_applied": True,
            "late_fee_amount": late_fee
        }).eq("id", inst["id"]).execute()

        fees_applied += late_fee

    return {
        "success": True,
        "installments_updated": len(installments.data) if installments.data else 0,
        "total_fees_applied": round(fees_applied, 2)
    }


@router.delete("/{plan_id}")
async def cancel_payment_plan(
    plan_id: UUID,
    reason: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Cancel a payment plan"""
    supabase.table("payment_plans").update({
        "status": "cancelled",
        "cancellation_reason": reason,
        "cancelled_at": datetime.utcnow().isoformat()
    }).eq("id", str(plan_id)).execute()

    return {"success": True}
