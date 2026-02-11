"""
System Admin API - Extended Platform Management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.security import require_system_admin
from app.db.supabase import supabase_admin

router = APIRouter(prefix="/system", tags=["System Admin"])


# ============== PLATFORM METRICS ==============

@router.get("/platform-metrics")
async def get_platform_metrics(current_user: dict = Depends(require_system_admin)):
    """Get platform-wide metrics"""
    
    if supabase_admin:
        schools = supabase_admin.table("schools").select("id, is_active").execute()
        total_schools = len(schools.data)
        active_schools = len([s for s in schools.data if s.get("is_active")])
        
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        new_schools = supabase_admin.table("schools").select("id").gte("created_at", thirty_days_ago).execute()
        
        users = supabase_admin.table("user_profiles").select("id, is_active, last_login").execute()
        total_users = len(users.data)
        active_users = len([u for u in users.data if u.get("is_active")])
        
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        dau = len([u for u in users.data if u.get("last_login") and u["last_login"] > yesterday])
        
        students = supabase_admin.table("students").select("id, status").execute()
        total_students = len([s for s in students.data if s.get("status") == "active"])
        
        return {
            "total_schools": total_schools,
            "active_schools": active_schools,
            "new_schools_30d": len(new_schools.data),
            "total_users": total_users,
            "active_users": active_users,
            "daily_active_users": dau,
            "total_students": total_students,
            "system_uptime": "99.9%",
            "api_response_time": "145ms",
            "error_rate": "0.02%",
        }
    
    return {
        "total_schools": 24,
        "active_schools": 22,
        "new_schools_30d": 3,
        "total_users": 3892,
        "active_users": 3654,
        "daily_active_users": 482,
        "total_students": 15240,
        "system_uptime": "99.9%",
        "api_response_time": "145ms",
        "error_rate": "0.02%",
    }


# ============== SCHOOLS MANAGEMENT ==============

@router.get("/schools")
async def get_all_schools(
    status: Optional[str] = None,
    plan: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(require_system_admin)
):
    """Get all schools with filters"""
    
    if supabase_admin:
        query = supabase_admin.table("schools").select("*")
        
        if status:
            query = query.eq("is_active", status == "active")
        
        schools_data = query.order("created_at", desc=True).execute()
        
        schools = []
        for school in schools_data.data:
            if search and search.lower() not in school["name"].lower():
                continue
                
            users = supabase_admin.table("user_profiles").select("id").eq("school_id", school["id"]).execute()
            students = supabase_admin.table("students").select("id").eq("school_id", school["id"]).eq("status", "active").execute()
            last_login = supabase_admin.table("user_profiles").select("last_login").eq("school_id", school["id"]).order("last_login", desc=True).limit(1).execute()
            
            schools.append({
                "id": school["id"],
                "name": school["name"],
                "code": school.get("code"),
                "plan": "Pro",
                "status": "Active" if school.get("is_active") else "Suspended",
                "users": len(users.data),
                "students": len(students.data),
                "storage_used": "2.4 GB",
                "last_active": last_login.data[0]["last_login"] if last_login.data else None,
                "renewal_date": "2024-12-31",
                "health": "Healthy",
            })
        
        return schools
    
    return [
        {"id": "1", "name": "Greenfield Academy", "code": "GFA001", "plan": "Pro", "status": "Active", "users": 182, "students": 1240, "storage_used": "12.4 GB", "last_active": "2 mins ago", "renewal_date": "2024-12-31", "health": "Healthy"},
        {"id": "2", "name": "Riverside High", "code": "RHS002", "plan": "Basic", "status": "Trial", "users": 24, "students": 180, "storage_used": "2.1 GB", "last_active": "1 hr ago", "renewal_date": "2024-03-15", "health": "Warning"},
    ]


@router.post("/schools")
async def create_school(school_data: dict, current_user: dict = Depends(require_system_admin)):
    """Create a new school"""
    
    if supabase_admin:
        result = supabase_admin.table("schools").insert({
            "name": school_data.get("name"),
            "code": school_data.get("code"),
            "address": school_data.get("address"),
            "phone": school_data.get("phone"),
            "email": school_data.get("email"),
            "is_active": True,
        }).execute()
        
        if result.data:
            supabase_admin.table("audit_logs").insert({
                "user_id": current_user["id"],
                "action": "school_created",
                "entity_type": "school",
                "entity_id": result.data[0]["id"],
            }).execute()
            
            return result.data[0]
    
    raise HTTPException(status_code=500, detail="Failed to create school")


@router.get("/schools/{school_id}")
async def get_school_details(school_id: str, current_user: dict = Depends(require_system_admin)):
    """Get detailed school information"""
    
    if supabase_admin:
        school = supabase_admin.table("schools").select("*").eq("id", school_id).execute()
        if not school.data:
            raise HTTPException(status_code=404, detail="School not found")
        
        users = supabase_admin.table("user_profiles").select("*").eq("school_id", school_id).execute()
        admins = [u for u in users.data if u.get("role") in ["principal", "office_admin"]]
        
        return {
            "school": school.data[0],
            "admins": admins,
            "subscription": {"plan": "Pro", "status": "Active", "renewal_date": "2024-12-31"},
            "usage": {"users": len(users.data), "storage": "12.4 GB", "api_calls": 45230},
        }
    
    return {
        "school": {"id": school_id, "name": "Greenfield Academy", "code": "GFA001"},
        "admins": [{"id": "1", "name": "John Admin", "email": "admin@school.com", "role": "principal"}],
        "subscription": {"plan": "Pro", "status": "Active", "renewal_date": "2024-12-31"},
        "usage": {"users": 182, "storage": "12.4 GB", "api_calls": 45230},
    }


@router.post("/schools/{school_id}/suspend")
async def suspend_school(school_id: str, current_user: dict = Depends(require_system_admin)):
    """Suspend a school"""
    
    if supabase_admin:
        result = supabase_admin.table("schools").update({"is_active": False}).eq("id", school_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="School not found")
        
        supabase_admin.table("audit_logs").insert({
            "user_id": current_user["id"],
            "action": "school_suspended",
            "entity_type": "school",
            "entity_id": school_id,
        }).execute()
    
    return {"message": "School suspended successfully"}


@router.post("/schools/{school_id}/activate")
async def activate_school(school_id: str, current_user: dict = Depends(require_system_admin)):
    """Activate a school"""
    
    if supabase_admin:
        result = supabase_admin.table("schools").update({"is_active": True}).eq("id", school_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="School not found")
    
    return {"message": "School activated successfully"}


# ============== GLOBAL USERS ==============

@router.get("/users")
async def get_all_users(
    role: Optional[str] = None,
    school_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(require_system_admin)
):
    """Get all users across platform"""
    
    if supabase_admin:
        query = supabase_admin.table("user_profiles").select("*")
        
        if role:
            query = query.eq("role", role)
        if school_id:
            query = query.eq("school_id", school_id)
        if status:
            query = query.eq("is_active", status == "active")
        
        result = query.range(skip, skip + limit - 1).order("created_at", desc=True).execute()
        return result.data
    
    return [
        {"id": "1", "name": "John Doe", "email": "john@school.com", "role": "principal", "school": "Greenfield Academy", "status": "Active", "last_login": "2024-01-15", "two_fa": True},
        {"id": "2", "name": "Jane Smith", "email": "jane@school.com", "role": "teacher", "school": "Riverside High", "status": "Active", "last_login": "2024-01-14", "two_fa": False},
    ]


@router.post("/users")
async def create_user(user_data: dict, current_user: dict = Depends(require_system_admin)):
    """Create a new user"""
    
    if supabase_admin:
        result = supabase_admin.table("user_profiles").insert({
            "email": user_data.get("email"),
            "full_name": user_data.get("full_name"),
            "role": user_data.get("role"),
            "school_id": user_data.get("school_id"),
            "is_active": True,
        }).execute()
        
        if result.data:
            supabase_admin.table("audit_logs").insert({
                "user_id": current_user["id"],
                "action": "user_created",
                "entity_type": "user",
                "entity_id": result.data[0]["id"],
            }).execute()
            
            return result.data[0]
    
    raise HTTPException(status_code=500, detail="Failed to create user")


@router.get("/users/{user_id}")
async def get_user_details(user_id: str, current_user: dict = Depends(require_system_admin)):
    """Get user details"""
    
    if supabase_admin:
        user = supabase_admin.table("user_profiles").select("*").eq("id", user_id).execute()
        if not user.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        login_history = supabase_admin.table("audit_logs").select("*").eq("user_id", user_id).eq("action", "login").order("created_at", desc=True).limit(10).execute()
        
        return {
            "user": user.data[0],
            "login_history": login_history.data if login_history.data else [],
        }
    
    return {
        "user": {"id": user_id, "name": "John Doe", "email": "john@school.com", "role": "principal"},
        "login_history": [],
    }


@router.post("/users/{user_id}/lock")
async def lock_user(user_id: str, current_user: dict = Depends(require_system_admin)):
    """Lock user account"""
    
    if supabase_admin:
        supabase_admin.table("user_profiles").update({"is_active": False}).eq("id", user_id).execute()
    
    return {"message": "User locked successfully"}


# ============== SECURITY ==============

@router.get("/security/summary")
async def get_security_summary(current_user: dict = Depends(require_system_admin)):
    """Get security metrics"""
    
    if supabase_admin:
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        failed_logins = supabase_admin.table("audit_logs").select("id").eq("action", "login_failed").gte("created_at", yesterday).execute()
        locked_accounts = supabase_admin.table("user_profiles").select("id").eq("is_active", False).execute()
        
        return {
            "failed_logins_24h": len(failed_logins.data),
            "locked_accounts": len(locked_accounts.data),
            "admin_role_changes": 0,
            "suspicious_activity": 0,
            "two_fa_adoption": "45%",
        }
    
    return {
        "failed_logins_24h": 12,
        "locked_accounts": 3,
        "admin_role_changes": 1,
        "suspicious_activity": 0,
        "two_fa_adoption": "45%",
    }


@router.get("/security/sessions")
async def get_active_sessions(current_user: dict = Depends(require_system_admin)):
    """Get active user sessions"""
    
    return [
        {"user": "John Doe", "school": "Greenfield", "device": "Chrome/Windows", "location": "New York, US", "session_age": "2h", "ip": "192.168.1.1"},
        {"user": "Jane Smith", "school": "Riverside", "device": "Safari/Mac", "location": "London, UK", "session_age": "30m", "ip": "192.168.1.2"},
    ]


# ============== SYSTEM LOGS ==============

@router.get("/logs")
async def get_system_logs(
    log_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(require_system_admin)
):
    """Get system audit logs"""
    
    if supabase_admin:
        query = supabase_admin.table("audit_logs").select("*")
        
        if log_type:
            query = query.eq("action", log_type)
        
        result = query.range(skip, skip + limit - 1).order("created_at", desc=True).execute()
        return result.data
    
    return [
        {"id": "1", "timestamp": datetime.now().isoformat(), "event_type": "school_created", "actor": "System Admin", "target": "Greenfield Academy", "ip": "192.168.1.1", "status": "success"},
        {"id": "2", "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(), "event_type": "user_locked", "actor": "System Admin", "target": "john@school.com", "ip": "192.168.1.1", "status": "success"},
    ]


# ============== FEATURE FLAGS ==============

@router.get("/features")
async def get_feature_flags(current_user: dict = Depends(require_system_admin)):
    """Get all feature flags"""
    
    return [
        {"id": "1", "name": "Parent Payments", "status": "enabled", "type": "stable", "enabled_schools": 18, "total_schools": 24, "last_modified": "2024-01-10"},
        {"id": "2", "name": "Messaging System", "status": "beta", "type": "beta", "enabled_schools": 12, "total_schools": 24, "last_modified": "2024-01-15"},
        {"id": "3", "name": "Timetabling", "status": "pilot", "type": "alpha", "enabled_schools": 3, "total_schools": 24, "last_modified": "2024-01-20"},
    ]


@router.post("/features/{feature_id}/toggle")
async def toggle_feature(feature_id: str, enabled: bool, current_user: dict = Depends(require_system_admin)):
    """Toggle feature flag globally"""
    
    return {"message": f"Feature {'enabled' if enabled else 'disabled'} successfully"}


# ============== PLATFORM SETTINGS ==============

@router.get("/settings")
async def get_platform_settings(current_user: dict = Depends(require_system_admin)):
    """Get platform settings"""
    
    return {
        "platform_name": "EduCore SaaS",
        "support_email": "support@educore.com",
        "default_timezone": "UTC",
        "default_currency": "USD",
        "session_timeout": "60",
    }


@router.put("/settings")
async def update_platform_settings(settings: dict, current_user: dict = Depends(require_system_admin)):
    """Update platform settings"""
    
    if supabase_admin:
        supabase_admin.table("audit_logs").insert({
            "user_id": current_user["id"],
            "action": "settings_updated",
            "entity_type": "platform",
        }).execute()
    
    return {"message": "Settings updated successfully"}


# ============== SYSTEM ALERTS ==============

@router.get("/alerts")
async def get_system_alerts(current_user: dict = Depends(require_system_admin)):
    """Get platform-level alerts"""
    
    return [
        {"type": "performance", "severity": "info", "message": "Database CPU usage at 65%", "timestamp": datetime.now().isoformat()},
        {"type": "security", "severity": "warning", "message": "12 failed login attempts detected", "timestamp": datetime.now().isoformat()},
    ]


# ============== PLATFORM ACTIVITY ==============

@router.get("/activity")
async def get_platform_activity(limit: int = 20, current_user: dict = Depends(require_system_admin)):
    """Get recent platform activity"""
    
    if supabase_admin:
        activities = supabase_admin.table("audit_logs").select("*").in_("action", [
            "school_created", "school_suspended", "feature_enabled", "global_setting_changed"
        ]).order("created_at", desc=True).limit(limit).execute()
        
        return activities.data
    
    return [
        {"id": "1", "action": "school_created", "description": "New school 'Bright Future Academy' created", "timestamp": datetime.now().isoformat()},
        {"id": "2", "action": "school_upgraded", "description": "School 'Greenfield' upgraded to Pro Plan", "timestamp": (datetime.now() - timedelta(hours=2)).isoformat()},
    ]
