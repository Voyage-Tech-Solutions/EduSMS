from fastapi import APIRouter, Depends
from typing import Optional
from pydantic import BaseModel
from app.core.auth import get_current_user, get_user_school_id
from app.db.supabase_client import get_supabase_admin

router = APIRouter()

class SchoolSettingsUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    timezone: Optional[str] = None
    currency: Optional[str] = None
    country: Optional[str] = None

class AttendanceSettingsUpdate(BaseModel):
    allow_future_dates: Optional[bool] = None
    late_cutoff_time: Optional[str] = None
    excused_requires_note: Optional[bool] = None
    default_status: Optional[str] = None
    auto_mark_absent: Optional[bool] = None

class BillingSettingsUpdate(BaseModel):
    invoice_prefix: Optional[str] = None
    default_due_days: Optional[int] = None
    allow_overpayment: Optional[bool] = None
    require_payment_proof: Optional[bool] = None
    collection_target: Optional[float] = None

@router.get("/school")
async def get_school_settings(
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    result = supabase.table("school_settings").select("*").eq("school_id", school_id).single().execute()
    return result.data

@router.patch("/school")
async def update_school_settings(
    settings: SchoolSettingsUpdate,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    data = {k: v for k, v in settings.dict().items() if v is not None}
    data["updated_by"] = user["id"]
    result = supabase.table("school_settings").update(data).eq("school_id", school_id).execute()
    return result.data[0]

@router.get("/attendance")
async def get_attendance_settings(
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    result = supabase.table("attendance_settings").select("*").eq("school_id", school_id).single().execute()
    return result.data

@router.patch("/attendance")
async def update_attendance_settings(
    settings: AttendanceSettingsUpdate,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    data = {k: v for k, v in settings.dict().items() if v is not None}
    result = supabase.table("attendance_settings").update(data).eq("school_id", school_id).execute()
    return result.data[0]

@router.get("/billing")
async def get_billing_settings(
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    result = supabase.table("billing_settings").select("*").eq("school_id", school_id).single().execute()
    return result.data

@router.patch("/billing")
async def update_billing_settings(
    settings: BillingSettingsUpdate,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_admin)
):
    school_id = get_user_school_id(user)
    data = {k: v for k, v in settings.dict().items() if v is not None}
    result = supabase.table("billing_settings").update(data).eq("school_id", school_id).execute()
    return result.data[0]
