"""
EduCore Backend - Financial Reports API
Generate financial reports and analytics
"""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/summary")
async def get_financial_summary(
    academic_year_id: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get overall financial summary"""
    school_id = current_user.get("school_id")

    # Get total fees billed
    fees_query = supabase.table("student_fees").select("amount").eq("school_id", school_id)
    if academic_year_id:
        fees_query = fees_query.eq("academic_year_id", str(academic_year_id))
    fees_result = fees_query.execute()
    total_billed = sum(f.get("amount") or 0 for f in (fees_result.data or []))

    # Get total payments
    payments_query = supabase.table("fee_payments").select("amount, payment_date").eq("school_id", school_id)
    if date_from:
        payments_query = payments_query.gte("payment_date", date_from.isoformat())
    if date_to:
        payments_query = payments_query.lte("payment_date", date_to.isoformat())
    payments_result = payments_query.execute()
    total_collected = sum(p.get("amount") or 0 for p in (payments_result.data or []))

    # Get scholarships disbursed
    scholarships_query = supabase.table("student_scholarships").select("award_amount").eq(
        "school_id", school_id
    ).eq("status", "active")
    if academic_year_id:
        scholarships_query = scholarships_query.eq("academic_year_id", str(academic_year_id))
    scholarships_result = scholarships_query.execute()
    total_scholarships = sum(s.get("award_amount") or 0 for s in (scholarships_result.data or []))

    # Get refunds processed
    refunds_query = supabase.table("refunds").select("approved_amount").eq(
        "school_id", school_id
    ).eq("status", "processed")
    if date_from:
        refunds_query = refunds_query.gte("processed_at", date_from.isoformat())
    if date_to:
        refunds_query = refunds_query.lte("processed_at", date_to.isoformat())
    refunds_result = refunds_query.execute()
    total_refunds = sum(r.get("approved_amount") or 0 for r in (refunds_result.data or []))

    return {
        "total_billed": total_billed,
        "total_collected": total_collected,
        "collection_rate": round(total_collected / total_billed * 100, 1) if total_billed > 0 else 0,
        "outstanding_balance": total_billed - total_collected,
        "total_scholarships": total_scholarships,
        "total_refunds": total_refunds,
        "net_revenue": total_collected - total_refunds
    }


@router.get("/collection-report")
async def get_collection_report(
    period: str = "monthly",  # daily, weekly, monthly, yearly
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get fee collection report by period"""
    school_id = current_user.get("school_id")

    # Default date range
    if not date_to:
        date_to = date.today()
    if not date_from:
        if period == "daily":
            date_from = date_to - timedelta(days=30)
        elif period == "weekly":
            date_from = date_to - timedelta(weeks=12)
        elif period == "monthly":
            date_from = date_to - timedelta(days=365)
        else:
            date_from = date_to - timedelta(days=365 * 3)

    # Get payments
    payments = supabase.table("fee_payments").select(
        "amount, payment_date, payment_method"
    ).eq("school_id", school_id).gte(
        "payment_date", date_from.isoformat()
    ).lte("payment_date", date_to.isoformat()).execute()

    # Group by period
    collection_data = {}
    method_totals = {}

    for payment in (payments.data or []):
        pdate = date.fromisoformat(payment["payment_date"])

        if period == "daily":
            key = pdate.isoformat()
        elif period == "weekly":
            week_start = pdate - timedelta(days=pdate.weekday())
            key = week_start.isoformat()
        elif period == "monthly":
            key = f"{pdate.year}-{pdate.month:02d}"
        else:
            key = str(pdate.year)

        if key not in collection_data:
            collection_data[key] = {"total": 0, "count": 0}
        collection_data[key]["total"] += payment.get("amount") or 0
        collection_data[key]["count"] += 1

        # Track by method
        method = payment.get("payment_method", "other")
        method_totals[method] = method_totals.get(method, 0) + (payment.get("amount") or 0)

    # Sort and format
    sorted_data = sorted(collection_data.items())

    return {
        "period": period,
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "collection_by_period": [
            {"period": k, "total": round(v["total"], 2), "transaction_count": v["count"]}
            for k, v in sorted_data
        ],
        "by_payment_method": method_totals,
        "grand_total": sum(v["total"] for v in collection_data.values())
    }


@router.get("/outstanding-report")
async def get_outstanding_report(
    class_id: Optional[UUID] = None,
    grade_id: Optional[UUID] = None,
    min_amount: Optional[float] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get outstanding fees report by student"""
    school_id = current_user.get("school_id")

    # Get all students with their fees
    students_query = supabase.table("students").select(
        "id, first_name, last_name, student_number, class_id, classes(name)"
    ).eq("school_id", school_id).eq("status", "active")

    if class_id:
        students_query = students_query.eq("class_id", str(class_id))

    students_result = students_query.execute()

    outstanding_list = []

    for student in (students_result.data or []):
        # Get total fees
        fees = supabase.table("student_fees").select("amount").eq(
            "student_id", student["id"]
        ).execute()
        total_fees = sum(f.get("amount") or 0 for f in (fees.data or []))

        # Get total payments
        payments = supabase.table("fee_payments").select("amount").eq(
            "student_id", student["id"]
        ).execute()
        total_paid = sum(p.get("amount") or 0 for p in (payments.data or []))

        # Get scholarships
        scholarships = supabase.table("student_scholarships").select("award_amount").eq(
            "student_id", student["id"]
        ).eq("status", "active").execute()
        total_scholarship = sum(s.get("award_amount") or 0 for s in (scholarships.data or []))

        outstanding = total_fees - total_paid - total_scholarship

        if outstanding > 0:
            if min_amount is None or outstanding >= min_amount:
                outstanding_list.append({
                    "student_id": student["id"],
                    "student_name": f"{student['first_name']} {student['last_name']}",
                    "student_number": student["student_number"],
                    "class_name": student.get("classes", {}).get("name"),
                    "total_fees": total_fees,
                    "total_paid": total_paid,
                    "scholarship_applied": total_scholarship,
                    "outstanding_balance": outstanding
                })

    # Sort by outstanding amount descending
    outstanding_list.sort(key=lambda x: x["outstanding_balance"], reverse=True)

    return {
        "students_with_outstanding": outstanding_list,
        "total_students": len(outstanding_list),
        "total_outstanding": sum(s["outstanding_balance"] for s in outstanding_list)
    }


@router.get("/payment-plan-status")
async def get_payment_plan_status(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get payment plan status overview"""
    school_id = current_user.get("school_id")

    # Get all payment plans
    plans = supabase.table("payment_plans").select(
        "id, status, total_amount, students(first_name, last_name)"
    ).eq("school_id", school_id).execute()

    today = date.today()

    stats = {
        "total_plans": len(plans.data) if plans.data else 0,
        "active": 0,
        "completed": 0,
        "cancelled": 0,
        "with_overdue": 0,
        "total_plan_value": 0,
        "total_collected": 0,
        "overdue_amount": 0
    }

    plans_with_issues = []

    for plan in (plans.data or []):
        stats[plan["status"]] = stats.get(plan["status"], 0) + 1
        stats["total_plan_value"] += plan.get("total_amount") or 0

        if plan["status"] == "active":
            # Get installments
            installments = supabase.table("payment_plan_installments").select(
                "due_date, amount, paid_amount, status"
            ).eq("payment_plan_id", plan["id"]).execute()

            collected = sum(i.get("paid_amount") or 0 for i in (installments.data or []))
            stats["total_collected"] += collected

            # Check for overdue
            has_overdue = False
            overdue_total = 0
            for inst in (installments.data or []):
                if inst["status"] != "paid" and inst["due_date"] < today.isoformat():
                    has_overdue = True
                    overdue_total += (inst["amount"] - (inst["paid_amount"] or 0))

            if has_overdue:
                stats["with_overdue"] += 1
                stats["overdue_amount"] += overdue_total
                plans_with_issues.append({
                    "plan_id": plan["id"],
                    "student_name": f"{plan['students']['first_name']} {plan['students']['last_name']}",
                    "overdue_amount": overdue_total
                })

    return {
        "summary": stats,
        "plans_with_overdue": plans_with_issues
    }


@router.get("/scholarship-report")
async def get_scholarship_report(
    academic_year_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get scholarship distribution report"""
    school_id = current_user.get("school_id")

    # Get scholarships
    scholarships_query = supabase.table("scholarships").select(
        "id, name, scholarship_type, amount, percentage"
    ).eq("school_id", school_id).eq("is_active", True)

    scholarships = scholarships_query.execute()

    report = []

    for sch in (scholarships.data or []):
        # Get awards for this scholarship
        awards_query = supabase.table("student_scholarships").select(
            "award_amount, status"
        ).eq("scholarship_id", sch["id"])

        if academic_year_id:
            awards_query = awards_query.eq("academic_year_id", str(academic_year_id))

        awards = awards_query.execute()

        active_awards = [a for a in (awards.data or []) if a["status"] == "active"]

        report.append({
            "scholarship_id": sch["id"],
            "name": sch["name"],
            "type": sch["scholarship_type"],
            "standard_amount": sch.get("amount"),
            "standard_percentage": sch.get("percentage"),
            "total_recipients": len(active_awards),
            "total_disbursed": sum(a.get("award_amount") or 0 for a in active_awards)
        })

    # Calculate totals
    total_disbursed = sum(r["total_disbursed"] for r in report)
    total_recipients = sum(r["total_recipients"] for r in report)

    return {
        "scholarships": report,
        "total_scholarships": len(report),
        "total_recipients": total_recipients,
        "total_amount_disbursed": total_disbursed
    }


@router.get("/daily-transactions")
async def get_daily_transactions(
    transaction_date: Optional[date] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get all transactions for a specific day"""
    school_id = current_user.get("school_id")

    if not transaction_date:
        transaction_date = date.today()

    # Get payments
    payments = supabase.table("fee_payments").select(
        "id, amount, payment_method, payment_date, reference_number, students(first_name, last_name, student_number), fee_structures(name)"
    ).eq("school_id", school_id).eq("payment_date", transaction_date.isoformat()).execute()

    # Get refunds processed
    refunds = supabase.table("refunds").select(
        "id, approved_amount, refund_method, processed_at, students(first_name, last_name)"
    ).eq("school_id", school_id).gte(
        "processed_at", f"{transaction_date}T00:00:00"
    ).lt("processed_at", f"{transaction_date + timedelta(days=1)}T00:00:00").execute()

    total_receipts = sum(p.get("amount") or 0 for p in (payments.data or []))
    total_refunds = sum(r.get("approved_amount") or 0 for r in (refunds.data or []))

    return {
        "date": transaction_date.isoformat(),
        "payments": payments.data or [],
        "payment_count": len(payments.data) if payments.data else 0,
        "total_receipts": total_receipts,
        "refunds": refunds.data or [],
        "refund_count": len(refunds.data) if refunds.data else 0,
        "total_refunds": total_refunds,
        "net_collection": total_receipts - total_refunds
    }


@router.get("/fee-type-breakdown")
async def get_fee_type_breakdown(
    academic_year_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get revenue breakdown by fee type"""
    school_id = current_user.get("school_id")

    # Get fee structures
    fees = supabase.table("fee_structures").select(
        "id, name, category"
    ).eq("school_id", school_id).execute()

    breakdown = []

    for fee in (fees.data or []):
        # Get billed amount
        billed_query = supabase.table("student_fees").select("amount").eq("fee_structure_id", fee["id"])
        if academic_year_id:
            billed_query = billed_query.eq("academic_year_id", str(academic_year_id))
        billed = billed_query.execute()
        total_billed = sum(b.get("amount") or 0 for b in (billed.data or []))

        # Get collected amount
        collected_query = supabase.table("fee_payments").select("amount").eq("fee_structure_id", fee["id"])
        collected = collected_query.execute()
        total_collected = sum(c.get("amount") or 0 for c in (collected.data or []))

        if total_billed > 0 or total_collected > 0:
            breakdown.append({
                "fee_id": fee["id"],
                "fee_name": fee["name"],
                "category": fee.get("category"),
                "total_billed": total_billed,
                "total_collected": total_collected,
                "collection_rate": round(total_collected / total_billed * 100, 1) if total_billed > 0 else 0,
                "outstanding": total_billed - total_collected
            })

    # Sort by collected amount
    breakdown.sort(key=lambda x: x["total_collected"], reverse=True)

    return {
        "breakdown": breakdown,
        "total_billed": sum(b["total_billed"] for b in breakdown),
        "total_collected": sum(b["total_collected"] for b in breakdown)
    }
