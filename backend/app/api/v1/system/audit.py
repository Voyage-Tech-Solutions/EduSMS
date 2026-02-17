"""
EduCore Backend - Audit Logging API
Track and query system audit logs
"""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime, timedelta
from enum import Enum

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


class AuditAction(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    IMPORT = "import"
    APPROVE = "approve"
    REJECT = "reject"
    SEND = "send"


class AuditResource(str, Enum):
    USER = "user"
    STUDENT = "student"
    TEACHER = "teacher"
    CLASS = "class"
    GRADE = "grade"
    ATTENDANCE = "attendance"
    FEE = "fee"
    PAYMENT = "payment"
    DOCUMENT = "document"
    ANNOUNCEMENT = "announcement"
    MESSAGE = "message"
    REPORT = "report"
    SETTING = "setting"


class AuditLogCreate(BaseModel):
    """Create an audit log entry"""
    action: AuditAction
    resource_type: AuditResource
    resource_id: Optional[str] = None
    description: str
    old_value: Optional[dict] = None
    new_value: Optional[dict] = None
    metadata: Optional[dict] = None


# ============================================================
# AUDIT LOG QUERY
# ============================================================

@router.get("")
async def query_audit_logs(
    action: Optional[AuditAction] = None,
    resource_type: Optional[AuditResource] = None,
    resource_id: Optional[str] = None,
    user_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    ip_address: Optional[str] = None,
    limit: int = Query(default=50, le=500),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Query audit logs with filters"""
    school_id = current_user.get("school_id")
    user_role = current_user.get("role")

    # Only admins can view audit logs
    if user_role not in ["system_admin", "school_admin", "principal"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    query = supabase.table("audit_logs").select(
        "*, user:user_id(first_name, last_name, email, role)"
    ).eq("school_id", school_id)

    if action:
        query = query.eq("action", action.value)
    if resource_type:
        query = query.eq("resource_type", resource_type.value)
    if resource_id:
        query = query.eq("resource_id", resource_id)
    if user_id:
        query = query.eq("user_id", str(user_id))
    if start_date:
        query = query.gte("created_at", start_date.isoformat())
    if end_date:
        query = query.lte("created_at", end_date.isoformat())
    if ip_address:
        query = query.eq("ip_address", ip_address)

    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

    result = query.execute()

    # Get total count
    count_query = supabase.table("audit_logs").select("id", count="exact").eq("school_id", school_id)
    if action:
        count_query = count_query.eq("action", action.value)
    count_result = count_query.execute()

    return {
        "logs": result.data or [],
        "total": count_result.count or 0,
        "limit": limit,
        "offset": offset
    }


@router.get("/summary")
async def get_audit_summary(
    days: int = 7,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get audit log summary statistics"""
    school_id = current_user.get("school_id")
    start_date = datetime.utcnow() - timedelta(days=days)

    result = supabase.table("audit_logs").select(
        "action, resource_type, user_id"
    ).eq("school_id", school_id).gte("created_at", start_date.isoformat()).execute()

    logs = result.data or []

    # Group by action
    by_action = {}
    for log in logs:
        action = log.get("action", "unknown")
        by_action[action] = by_action.get(action, 0) + 1

    # Group by resource
    by_resource = {}
    for log in logs:
        resource = log.get("resource_type", "unknown")
        by_resource[resource] = by_resource.get(resource, 0) + 1

    # Group by user
    by_user = {}
    for log in logs:
        user = log.get("user_id", "unknown")
        by_user[user] = by_user.get(user, 0) + 1

    # Top users
    top_users = sorted(by_user.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "period_days": days,
        "total_events": len(logs),
        "by_action": by_action,
        "by_resource": by_resource,
        "top_active_users": [{"user_id": u[0], "events": u[1]} for u in top_users]
    }


@router.get("/user/{user_id}")
async def get_user_audit_trail(
    user_id: UUID,
    days: int = 30,
    limit: int = Query(default=100, le=500),
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get audit trail for a specific user"""
    school_id = current_user.get("school_id")
    start_date = datetime.utcnow() - timedelta(days=days)

    result = supabase.table("audit_logs").select("*").eq(
        "school_id", school_id
    ).eq("user_id", str(user_id)).gte(
        "created_at", start_date.isoformat()
    ).order("created_at", desc=True).limit(limit).execute()

    return {"logs": result.data or [], "user_id": str(user_id)}


@router.get("/resource/{resource_type}/{resource_id}")
async def get_resource_audit_trail(
    resource_type: AuditResource,
    resource_id: str,
    limit: int = Query(default=50, le=200),
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get audit trail for a specific resource"""
    school_id = current_user.get("school_id")

    result = supabase.table("audit_logs").select(
        "*, user:user_id(first_name, last_name)"
    ).eq("school_id", school_id).eq(
        "resource_type", resource_type.value
    ).eq("resource_id", resource_id).order("created_at", desc=True).limit(limit).execute()

    return {
        "logs": result.data or [],
        "resource_type": resource_type.value,
        "resource_id": resource_id
    }


# ============================================================
# AUDIT LOG CREATION
# ============================================================

@router.post("")
async def create_audit_log(
    log: AuditLogCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create an audit log entry (internal use)"""
    school_id = current_user.get("school_id")
    user_id = current_user.get("id")

    log_data = {
        "school_id": school_id,
        "user_id": user_id,
        "action": log.action.value,
        "resource_type": log.resource_type.value,
        "resource_id": log.resource_id,
        "description": log.description,
        "old_value": log.old_value,
        "new_value": log.new_value,
        "metadata": log.metadata,
        "ip_address": None,  # Would be set by middleware
        "user_agent": None
    }

    result = supabase.table("audit_logs").insert(log_data).execute()

    return result.data[0] if result.data else None


# ============================================================
# SECURITY AUDIT
# ============================================================

@router.get("/security/failed-logins")
async def get_failed_logins(
    days: int = 7,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get failed login attempts"""
    school_id = current_user.get("school_id")
    start_date = datetime.utcnow() - timedelta(days=days)

    result = supabase.table("audit_logs").select(
        "user_id, ip_address, created_at, metadata"
    ).eq("school_id", school_id).eq("action", "login").eq(
        "metadata->success", False
    ).gte("created_at", start_date.isoformat()).order("created_at", desc=True).execute()

    # Group by IP
    by_ip = {}
    for log in (result.data or []):
        ip = log.get("ip_address", "unknown")
        if ip not in by_ip:
            by_ip[ip] = {"count": 0, "last_attempt": None}
        by_ip[ip]["count"] += 1
        if not by_ip[ip]["last_attempt"]:
            by_ip[ip]["last_attempt"] = log.get("created_at")

    suspicious_ips = [
        {"ip": ip, **data}
        for ip, data in by_ip.items()
        if data["count"] >= 5
    ]

    return {
        "total_failed_logins": len(result.data or []),
        "suspicious_ips": suspicious_ips,
        "period_days": days
    }


@router.get("/security/sensitive-actions")
async def get_sensitive_actions(
    days: int = 7,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get sensitive/high-risk actions"""
    school_id = current_user.get("school_id")
    start_date = datetime.utcnow() - timedelta(days=days)

    sensitive_actions = ["delete", "export", "update"]
    sensitive_resources = ["user", "payment", "grade", "setting"]

    result = supabase.table("audit_logs").select(
        "*, user:user_id(first_name, last_name, role)"
    ).eq("school_id", school_id).in_(
        "action", sensitive_actions
    ).in_("resource_type", sensitive_resources).gte(
        "created_at", start_date.isoformat()
    ).order("created_at", desc=True).execute()

    return {
        "sensitive_actions": result.data or [],
        "total": len(result.data or []),
        "period_days": days
    }


@router.get("/security/data-exports")
async def get_data_exports(
    days: int = 30,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get data export history"""
    school_id = current_user.get("school_id")
    start_date = datetime.utcnow() - timedelta(days=days)

    result = supabase.table("audit_logs").select(
        "*, user:user_id(first_name, last_name, role)"
    ).eq("school_id", school_id).eq("action", "export").gte(
        "created_at", start_date.isoformat()
    ).order("created_at", desc=True).execute()

    return {"exports": result.data or []}


# ============================================================
# COMPLIANCE REPORTS
# ============================================================

@router.get("/compliance/gdpr")
async def get_gdpr_compliance_report(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get GDPR compliance report"""
    school_id = current_user.get("school_id")

    # Data access logs
    access_logs = supabase.table("audit_logs").select(
        "id", count="exact"
    ).eq("school_id", school_id).eq("action", "read").eq(
        "resource_type", "student"
    ).execute()

    # Data exports
    exports = supabase.table("audit_logs").select(
        "id", count="exact"
    ).eq("school_id", school_id).eq("action", "export").execute()

    # Data deletions
    deletions = supabase.table("audit_logs").select(
        "id", count="exact"
    ).eq("school_id", school_id).eq("action", "delete").execute()

    # Consent records (if applicable)
    consents = supabase.table("consent_records").select(
        "id", count="exact"
    ).eq("school_id", school_id).execute()

    return {
        "data_access_events": access_logs.count or 0,
        "data_export_events": exports.count or 0,
        "data_deletion_events": deletions.count or 0,
        "consent_records": consents.count or 0,
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/compliance/access-report")
async def get_access_compliance_report(
    user_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get data access report for a specific user (GDPR Subject Access Request)"""
    school_id = current_user.get("school_id")

    # All data accessed about this user
    result = supabase.table("audit_logs").select(
        "action, resource_type, created_at, user:user_id(first_name, last_name)"
    ).eq("school_id", school_id).eq("resource_id", str(user_id)).order("created_at", desc=True).execute()

    return {
        "subject_id": str(user_id),
        "access_history": result.data or [],
        "generated_at": datetime.utcnow().isoformat()
    }
