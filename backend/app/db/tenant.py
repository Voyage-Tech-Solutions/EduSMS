"""
EduCore Backend - Tenant Context Manager
"""
from contextvars import ContextVar
from typing import Optional


# Context variable to store current tenant (school_id)
current_school_id: ContextVar[Optional[str]] = ContextVar("current_school_id", default=None)


def set_tenant(school_id: str) -> None:
    """Set the current tenant context"""
    current_school_id.set(school_id)


def get_tenant() -> Optional[str]:
    """Get the current tenant context"""
    return current_school_id.get()


def clear_tenant() -> None:
    """Clear the current tenant context"""
    current_school_id.set(None)


class TenantContext:
    """Context manager for tenant operations"""
    
    def __init__(self, school_id: str):
        self.school_id = school_id
        self.previous_school_id = None
    
    def __enter__(self):
        self.previous_school_id = get_tenant()
        set_tenant(self.school_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.previous_school_id:
            set_tenant(self.previous_school_id)
        else:
            clear_tenant()
        return False
