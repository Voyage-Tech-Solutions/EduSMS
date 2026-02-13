"""
EduCore Backend - Security & Authentication
"""
from datetime import datetime, timedelta
from typing import Optional, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client

from app.core.config import settings
from app.db.supabase import get_supabase_client

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token scheme
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token (Legacy/Local Dev)"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Get current authenticated user from Supabase token"""
    token = credentials.credentials
    
    try:
        # Use admin client to verify token
        from app.db.supabase import get_supabase_admin
        supabase = get_supabase_admin()
        
        # Verify token with Supabase admin client
        user_response = supabase.auth.get_user(token)
        user = user_response.user
        
        if not user:
             raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
            )
            
        # Fetch user profile including role
        profile_response = supabase.table("user_profiles").select("*").eq("id", user.id).single().execute()
        
        if not profile_response.data:
             # Fallback for users without profile
             return {
                "id": user.id,
                "email": user.email,
                "role": "student",
                "school_id": None
             }
             
        profile = profile_response.data

        return {
            "id": profile["id"],
            "email": profile["email"],
            "role": profile["role"],
            "school_id": profile["school_id"],
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Auth Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


class RoleChecker:
    """Dependency to check if user has required role"""
    
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return user


# Role checker instances for common use
require_system_admin = RoleChecker(["system_admin"])
require_principal = RoleChecker(["system_admin", "principal"])
require_office_admin = RoleChecker(["system_admin", "principal", "office_admin"])
require_teacher = RoleChecker(["system_admin", "principal", "office_admin", "teacher"])
require_authenticated = RoleChecker(["system_admin", "principal", "office_admin", "teacher", "parent", "student"])
