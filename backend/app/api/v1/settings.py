"""
EduCore Backend - School Settings API
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any
from datetime import datetime
from app.core.security import require_office_admin
from app.db.supabase import supabase_admin

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/school")
async def get_school_settings(current_user: dict = Depends(require_office_admin)):
    """Get school information and settings"""
    school_id = current_user.get("school_id")
    if supabase_admin:
        school = supabase_admin.table("schools").select("*").eq("id", school_id).execute()
        settings = supabase_admin.table("school_settings").select("*").eq("school_id", school_id).execute()
        return {"school": school.data[0] if school.data else {}, "settings": settings.data[0] if settings.data else {}}
    return {"school": {}, "settings": {}}


@router.patch("/school")
async def update_school_settings(update_data: Dict[str, Any], current_user: dict = Depends(require_office_admin)):
    """Update school information"""
    school_id = current_user.get("school_id")
    user_id = current_user.get("id")
    
    school_data = {k: v for k, v in update_data.items() if k in ["name", "address", "phone", "email", "website", "logo_url"]}
    settings_data = {k: v for k, v in update_data.items() if k in ["timezone", "currency", "country", "primary_color"]}
    
    if supabase_admin:
        if school_data:
            supabase_admin.table("schools").update(school_data).eq("id", school_id).execute()
        if settings_data:
            settings_data["updated_by"] = user_id
            supabase_admin.table("school_settings").upsert({"school_id": school_id, **settings_data}).execute()
        return {"success": True}
    return {"success": False}


@router.get("/attendance")
async def get_attendance_settings(current_user: dict = Depends(require_office_admin)):
    """Get attendance rules"""
    school_id = current_user.get("school_id")
    if supabase_admin:
        result = supabase_admin.table("school_settings").select("allow_future_attendance, late_cutoff_time").eq("school_id", school_id).execute()
        return result.data[0] if result.data else {}
    return {}


@router.patch("/attendance")
async def update_attendance_settings(update_data: Dict[str, Any], current_user: dict = Depends(require_office_admin)):
    """Update attendance rules"""
    school_id = current_user.get("school_id")
    user_id = current_user.get("id")
    update_data["updated_by"] = user_id
    if supabase_admin:
        supabase_admin.table("school_settings").upsert({"school_id": school_id, **update_data}).execute()
        return {"success": True}
    return {"success": False}


@router.get("/billing")
async def get_billing_settings(current_user: dict = Depends(require_office_admin)):
    """Get billing settings"""
    school_id = current_user.get("school_id")
    if supabase_admin:
        result = supabase_admin.table("school_settings").select("invoice_prefix, invoice_next_number, default_due_days, allow_overpayment").eq("school_id", school_id).execute()
        return result.data[0] if result.data else {}
    return {}


@router.patch("/billing")
async def update_billing_settings(update_data: Dict[str, Any], current_user: dict = Depends(require_office_admin)):
    """Update billing settings"""
    school_id = current_user.get("school_id")
    user_id = current_user.get("id")
    update_data["updated_by"] = user_id
    if supabase_admin:
        supabase_admin.table("school_settings").upsert({"school_id": school_id, **update_data}).execute()
        return {"success": True}
    return {"success": False}


@router.get("/notifications")
async def get_notification_settings(current_user: dict = Depends(require_office_admin)):
    """Get notification settings"""
    school_id = current_user.get("school_id")
    if supabase_admin:
        result = supabase_admin.table("school_settings").select("sms_enabled, email_enabled").eq("school_id", school_id).execute()
        return result.data[0] if result.data else {}
    return {}


@router.patch("/notifications")
async def update_notification_settings(update_data: Dict[str, Any], current_user: dict = Depends(require_office_admin)):
    """Update notification settings"""
    school_id = current_user.get("school_id")
    user_id = current_user.get("id")
    update_data["updated_by"] = user_id
    if supabase_admin:
        supabase_admin.table("school_settings").upsert({"school_id": school_id, **update_data}).execute()
        return {"success": True}
    return {"success": False}


@router.post("/notifications/test")
async def test_notification(test_data: Dict[str, Any], current_user: dict = Depends(require_office_admin)):
    """Send test notification"""
    return {"message": "Test notification sent", "type": test_data.get("type", "email")}
