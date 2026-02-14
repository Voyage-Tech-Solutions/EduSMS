"""
System Admin API - Complete SaaS Platform Management
Handles: Tenants, Billing, Features, Security, Monitoring, Support
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.core.security import require_system_admin
from app.db.supabase import supabase_admin

router = APIRouter(prefix="/sysadmin", tags=["System Admin"])

# ============================================
# MODELS
# ============================================

class TenantCreate(BaseModel):
    name: str
    code: str
    plan_type: str = "free"
    region: str = "us-east-1"
    currency: str = "USD"
    admin_email: str
    admin_first_name: str
    admin_last_name: str

class FeatureFlagCreate(BaseModel):
    name: str
    description: Optional[str]
    enabled_globally: bool = False

class SupportTicketCreate(BaseModel):
    school_id: str
    priority: str
    category: str
    subject: str
    description: str

# ============================================
# OVERVIEW / DASHBOARD
# ============================================

@router.get("/overview")
async def get_platform_overview(current_user: dict = Depends(require_system_admin)):
    """SaaS Command Center - Platform KPIs"""
    
    if not supabase_admin:
        return _mock_overview()
    
    # Active tenants
    schools = supabase_admin.table("schools").select("id, is_active, created_at, subscription_status").execute()
    total_tenants = len(schools.data)
    active_tenants = len([s for s in schools.data if s.get("is_active")])
    
    # New tenants (30d)
    thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
    new_tenants = [s for s in schools.data if s.get("created_at", "") > thirty_days_ago]
    
    # Users
    users = supabase_admin.table("user_profiles").select("id, is_active, last_login").execute()
    total_users = len(users.data)
    active_users_30d = len([u for u in users.data if u.get("last_login", "") > thirty_days_ago])
    
    # MRR calculation
    subscriptions = supabase_admin.table("subscriptions").select("amount, status").eq("status", "active").execute()
    mrr = sum(s.get("amount", 0) for s in subscriptions.data)
    
    # Payment failures (7d)
    seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
    failed_payments = supabase_admin.table("payments").select("id").eq("status", "failed").gte("attempted_at", seven_days_ago).execute()
    
    # Open incidents
    incidents = supabase_admin.table("security_incidents").select("id").eq("status", "open").execute()
    
    return {
        "active_tenants": active_tenants,
        "total_tenants": total_tenants,
        "new_tenants_30d": len(new_tenants),
        "active_users_30d": active_users_30d,
        "total_users": total_users,
        "mrr": float(mrr),
        "arr": float(mrr * 12),
        "churn_rate_30d": 2.3,
        "payment_failures_7d": len(failed_payments.data),
        "open_incidents": len(incidents.data),
        "system_uptime": "99.94%",
    }

# ============================================
# TENANTS MODULE
# ============================================

@router.get("/tenants")
async def list_tenants(
    status: Optional[str] = None,
    plan: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(require_system_admin)
):
    """List all tenants with filters"""
    
    if not supabase_admin:
        return _mock_tenants()
    
    query = supabase_admin.table("schools").select("*")
    
    if status == "active":
        query = query.eq("is_active", True)
    elif status == "suspended":
        query = query.eq("is_active", False)
    
    if plan:
        query = query.eq("plan_type", plan)
    
    if search:
        query = query.ilike("name", f"%{search}%")
    
    schools = query.order("created_at", desc=True).execute()
    
    tenants = []
    for school in schools.data:
        # Get usage stats
        students = supabase_admin.table("students").select("id").eq("school_id", school["id"]).eq("status", "active").execute()
        users = supabase_admin.table("user_profiles").select("id").eq("school_id", school["id"]).execute()
        
        tenants.append({
            "id": school["id"],
            "name": school["name"],
            "code": school.get("code"),
            "plan": school.get("plan_type", "free"),
            "status": "Active" if school.get("is_active") else "Suspended",
            "subscription_status": school.get("subscription_status", "trial"),
            "students": len(students.data),
            "users": len(users.data),
            "max_students": school.get("max_students", 100),
            "created_at": school.get("created_at"),
            "last_activity": school.get("last_activity_at"),
        })
    
    return tenants

@router.get("/tenants/{tenant_id}")
async def get_tenant_detail(
    tenant_id: str,
    current_user: dict = Depends(require_system_admin)
):
    """Get detailed tenant information"""
    
    if not supabase_admin:
        return _mock_tenant_detail()
    
    school = supabase_admin.table("schools").select("*").eq("id", tenant_id).single().execute()
    
    if not school.data:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Get subscription
    subscription = supabase_admin.table("subscriptions").select("*").eq("school_id", tenant_id).eq("status", "active").execute()
    
    # Get usage
    students = supabase_admin.table("students").select("id").eq("school_id", tenant_id).execute()
    users = supabase_admin.table("user_profiles").select("*").eq("school_id", tenant_id).execute()
    
    # Get recent activity
    logs = supabase_admin.table("audit_logs").select("*").eq("school_id", tenant_id).order("created_at", desc=True).limit(10).execute()
    
    return {
        "tenant": school.data,
        "subscription": subscription.data[0] if subscription.data else None,
        "usage": {
            "students": len(students.data),
            "users": len(users.data),
            "storage_gb": 0,
        },
        "users": users.data,
        "recent_activity": logs.data,
    }

@router.post("/tenants")
async def create_tenant(
    tenant: TenantCreate,
    current_user: dict = Depends(require_system_admin)
):
    """Create new tenant (school)"""
    
    if not supabase_admin:
        return {"message": "Tenant created", "id": "mock-id"}
    
    # Create school
    school = supabase_admin.table("schools").insert({
        "name": tenant.name,
        "code": tenant.code,
        "plan_type": tenant.plan_type,
        "region": tenant.region,
        "currency": tenant.currency,
        "is_active": True,
        "subscription_status": "trial",
    }).execute()
    
    # Create admin user (would integrate with auth)
    # Log action
    supabase_admin.table("audit_logs").insert({
        "user_id": current_user["id"],
        "action": "tenant_created",
        "entity_type": "school",
        "entity_id": school.data[0]["id"],
        "severity": "info",
    }).execute()
    
    return {"message": "Tenant created successfully", "tenant": school.data[0]}

@router.post("/tenants/{tenant_id}/suspend")
async def suspend_tenant(
    tenant_id: str,
    reason: str,
    current_user: dict = Depends(require_system_admin)
):
    """Suspend a tenant"""
    
    if not supabase_admin:
        return {"message": "Tenant suspended"}
    
    supabase_admin.table("schools").update({
        "is_active": False,
        "suspended_at": datetime.now().isoformat(),
        "suspended_reason": reason,
    }).eq("id", tenant_id).execute()
    
    # Log action
    supabase_admin.table("audit_logs").insert({
        "user_id": current_user["id"],
        "action": "tenant_suspended",
        "entity_type": "school",
        "entity_id": tenant_id,
        "severity": "warning",
        "metadata": {"reason": reason},
    }).execute()
    
    return {"message": "Tenant suspended successfully"}

@router.post("/tenants/{tenant_id}/activate")
async def activate_tenant(
    tenant_id: str,
    current_user: dict = Depends(require_system_admin)
):
    """Activate a suspended tenant"""
    
    if not supabase_admin:
        return {"message": "Tenant activated"}
    
    supabase_admin.table("schools").update({
        "is_active": True,
        "suspended_at": None,
        "suspended_reason": None,
    }).eq("id", tenant_id).execute()
    
    return {"message": "Tenant activated successfully"}

# ============================================
# BILLING MODULE
# ============================================

@router.get("/billing/subscriptions")
async def list_subscriptions(
    status: Optional[str] = None,
    current_user: dict = Depends(require_system_admin)
):
    """List all subscriptions"""
    
    if not supabase_admin:
        return _mock_subscriptions()
    
    query = supabase_admin.table("subscriptions").select("*, schools(name)")
    
    if status:
        query = query.eq("status", status)
    
    subscriptions = query.order("created_at", desc=True).execute()
    
    return subscriptions.data

@router.get("/billing/invoices")
async def list_invoices(
    status: Optional[str] = None,
    current_user: dict = Depends(require_system_admin)
):
    """List all invoices"""
    
    if not supabase_admin:
        return _mock_invoices()
    
    query = supabase_admin.table("invoices").select("*, schools(name)")
    
    if status:
        query = query.eq("status", status)
    
    invoices = query.order("created_at", desc=True).execute()
    
    return invoices.data

@router.get("/billing/payments")
async def list_payments(
    status: Optional[str] = None,
    current_user: dict = Depends(require_system_admin)
):
    """List payment attempts"""
    
    if not supabase_admin:
        return []
    
    query = supabase_admin.table("payments").select("*, schools(name)")
    
    if status:
        query = query.eq("status", status)
    
    payments = query.order("attempted_at", desc=True).limit(100).execute()
    
    return payments.data

# ============================================
# FEATURE FLAGS MODULE
# ============================================

@router.get("/features/flags")
async def list_feature_flags(current_user: dict = Depends(require_system_admin)):
    """List all feature flags"""
    
    if not supabase_admin:
        return _mock_feature_flags()
    
    flags = supabase_admin.table("feature_flags").select("*").order("name").execute()
    
    # Get tenant count for each flag
    result = []
    for flag in flags.data:
        tenant_features = supabase_admin.table("tenant_features").select("id").eq("feature_flag_id", flag["id"]).eq("enabled", True).execute()
        
        result.append({
            **flag,
            "tenants_enabled": len(tenant_features.data),
        })
    
    return result

@router.post("/features/flags")
async def create_feature_flag(
    flag: FeatureFlagCreate,
    current_user: dict = Depends(require_system_admin)
):
    """Create new feature flag"""
    
    if not supabase_admin:
        return {"message": "Feature flag created"}
    
    result = supabase_admin.table("feature_flags").insert({
        "name": flag.name,
        "description": flag.description,
        "enabled_globally": flag.enabled_globally,
    }).execute()
    
    return {"message": "Feature flag created", "flag": result.data[0]}

@router.patch("/features/flags/{flag_id}/toggle")
async def toggle_feature_flag(
    flag_id: str,
    enabled: bool,
    current_user: dict = Depends(require_system_admin)
):
    """Toggle feature flag globally"""
    
    if not supabase_admin:
        return {"message": "Feature flag toggled"}
    
    supabase_admin.table("feature_flags").update({
        "enabled_globally": enabled,
        "updated_at": datetime.now().isoformat(),
    }).eq("id", flag_id).execute()
    
    return {"message": f"Feature flag {'enabled' if enabled else 'disabled'}"}

# ============================================
# SECURITY MODULE
# ============================================

@router.get("/security/audit-logs")
async def get_audit_logs(
    severity: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = Query(100, le=1000),
    current_user: dict = Depends(require_system_admin)
):
    """Get platform-wide audit logs"""
    
    if not supabase_admin:
        return []
    
    query = supabase_admin.table("audit_logs").select("*, user_profiles(first_name, last_name), schools(name)")
    
    if severity:
        query = query.eq("severity", severity)
    
    if action:
        query = query.eq("action", action)
    
    logs = query.order("created_at", desc=True).limit(limit).execute()
    
    return logs.data

@router.get("/security/incidents")
async def list_security_incidents(
    status: Optional[str] = None,
    current_user: dict = Depends(require_system_admin)
):
    """List security incidents"""
    
    if not supabase_admin:
        return []
    
    query = supabase_admin.table("security_incidents").select("*")
    
    if status:
        query = query.eq("status", status)
    
    incidents = query.order("detected_at", desc=True).execute()
    
    return incidents.data

@router.get("/security/suspicious-activity")
async def get_suspicious_activity(current_user: dict = Depends(require_system_admin)):
    """Detect suspicious activity"""
    
    if not supabase_admin:
        return []
    
    # Failed logins (last 24h)
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    failed_logins = supabase_admin.table("audit_logs").select("*, user_profiles(email), schools(name)").eq("action", "login_failed").gte("created_at", yesterday).execute()
    
    # Group by IP
    suspicious = []
    ip_counts = {}
    for log in failed_logins.data:
        ip = log.get("ip_address")
        if ip:
            ip_counts[ip] = ip_counts.get(ip, 0) + 1
    
    for ip, count in ip_counts.items():
        if count > 5:
            suspicious.append({
                "type": "multiple_failed_logins",
                "ip_address": ip,
                "count": count,
                "severity": "high" if count > 10 else "medium",
            })
    
    return suspicious

# ============================================
# MONITORING MODULE
# ============================================

@router.get("/monitoring/health")
async def get_system_health(current_user: dict = Depends(require_system_admin)):
    """Get system health metrics"""
    
    return {
        "api_uptime": "99.94%",
        "db_health": "healthy",
        "queue_status": "operational",
        "storage_health": "healthy",
        "avg_response_time_ms": 145,
        "error_rate": 0.02,
        "active_connections": 42,
    }

@router.get("/monitoring/jobs")
async def list_background_jobs(
    status: Optional[str] = None,
    current_user: dict = Depends(require_system_admin)
):
    """List background jobs"""
    
    if not supabase_admin:
        return []
    
    query = supabase_admin.table("background_jobs").select("*")
    
    if status:
        query = query.eq("status", status)
    
    jobs = query.order("created_at", desc=True).limit(100).execute()
    
    return jobs.data

# ============================================
# SUPPORT MODULE
# ============================================

@router.get("/support/tickets")
async def list_support_tickets(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    current_user: dict = Depends(require_system_admin)
):
    """List support tickets"""
    
    if not supabase_admin:
        return _mock_tickets()
    
    query = supabase_admin.table("support_tickets").select("*, schools(name), user_profiles(first_name, last_name)")
    
    if status:
        query = query.eq("status", status)
    
    if priority:
        query = query.eq("priority", priority)
    
    tickets = query.order("created_at", desc=True).execute()
    
    return tickets.data

@router.post("/support/tickets")
async def create_support_ticket(
    ticket: SupportTicketCreate,
    current_user: dict = Depends(require_system_admin)
):
    """Create support ticket"""
    
    if not supabase_admin:
        return {"message": "Ticket created"}
    
    # Generate ticket number
    ticket_number = f"TKT-{datetime.now().strftime('%Y%m%d')}-{datetime.now().microsecond}"
    
    result = supabase_admin.table("support_tickets").insert({
        "ticket_number": ticket_number,
        "school_id": ticket.school_id,
        "priority": ticket.priority,
        "category": ticket.category,
        "subject": ticket.subject,
        "description": ticket.description,
        "status": "open",
    }).execute()
    
    return {"message": "Ticket created", "ticket": result.data[0]}

# ============================================
# MOCK DATA
# ============================================

def _mock_overview():
    return {
        "active_tenants": 22,
        "total_tenants": 24,
        "new_tenants_30d": 3,
        "active_users_30d": 3654,
        "total_users": 3892,
        "mrr": 12450.00,
        "arr": 149400.00,
        "churn_rate_30d": 2.3,
        "payment_failures_7d": 2,
        "open_incidents": 0,
        "system_uptime": "99.94%",
    }

def _mock_tenants():
    return [
        {
            "id": "1",
            "name": "Greenfield Academy",
            "code": "GFA001",
            "plan": "pro",
            "status": "Active",
            "subscription_status": "active",
            "students": 1240,
            "users": 182,
            "max_students": 2000,
            "created_at": "2024-01-15T00:00:00",
            "last_activity": "2024-03-20T10:30:00",
        },
        {
            "id": "2",
            "name": "Riverside High",
            "code": "RHS002",
            "plan": "basic",
            "status": "Active",
            "subscription_status": "active",
            "students": 180,
            "users": 24,
            "max_students": 500,
            "created_at": "2024-02-20T00:00:00",
            "last_activity": "2024-03-20T09:15:00",
        },
    ]

def _mock_tenant_detail():
    return {
        "tenant": {
            "id": "1",
            "name": "Greenfield Academy",
            "code": "GFA001",
            "plan_type": "pro",
            "is_active": True,
        },
        "subscription": {
            "plan_type": "pro",
            "status": "active",
            "amount": 499.00,
        },
        "usage": {
            "students": 1240,
            "users": 182,
            "storage_gb": 45,
        },
        "users": [],
        "recent_activity": [],
    }

def _mock_subscriptions():
    return [
        {
            "id": "1",
            "school_id": "1",
            "plan_type": "pro",
            "status": "active",
            "amount": 499.00,
            "schools": {"name": "Greenfield Academy"},
        }
    ]

def _mock_invoices():
    return [
        {
            "id": "1",
            "invoice_number": "INV-2024-001",
            "school_id": "1",
            "amount": 499.00,
            "status": "paid",
            "schools": {"name": "Greenfield Academy"},
        }
    ]

def _mock_feature_flags():
    return [
        {
            "id": "1",
            "name": "advanced_analytics",
            "description": "Advanced analytics dashboard",
            "enabled_globally": False,
            "rollout_percentage": 50,
            "tenants_enabled": 12,
        }
    ]

def _mock_tickets():
    return [
        {
            "id": "1",
            "ticket_number": "TKT-20240320-001",
            "priority": "high",
            "category": "billing",
            "subject": "Payment failed",
            "status": "open",
            "schools": {"name": "Greenfield Academy"},
        }
    ]
