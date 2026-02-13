"""
EduCore Backend - Student Transfers API
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

from app.core.security import get_current_user, require_office_admin
from app.db.supabase import supabase_admin

router = APIRouter(prefix="/transfers", tags=["Transfers"])


@router.get("/stats")
async def get_transfer_stats(current_user: dict = Depends(require_office_admin)):
    """Get transfer statistics"""
    school_id = current_user.get("school_id")
    
    if not supabase_admin:
        return {"pending": 0, "approved": 0, "completed": 0, "rejected": 0}
    
    result = supabase_admin.table("student_transfers").select("status", count="exact").eq("school_id", school_id).execute()
    
    stats = {"pending": 0, "approved": 0, "completed": 0, "rejected": 0}
    for transfer in result.data:
        stats[transfer["status"]] = stats.get(transfer["status"], 0) + 1
    
    return stats


@router.get("")
async def list_transfers(
    status_filter: Optional[str] = Query(None, alias="status"),
    transfer_type: Optional[str] = None,
    current_user: dict = Depends(require_office_admin),
):
    """List all transfers"""
    school_id = current_user.get("school_id")
    
    if not supabase_admin:
        return []
    
    query = supabase_admin.table("student_transfers").select("*, students(first_name, last_name, admission_number)").eq("school_id", school_id)
    
    if status_filter:
        query = query.eq("status", status_filter)
    if transfer_type:
        query = query.eq("transfer_type", transfer_type)
    
    result = query.order("created_at", desc=True).execute()
    return result.data


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_transfer(
    transfer_data: Dict[str, Any],
    current_user: dict = Depends(require_office_admin),
):
    """Create a new transfer request"""
    school_id = current_user.get("school_id")
    user_id = current_user.get("id")
    
    transfer_dict = {
        "school_id": school_id,
        "student_id": transfer_data["student_id"],
        "transfer_type": transfer_data["transfer_type"],
        "from_school": transfer_data.get("from_school"),
        "to_school": transfer_data.get("to_school"),
        "from_grade_id": transfer_data.get("from_grade_id"),
        "to_grade_id": transfer_data.get("to_grade_id"),
        "from_class_id": transfer_data.get("from_class_id"),
        "to_class_id": transfer_data.get("to_class_id"),
        "reason": transfer_data.get("reason"),
        "status": "pending",
        "requested_by": user_id,
    }
    
    if not supabase_admin:
        return {**transfer_dict, "id": str(uuid.uuid4())}
    
    result = supabase_admin.table("student_transfers").insert(transfer_dict).execute()
    return result.data[0]


@router.post("/{transfer_id}/approve")
async def approve_transfer(
    transfer_id: str,
    current_user: dict = Depends(require_office_admin),
):
    """Approve a transfer request"""
    school_id = current_user.get("school_id")
    user_id = current_user.get("id")
    
    if not supabase_admin:
        return {"id": transfer_id, "status": "approved"}
    
    result = supabase_admin.table("student_transfers").update({
        "status": "approved",
        "approved_by": user_id,
        "approved_at": datetime.now().isoformat()
    }).eq("id", transfer_id).eq("school_id", school_id).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Transfer not found")
    
    return result.data[0]


@router.post("/{transfer_id}/complete")
async def complete_transfer(
    transfer_id: str,
    current_user: dict = Depends(require_office_admin),
):
    """Complete a transfer (update student record)"""
    school_id = current_user.get("school_id")
    
    if not supabase_admin:
        return {"id": transfer_id, "status": "completed"}
    
    # Get transfer details
    transfer = supabase_admin.table("student_transfers").select("*").eq("id", transfer_id).eq("school_id", school_id).execute()
    if not transfer.data:
        raise HTTPException(status_code=404, detail="Transfer not found")
    
    t = transfer.data[0]
    
    # Update student record
    student_update = {}
    if t["transfer_type"] == "internal":
        if t["to_grade_id"]:
            student_update["grade_id"] = t["to_grade_id"]
        if t["to_class_id"]:
            student_update["class_id"] = t["to_class_id"]
    elif t["transfer_type"] == "outgoing":
        student_update["status"] = "transferred"
    
    if student_update:
        supabase_admin.table("students").update(student_update).eq("id", t["student_id"]).execute()
    
    # Mark transfer complete
    result = supabase_admin.table("student_transfers").update({
        "status": "completed",
        "completed_at": datetime.now().isoformat()
    }).eq("id", transfer_id).execute()
    
    # Log lifecycle event
    supabase_admin.table("student_lifecycle_events").insert({
        "school_id": school_id,
        "student_id": t["student_id"],
        "event_type": "transfer",
        "from_grade_id": t["from_grade_id"],
        "to_grade_id": t["to_grade_id"],
        "event_date": datetime.now().date().isoformat(),
        "reason": t["reason"],
        "recorded_by": current_user.get("id")
    }).execute()
    
    return result.data[0]


@router.post("/{transfer_id}/reject")
async def reject_transfer(
    transfer_id: str,
    rejection_data: Dict[str, Any],
    current_user: dict = Depends(require_office_admin),
):
    """Reject a transfer request"""
    school_id = current_user.get("school_id")
    
    if not supabase_admin:
        return {"id": transfer_id, "status": "rejected"}
    
    result = supabase_admin.table("student_transfers").update({
        "status": "rejected",
        "notes": rejection_data.get("notes", "")
    }).eq("id", transfer_id).eq("school_id", school_id).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Transfer not found")
    
    return result.data[0]
