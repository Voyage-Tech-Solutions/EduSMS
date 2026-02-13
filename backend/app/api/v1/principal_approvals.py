from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
from app.models.principal import ApprovalRequest, ApprovalDecision, ApprovalRow
from app.core.auth import get_current_user, get_user_school_id
from app.db.supabase import get_supabase_admin

router = APIRouter(prefix="/principal/approvals", tags=["principal-approvals"])

@router.get("/summary")
async def get_approvals_summary(
    current_user: dict = Depends(get_current_user)
):
    """Get approval summary"""
    try:
        supabase = get_supabase_admin()
        school_id = get_user_school_id(current_user)
        
        pending = supabase.table("approval_requests").select("id", count="exact").eq(
            "school_id", school_id
        ).eq("status", "pending").execute()
        
        return {
            "total_pending": pending.count or 0,
            "high_priority": 0,
            "by_type": {}
        }
    except Exception as e:
        print(f"Error in get_approvals_summary: {str(e)}")
        return {
            "total_pending": 0,
            "high_priority": 0,
            "by_type": {}
        }

@router.get("")
async def get_approvals(
    status: str = "pending",
    type: Optional[str] = None,
    priority: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get approval requests"""
    supabase = get_supabase_admin()
    school_id = get_user_school_id(current_user)
    
    query = supabase.table("approval_requests").select("""
        *, 
        user_profiles!approval_requests_requested_by_fkey(first_name, last_name)
    """).eq("school_id", school_id).eq("status", status)
    
    if type:
        query = query.eq("type", type)
    if priority:
        query = query.eq("priority", priority)
    
    result = query.order("submitted_at", desc=True).execute()
    
    # Format approvals
    approvals = []
    for approval in result.data:
        # Get entity name based on type
        entity_name = await _get_entity_name(supabase, approval["entity_type"], approval["entity_id"])
        
        # Calculate priority
        days_pending = (datetime.now() - datetime.fromisoformat(approval["submitted_at"].replace('Z', '+00:00'))).days
        calculated_priority = approval["priority"]
        if days_pending > 7:
            calculated_priority = "high"
        
        approvals.append({
            "id": approval["id"],
            "request_id": approval["id"][:8],
            "type": approval["type"],
            "entity_name": entity_name,
            "description": approval.get("metadata", {}).get("description", ""),
            "priority": calculated_priority,
            "submitted_by": f"{approval['user_profiles']['first_name']} {approval['user_profiles']['last_name']}",
            "submitted_at": approval["submitted_at"],
            "status": approval["status"]
        })
    
    # Summary stats
    total_pending = len(approvals)
    high_priority = len([a for a in approvals if a["priority"] in ["high", "urgent"]])
    
    # Count by type
    by_type = {}
    for approval in approvals:
        by_type[approval["type"]] = by_type.get(approval["type"], 0) + 1
    
    return {
        "summary": {
            "total_pending": total_pending,
            "high_priority": high_priority,
            "by_type": by_type
        },
        "approvals": approvals
    }

@router.get("/{approval_id}")
async def get_approval_details(
    approval_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """Get approval details"""
    supabase = get_supabase_admin()
    school_id = get_user_school_id(current_user)
    
    approval = supabase.table("approval_requests").select("*").eq(
        "id", str(approval_id)
    ).eq("school_id", school_id).single().execute()
    
    # Get entity details based on type
    entity_details = await _get_entity_details(supabase, approval.data["entity_type"], approval.data["entity_id"])
    
    return {
        "approval": approval.data,
        "entity_details": entity_details
    }

@router.post("/{approval_id}/decision")
async def make_approval_decision(
    approval_id: UUID,
    decision: ApprovalDecision,
    current_user: dict = Depends(get_current_user)
):
    """Approve or reject request"""
    supabase = get_supabase_admin()
    school_id = get_user_school_id(current_user)
    
    # Get approval
    approval = supabase.table("approval_requests").select("*").eq(
        "id", str(approval_id)
    ).eq("school_id", school_id).single().execute()
    
    if not approval.data:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    # Validate decision
    if decision.decision not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid decision")
    
    if decision.decision == "rejected" and not decision.notes:
        raise HTTPException(status_code=400, detail="Notes required for rejection")
    
    # Update approval
    result = supabase.table("approval_requests").update({
        "status": decision.decision,
        "decision": decision.decision,
        "decided_by": current_user["id"],
        "decided_at": datetime.now().isoformat(),
        "notes": decision.notes
    }).eq("id", str(approval_id)).execute()
    
    # Execute approval action
    if decision.decision == "approved":
        await _execute_approval_action(supabase, school_id, approval.data)
    
    # Log audit
    supabase.table("audit_logs").insert({
        "school_id": school_id,
        "user_id": current_user["id"],
        "action": f"approval_{decision.decision}",
        "entity_type": "approval_request",
        "entity_id": str(approval_id),
        "after_state": {
            "decision": decision.decision,
            "notes": decision.notes
        }
    }).execute()
    
    # Send notifications if requested
    if decision.notify_requester:
        # Queue notification to requester
        pass
    
    return {"message": f"Approval {decision.decision} successfully"}

@router.get("/stats")
async def get_approval_stats(
    current_user: dict = Depends(get_current_user)
):
    """Get approval statistics"""
    supabase = get_supabase_admin()
    school_id = get_user_school_id(current_user)
    
    # Get counts
    pending = supabase.table("approval_requests").select("id", count="exact").eq(
        "school_id", school_id
    ).eq("status", "pending").execute()
    
    approved_today = supabase.table("approval_requests").select("id", count="exact").eq(
        "school_id", school_id
    ).eq("status", "approved").gte("decided_at", datetime.now().date().isoformat()).execute()
    
    # Average approval time
    recent_approved = supabase.table("approval_requests").select(
        "submitted_at, decided_at"
    ).eq("school_id", school_id).eq("status", "approved").limit(50).execute()
    
    avg_time = 0
    if recent_approved.data:
        times = []
        for approval in recent_approved.data:
            submitted = datetime.fromisoformat(approval["submitted_at"].replace('Z', '+00:00'))
            decided = datetime.fromisoformat(approval["decided_at"].replace('Z', '+00:00'))
            times.append((decided - submitted).total_seconds() / 3600)
        avg_time = sum(times) / len(times)
    
    return {
        "pending_count": pending.count,
        "approved_today": approved_today.count,
        "avg_approval_time_hours": round(avg_time, 1)
    }

# Helper functions
async def _get_entity_name(supabase, entity_type: str, entity_id: str) -> str:
    """Get entity name based on type"""
    if entity_type == "student":
        result = supabase.table("students").select("first_name, last_name").eq("id", entity_id).single().execute()
        return f"{result.data['first_name']} {result.data['last_name']}"
    elif entity_type == "user":
        result = supabase.table("user_profiles").select("first_name, last_name").eq("id", entity_id).single().execute()
        return f"{result.data['first_name']} {result.data['last_name']}"
    elif entity_type == "invoice":
        result = supabase.table("invoices").select("invoice_number").eq("id", entity_id).single().execute()
        return result.data["invoice_number"]
    return "Unknown"

async def _get_entity_details(supabase, entity_type: str, entity_id: str) -> dict:
    """Get full entity details"""
    if entity_type == "student":
        return supabase.table("students").select("*").eq("id", entity_id).single().execute().data
    elif entity_type == "user":
        return supabase.table("user_profiles").select("*").eq("id", entity_id).single().execute().data
    elif entity_type == "invoice":
        return supabase.table("invoices").select("*").eq("id", entity_id).single().execute().data
    return {}

async def _execute_approval_action(supabase, school_id: str, approval: dict):
    """Execute the approved action"""
    approval_type = approval["type"]
    entity_id = approval["entity_id"]
    metadata = approval.get("metadata", {})
    
    if approval_type == "admission":
        # Approve admission application
        supabase.table("admissions_applications").update({
            "status": "approved"
        }).eq("id", entity_id).execute()
        
    elif approval_type == "transfer":
        # Approve transfer
        supabase.table("students").update({
            "status": "transferred"
        }).eq("id", entity_id).execute()
        
    elif approval_type == "writeoff":
        # Apply write-off
        supabase.table("invoice_adjustments").insert({
            "invoice_id": entity_id,
            "adjustment_type": "writeoff",
            "amount": metadata.get("amount"),
            "reason": metadata.get("reason"),
            "approved_by": approval["decided_by"]
        }).execute()
        
    elif approval_type == "payment_plan":
        # Approve payment plan
        supabase.table("payment_plans").update({
            "status": "active"
        }).eq("id", entity_id).execute()
        
    elif approval_type == "role_change":
        # Change user role
        supabase.table("user_profiles").update({
            "role": metadata.get("new_role")
        }).eq("id", entity_id).execute()
