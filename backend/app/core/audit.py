"""
EduCore Backend - Enhanced Audit Logging System
Comprehensive audit trail for security and compliance
"""
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union
from enum import Enum
from functools import wraps
from uuid import UUID

from fastapi import Request
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    """Standard audit actions"""
    # Authentication
    LOGIN = "auth.login"
    LOGIN_FAILED = "auth.login_failed"
    LOGOUT = "auth.logout"
    PASSWORD_CHANGE = "auth.password_change"
    PASSWORD_RESET = "auth.password_reset"
    MFA_ENABLED = "auth.mfa_enabled"
    MFA_DISABLED = "auth.mfa_disabled"
    MFA_VERIFIED = "auth.mfa_verified"
    SESSION_REVOKED = "auth.session_revoked"

    # User Management
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_ACTIVATE = "user.activate"
    USER_DEACTIVATE = "user.deactivate"
    USER_ROLE_CHANGE = "user.role_change"

    # Student Management
    STUDENT_CREATE = "student.create"
    STUDENT_UPDATE = "student.update"
    STUDENT_DELETE = "student.delete"
    STUDENT_ENROLL = "student.enroll"
    STUDENT_TRANSFER = "student.transfer"
    STUDENT_GRADUATE = "student.graduate"

    # Academic
    GRADE_ENTRY = "academic.grade_entry"
    GRADE_UPDATE = "academic.grade_update"
    GRADE_DELETE = "academic.grade_delete"
    ATTENDANCE_RECORD = "attendance.record"
    ATTENDANCE_UPDATE = "attendance.update"

    # Financial
    INVOICE_CREATE = "finance.invoice_create"
    INVOICE_UPDATE = "finance.invoice_update"
    PAYMENT_RECORD = "finance.payment"
    REFUND_PROCESS = "finance.refund"
    FEE_STRUCTURE_CHANGE = "finance.fee_change"

    # Administrative
    SCHOOL_SETTINGS_UPDATE = "admin.settings_update"
    SECURITY_SETTINGS_UPDATE = "admin.security_update"
    APPROVAL_GRANTED = "admin.approval_granted"
    APPROVAL_DENIED = "admin.approval_denied"

    # Data Operations
    DATA_EXPORT = "data.export"
    DATA_IMPORT = "data.import"
    BULK_UPDATE = "data.bulk_update"
    BULK_DELETE = "data.bulk_delete"

    # System
    SYSTEM_ERROR = "system.error"
    PERMISSION_DENIED = "system.permission_denied"
    RATE_LIMIT_EXCEEDED = "system.rate_limit"


class AuditSeverity(str, Enum):
    """Audit log severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditCategory(str, Enum):
    """Audit log categories"""
    AUTHENTICATION = "authentication"
    USER_MANAGEMENT = "user_management"
    STUDENT_MANAGEMENT = "student_management"
    ACADEMIC = "academic"
    FINANCIAL = "financial"
    ADMINISTRATIVE = "administrative"
    DATA_OPERATIONS = "data_operations"
    SYSTEM = "system"
    SECURITY = "security"


class AuditEntry(BaseModel):
    """Audit log entry model"""
    school_id: Optional[str] = None
    user_id: Optional[str] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    before_data: Optional[Dict] = None
    after_data: Optional[Dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    severity: str = AuditSeverity.INFO
    category: Optional[str] = None
    metadata: Optional[Dict] = None
    duration_ms: Optional[int] = None
    status_code: Optional[int] = None
    request_id: Optional[str] = None


class AuditLogger:
    """
    Comprehensive audit logging system.

    Features:
    - Action categorization
    - Before/after data tracking
    - Request context capture
    - Severity levels
    - Async logging for performance
    """

    # Map actions to categories
    ACTION_CATEGORIES = {
        AuditAction.LOGIN: AuditCategory.AUTHENTICATION,
        AuditAction.LOGIN_FAILED: AuditCategory.AUTHENTICATION,
        AuditAction.LOGOUT: AuditCategory.AUTHENTICATION,
        AuditAction.PASSWORD_CHANGE: AuditCategory.SECURITY,
        AuditAction.PASSWORD_RESET: AuditCategory.SECURITY,
        AuditAction.MFA_ENABLED: AuditCategory.SECURITY,
        AuditAction.MFA_DISABLED: AuditCategory.SECURITY,
        AuditAction.MFA_VERIFIED: AuditCategory.AUTHENTICATION,
        AuditAction.SESSION_REVOKED: AuditCategory.SECURITY,
        AuditAction.USER_CREATE: AuditCategory.USER_MANAGEMENT,
        AuditAction.USER_UPDATE: AuditCategory.USER_MANAGEMENT,
        AuditAction.USER_DELETE: AuditCategory.USER_MANAGEMENT,
        AuditAction.STUDENT_CREATE: AuditCategory.STUDENT_MANAGEMENT,
        AuditAction.STUDENT_UPDATE: AuditCategory.STUDENT_MANAGEMENT,
        AuditAction.GRADE_ENTRY: AuditCategory.ACADEMIC,
        AuditAction.ATTENDANCE_RECORD: AuditCategory.ACADEMIC,
        AuditAction.INVOICE_CREATE: AuditCategory.FINANCIAL,
        AuditAction.PAYMENT_RECORD: AuditCategory.FINANCIAL,
        AuditAction.DATA_EXPORT: AuditCategory.DATA_OPERATIONS,
        AuditAction.BULK_DELETE: AuditCategory.DATA_OPERATIONS,
        AuditAction.SYSTEM_ERROR: AuditCategory.SYSTEM,
        AuditAction.PERMISSION_DENIED: AuditCategory.SECURITY,
    }

    # Severity mapping for certain actions
    ACTION_SEVERITY = {
        AuditAction.LOGIN_FAILED: AuditSeverity.WARNING,
        AuditAction.PASSWORD_RESET: AuditSeverity.WARNING,
        AuditAction.MFA_DISABLED: AuditSeverity.WARNING,
        AuditAction.SESSION_REVOKED: AuditSeverity.WARNING,
        AuditAction.USER_DELETE: AuditSeverity.WARNING,
        AuditAction.STUDENT_DELETE: AuditSeverity.WARNING,
        AuditAction.BULK_DELETE: AuditSeverity.WARNING,
        AuditAction.SYSTEM_ERROR: AuditSeverity.ERROR,
        AuditAction.PERMISSION_DENIED: AuditSeverity.WARNING,
        AuditAction.RATE_LIMIT_EXCEEDED: AuditSeverity.WARNING,
    }

    def __init__(self):
        self.enabled = True

    def _get_category(self, action: Union[AuditAction, str]) -> str:
        """Get category for an action"""
        if isinstance(action, AuditAction):
            return self.ACTION_CATEGORIES.get(action, AuditCategory.SYSTEM).value
        # Try to infer category from action string
        action_lower = action.lower()
        if "auth" in action_lower or "login" in action_lower:
            return AuditCategory.AUTHENTICATION.value
        if "user" in action_lower:
            return AuditCategory.USER_MANAGEMENT.value
        if "student" in action_lower:
            return AuditCategory.STUDENT_MANAGEMENT.value
        if "grade" in action_lower or "attendance" in action_lower:
            return AuditCategory.ACADEMIC.value
        if "payment" in action_lower or "invoice" in action_lower or "fee" in action_lower:
            return AuditCategory.FINANCIAL.value
        return AuditCategory.SYSTEM.value

    def _get_severity(self, action: Union[AuditAction, str]) -> str:
        """Get severity for an action"""
        if isinstance(action, AuditAction):
            return self.ACTION_SEVERITY.get(action, AuditSeverity.INFO).value
        return AuditSeverity.INFO.value

    def _sanitize_data(self, data: Optional[Dict]) -> Optional[Dict]:
        """Remove sensitive fields from audit data"""
        if not data:
            return None

        sensitive_fields = {
            "password", "password_hash", "secret", "secret_key",
            "token", "access_token", "refresh_token", "api_key",
            "backup_codes", "credit_card", "cvv", "ssn"
        }

        def sanitize(obj):
            if isinstance(obj, dict):
                return {
                    k: "[REDACTED]" if k.lower() in sensitive_fields else sanitize(v)
                    for k, v in obj.items()
                }
            elif isinstance(obj, list):
                return [sanitize(item) for item in obj]
            return obj

        return sanitize(data)

    def _extract_request_context(self, request: Optional[Request]) -> Dict[str, Any]:
        """Extract relevant context from request"""
        if not request:
            return {}

        context = {}

        # IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            context["ip_address"] = forwarded.split(",")[0].strip()
        elif request.client:
            context["ip_address"] = request.client.host

        # User agent
        context["user_agent"] = request.headers.get("User-Agent")

        # Request ID
        context["request_id"] = request.headers.get("X-Request-ID")

        return context

    async def log(
        self,
        supabase,
        action: Union[AuditAction, str],
        user_id: Optional[str] = None,
        school_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        before_data: Optional[Dict] = None,
        after_data: Optional[Dict] = None,
        severity: Optional[str] = None,
        category: Optional[str] = None,
        metadata: Optional[Dict] = None,
        request: Optional[Request] = None,
        duration_ms: Optional[int] = None,
        status_code: Optional[int] = None
    ) -> Optional[str]:
        """
        Log an audit entry.

        Args:
            supabase: Supabase client
            action: The action being logged
            user_id: User performing the action
            school_id: School context
            entity_type: Type of entity affected
            entity_id: ID of entity affected
            before_data: State before change
            after_data: State after change
            severity: Log severity level
            category: Log category
            metadata: Additional metadata
            request: FastAPI request object
            duration_ms: Operation duration
            status_code: HTTP status code

        Returns:
            Audit log ID if successful
        """
        if not self.enabled:
            return None

        try:
            # Get action string
            action_str = action.value if isinstance(action, AuditAction) else action

            # Extract request context
            request_context = self._extract_request_context(request)

            # Build audit entry
            entry = {
                "school_id": school_id,
                "user_id": user_id,
                "action": action_str,
                "entity_type": entity_type,
                "entity_id": str(entity_id) if entity_id else None,
                "before_data": self._sanitize_data(before_data),
                "after_data": self._sanitize_data(after_data),
                "ip_address": request_context.get("ip_address"),
                "user_agent": request_context.get("user_agent"),
                "severity": severity or self._get_severity(action),
                "category": category or self._get_category(action),
                "metadata": metadata or {},
                "duration_ms": duration_ms,
                "status_code": status_code,
                "request_id": request_context.get("request_id"),
                "created_at": datetime.utcnow().isoformat()
            }

            # Insert audit log
            result = supabase.table("audit_logs").insert(entry).execute()

            if result.data:
                audit_id = result.data[0]["id"]
                logger.debug(f"Audit logged: {action_str} by {user_id}")
                return audit_id

        except Exception as e:
            logger.error(f"Failed to log audit entry: {e}")

        return None

    async def log_security_event(
        self,
        supabase,
        event_type: str,
        user_id: Optional[str] = None,
        school_id: Optional[str] = None,
        severity: str = AuditSeverity.INFO,
        details: Optional[Dict] = None,
        request: Optional[Request] = None
    ) -> Optional[str]:
        """
        Log a security-specific event.

        Args:
            supabase: Supabase client
            event_type: Type of security event
            user_id: User involved
            school_id: School context
            severity: Event severity
            details: Additional details
            request: FastAPI request

        Returns:
            Security event ID
        """
        try:
            request_context = self._extract_request_context(request)

            entry = {
                "school_id": school_id,
                "user_id": user_id,
                "event_type": event_type,
                "severity": severity,
                "ip_address": request_context.get("ip_address"),
                "user_agent": request_context.get("user_agent"),
                "request_id": request_context.get("request_id"),
                "details": details or {},
                "created_at": datetime.utcnow().isoformat()
            }

            result = supabase.table("security_events").insert(entry).execute()

            if result.data:
                return result.data[0]["id"]

        except Exception as e:
            logger.error(f"Failed to log security event: {e}")

        return None

    async def get_audit_logs(
        self,
        supabase,
        school_id: Optional[str] = None,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Query audit logs with filters.

        Returns:
            Dict with logs and pagination info
        """
        try:
            query = supabase.table("audit_logs").select(
                "*, user_profiles(email, first_name, last_name)"
            )

            if school_id:
                query = query.eq("school_id", school_id)
            if user_id:
                query = query.eq("user_id", user_id)
            if action:
                query = query.eq("action", action)
            if category:
                query = query.eq("category", category)
            if severity:
                query = query.eq("severity", severity)
            if entity_type:
                query = query.eq("entity_type", entity_type)
            if entity_id:
                query = query.eq("entity_id", entity_id)
            if start_date:
                query = query.gte("created_at", start_date.isoformat())
            if end_date:
                query = query.lte("created_at", end_date.isoformat())

            # Get total count
            count_result = query.execute()
            total = len(count_result.data) if count_result.data else 0

            # Get paginated results
            query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
            result = query.execute()

            return {
                "logs": result.data or [],
                "total": total,
                "limit": limit,
                "offset": offset
            }

        except Exception as e:
            logger.error(f"Failed to query audit logs: {e}")
            return {"logs": [], "total": 0, "limit": limit, "offset": offset}

    async def get_user_activity(
        self,
        supabase,
        user_id: str,
        days: int = 30
    ) -> List[Dict]:
        """Get activity summary for a user"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            result = supabase.table("audit_logs").select(
                "action, entity_type, created_at"
            ).eq("user_id", user_id).gte(
                "created_at", start_date.isoformat()
            ).order("created_at", desc=True).limit(100).execute()

            return result.data or []

        except Exception as e:
            logger.error(f"Failed to get user activity: {e}")
            return []


# Global audit logger instance
audit_logger = AuditLogger()


def audit_log(
    action: Union[AuditAction, str],
    entity_type: Optional[str] = None,
    get_entity_id: Optional[callable] = None,
    get_before_data: Optional[callable] = None,
    get_after_data: Optional[callable] = None
):
    """
    Decorator for automatic audit logging.

    Usage:
        @audit_log(AuditAction.STUDENT_UPDATE, entity_type="student")
        async def update_student(student_id: str, data: dict):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()

            # Try to get request and supabase from args/kwargs
            request = kwargs.get("request")
            supabase = kwargs.get("supabase")

            # Get user context
            user_id = None
            school_id = None
            if request and hasattr(request, "state"):
                user_id = getattr(request.state, "user_id", None)
                school_id = getattr(request.state, "school_id", None)

            # Get before data if function provided
            before_data = None
            if get_before_data:
                try:
                    before_data = await get_before_data(*args, **kwargs)
                except Exception:
                    pass

            # Execute the function
            result = await func(*args, **kwargs)

            # Calculate duration
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Get entity ID
            entity_id = None
            if get_entity_id:
                try:
                    entity_id = get_entity_id(*args, **kwargs)
                except Exception:
                    pass

            # Get after data
            after_data = None
            if get_after_data:
                try:
                    after_data = await get_after_data(result)
                except Exception:
                    pass

            # Log the audit entry
            if supabase:
                await audit_logger.log(
                    supabase=supabase,
                    action=action,
                    user_id=user_id,
                    school_id=school_id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    before_data=before_data,
                    after_data=after_data,
                    request=request,
                    duration_ms=duration_ms
                )

            return result

        return wrapper
    return decorator
