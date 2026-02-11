from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.core.auth import get_current_user
from app.db.supabase_client import get_supabase_client

router = APIRouter()

@router.get("/dashboard/priorities")
async def get_today_priorities(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "office_admin":
        raise HTTPException(status_code=403, detail="Office admin access required")
    
    supabase = get_supabase_client()
    school_id = current_user["school_id"]
    
    # Admissions awaiting verification (students with is_approved=false)
    pending_admissions = supabase.table("user_profiles").select("id", count="exact").eq("school_id", school_id).eq("role", "student").eq("is_approved", False).execute()
    
    # Students with missing documents (mock - would need documents table)
    missing_docs = 14
    
    # Payments to allocate (payments without proper invoice link - mock)
    pending_payments = 5
    
    # Proof of payment uploads (mock - would need uploads table)
    proof_uploads = 7
    
    # Transfer requests (students with status='transferred')
    transfers = supabase.table("students").select("id", count="exact").eq("school_id", school_id).eq("status", "transferred").execute()
    
    return {
        "admissions_pending": pending_admissions.count or 0,
        "missing_documents": missing_docs,
        "payments_to_allocate": pending_payments,
        "proof_uploads": proof_uploads,
        "transfer_requests": transfers.count or 0,
        "letters_requested": 6
    }

@router.get("/fees/snapshot")
async def get_fees_snapshot(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "office_admin":
        raise HTTPException(status_code=403, detail="Office admin access required")
    
    supabase = get_supabase_client()
    school_id = current_user["school_id"]
    
    # This month's collections
    first_day = datetime.now().replace(day=1).date().isoformat()
    payments = supabase.table("payments").select("amount").gte("created_at", first_day).execute()
    collected_this_month = sum(float(p["amount"]) for p in payments.data)
    
    # Outstanding balance
    invoices = supabase.table("invoices").select("amount, amount_paid").eq("school_id", school_id).execute()
    outstanding = sum(float(i["amount"]) - float(i["amount_paid"]) for i in invoices.data)
    
    # Overdue accounts
    today = datetime.now().date()
    overdue = sum(float(i["amount"]) - float(i["amount_paid"]) for i in invoices.data 
                  if datetime.fromisoformat(i.get("due_date", "9999-12-31").replace('Z', '+00:00')).date() < today 
                  and float(i["amount_paid"]) < float(i["amount"]))
    
    # Payment plans (mock - would need payment_plans table)
    payment_plans = 8
    
    return {
        "collected_this_month": round(collected_this_month, 2),
        "outstanding_balance": round(outstanding, 2),
        "overdue_amount": round(overdue, 2),
        "active_payment_plans": payment_plans
    }

@router.get("/students/snapshot")
async def get_students_snapshot(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "office_admin":
        raise HTTPException(status_code=403, detail="Office admin access required")
    
    supabase = get_supabase_client()
    school_id = current_user["school_id"]
    
    # Active students
    active = supabase.table("students").select("id", count="exact").eq("school_id", school_id).eq("status", "active").execute()
    
    # New admissions this month
    first_day = datetime.now().replace(day=1).date().isoformat()
    new_admissions = supabase.table("students").select("id", count="exact").eq("school_id", school_id).gte("admission_date", first_day).execute()
    
    # Pending transfers
    transfers = supabase.table("students").select("id", count="exact").eq("school_id", school_id).eq("status", "transferred").execute()
    
    # Inactive students
    inactive = supabase.table("students").select("id", count="exact").eq("school_id", school_id).eq("status", "inactive").execute()
    
    return {
        "total_active": active.count or 0,
        "new_this_month": new_admissions.count or 0,
        "pending_transfers": transfers.count or 0,
        "inactive_students": inactive.count or 0
    }

@router.get("/documents/compliance")
async def get_documents_compliance(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "office_admin":
        raise HTTPException(status_code=403, detail="Office admin access required")
    
    # Mock data - would need documents table
    return {
        "missing_birth_certificates": 9,
        "missing_parent_ids": 6,
        "missing_medical_forms": 11
    }

@router.get("/activity/recent")
async def get_recent_activity(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "office_admin":
        raise HTTPException(status_code=403, detail="Office admin access required")
    
    supabase = get_supabase_client()
    school_id = current_user["school_id"]
    
    # Get recent audit logs for office operations
    logs = supabase.table("audit_logs").select("action, entity_type, created_at").eq("school_id", school_id).order("created_at", desc=True).limit(10).execute()
    
    activities = []
    for log in logs.data:
        if log["entity_type"] in ["student", "payment", "invoice"]:
            activities.append({
                "action": log["action"],
                "time": log["created_at"]
            })
    
    return activities

@router.get("/exceptions")
async def get_exceptions(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "office_admin":
        raise HTTPException(status_code=403, detail="Office admin access required")
    
    # Mock data - would need proper exception tracking
    return [
        {"type": "duplicate_records", "message": "Duplicate student records detected", "count": 2},
        {"type": "unmatched_payment", "message": "Payment received without reference", "count": 1},
        {"type": "missing_invoice", "message": "Student assigned to class but not invoiced", "count": 3}
    ]
