"""
EduCore Backend - Authentication API Endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request
from datetime import timedelta

from app.models import (
    UserCreate,
    UserResponse,
    LoginRequest,
    TokenResponse,
    UserRole,
)
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    require_system_admin,
)
from app.core.config import settings
from app.db.supabase import supabase_admin


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    Register a new user.
    System admins can register without school_id.
    Other roles require a valid school_id.
    """
    # Validate school_id requirement
    if user_data.role != UserRole.SYSTEM_ADMIN and not user_data.school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="School ID is required for non-system admin users"
        )
    
    # Check if email already exists
    if supabase_admin:
        existing = supabase_admin.table("users").select("id").eq("email", user_data.email).execute()
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    
    user_dict = {
        "email": user_data.email,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "phone": user_data.phone,
        "password_hash": hashed_password,
        "role": user_data.role.value,
        "school_id": user_data.school_id,
        "is_active": True,
    }
    
    if supabase_admin:
        result = supabase_admin.table("users").insert(user_dict).execute()
        user = result.data[0]
    else:
        # Mock response for development without Supabase
        user = {**user_dict, "id": "mock-user-id"}
    
    # Create access token
    token_data = {
        "sub": user["id"],
        "email": user["email"],
        "role": user_data.role.value,
        "school_id": user_data.school_id,
    }
    access_token = create_access_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            first_name=user["first_name"],
            last_name=user["last_name"],
            phone=user.get("phone"),
            role=user_data.role,
            school_id=user_data.school_id,
            is_active=True,
        )
    )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    """Authenticate user and return access token"""
    
    if supabase_admin:
        result = supabase_admin.table("users").select("*").eq("email", credentials.email).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        user = result.data[0]
        
        if not verify_password(credentials.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled"
            )
    else:
        # Mock response for development without Supabase
        user = {
            "id": "mock-user-id",
            "email": credentials.email,
            "first_name": "Test",
            "last_name": "User",
            "role": "principal",
            "school_id": "mock-school-id",
            "is_active": True,
        }
    
    # Create access token
    token_data = {
        "sub": user["id"],
        "email": user["email"],
        "role": user["role"],
        "school_id": user.get("school_id"),
    }
    access_token = create_access_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            first_name=user["first_name"],
            last_name=user["last_name"],
            phone=user.get("phone"),
            role=UserRole(user["role"]),
            school_id=user.get("school_id"),
            is_active=user.get("is_active", True),
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user profile"""
    
    if supabase_admin:
        result = supabase_admin.table("users").select("*").eq("id", current_user["id"]).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = result.data[0]
    else:
        user = {
            "id": current_user["id"],
            "email": current_user["email"],
            "first_name": "Test",
            "last_name": "User",
            "role": current_user["role"],
            "school_id": current_user.get("school_id"),
            "is_active": True,
        }
    
    return UserResponse(
        id=user["id"],
        email=user["email"],
        first_name=user["first_name"],
        last_name=user["last_name"],
        phone=user.get("phone"),
        role=UserRole(user["role"]),
        school_id=user.get("school_id"),
        is_active=user.get("is_active", True),
    )


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout current user (client-side token removal)"""
    # JWT tokens are stateless, so we just return success
    # Client should remove the token from storage
    return {"message": "Successfully logged out"}
