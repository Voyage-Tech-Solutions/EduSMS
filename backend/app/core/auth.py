"""Auth module - re-exports from security for backward compatibility"""
from app.core.security import (
    get_current_user,
    require_system_admin,
    require_principal,
    require_office_admin,
    require_teacher,
    require_authenticated,
    create_access_token,
    verify_password,
    get_password_hash,
)

def get_user_school_id(user: dict) -> str:
    """Extract school_id from user profile"""
    return user.get("school_id", "")
