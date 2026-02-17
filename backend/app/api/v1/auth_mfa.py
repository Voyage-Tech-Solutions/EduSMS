"""
EduCore Backend - MFA Authentication API
Endpoints for Multi-Factor Authentication setup and verification
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user, get_supabase
from app.core.mfa import mfa_service
from app.core.sessions import session_manager
from app.core.audit import audit_logger, AuditAction

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth/mfa", tags=["auth", "mfa"])


class MFASetupResponse(BaseModel):
    """Response for MFA setup initiation"""
    secret: str
    qr_code: str  # Base64 encoded PNG
    provisioning_uri: str
    message: str


class MFAVerifyRequest(BaseModel):
    """Request to verify MFA code"""
    code: str


class MFAVerifyResponse(BaseModel):
    """Response for MFA verification"""
    success: bool
    backup_codes: Optional[list] = None
    warning: Optional[str] = None
    message: Optional[str] = None


class MFAStatusResponse(BaseModel):
    """Response for MFA status check"""
    is_enabled: bool
    is_configured: bool
    is_verified: Optional[bool] = None
    recovery_email: Optional[str] = None
    backup_codes_remaining: Optional[int] = None
    configured_at: Optional[str] = None
    last_used_at: Optional[str] = None


class MFADisableRequest(BaseModel):
    """Request to disable MFA"""
    code: str


class BackupCodesResponse(BaseModel):
    """Response with regenerated backup codes"""
    success: bool
    backup_codes: Optional[list] = None
    message: str
    warning: Optional[str] = None


@router.get("/status", response_model=MFAStatusResponse)
async def get_mfa_status(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Get the current MFA status for the authenticated user.
    """
    user_id = current_user["id"]
    status = await mfa_service.get_mfa_status(supabase, user_id)
    return MFAStatusResponse(**status)


@router.post("/setup", response_model=MFASetupResponse)
async def setup_mfa(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Initialize MFA setup for the current user.

    Returns a QR code to scan with an authenticator app
    (Google Authenticator, Authy, Microsoft Authenticator, etc.)

    After scanning, verify with the generated code using /verify-setup endpoint.
    """
    user_id = current_user["id"]
    user_email = current_user["email"]
    user_name = f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip()

    result = await mfa_service.setup_mfa(
        supabase=supabase,
        user_id=user_id,
        user_email=user_email,
        user_name=user_name or None
    )

    return MFASetupResponse(**result)


@router.post("/verify-setup", response_model=MFAVerifyResponse)
async def verify_mfa_setup(
    request: MFAVerifyRequest,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Verify MFA setup with a code from the authenticator app.

    This endpoint enables MFA for the user and returns backup codes.
    **Save the backup codes securely - they cannot be retrieved again.**
    """
    user_id = current_user["id"]
    school_id = current_user.get("school_id")

    result = await mfa_service.verify_and_enable_mfa(
        supabase=supabase,
        user_id=user_id,
        code=request.code
    )

    if result["success"]:
        # Log the MFA enable event
        await audit_logger.log(
            supabase=supabase,
            action=AuditAction.MFA_ENABLED,
            user_id=user_id,
            school_id=school_id,
            entity_type="user_mfa",
            entity_id=user_id
        )

    return MFAVerifyResponse(**result)


@router.post("/verify", response_model=MFAVerifyResponse)
async def verify_mfa_code(
    request: MFAVerifyRequest,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Verify an MFA code during login or sensitive operation.

    Accepts either:
    - A 6-digit TOTP code from the authenticator app
    - A backup code (format: XXXX-XXXX)
    """
    user_id = current_user["id"]
    school_id = current_user.get("school_id")

    result = await mfa_service.verify_mfa_code(
        supabase=supabase,
        user_id=user_id,
        code=request.code
    )

    if result["success"]:
        # Log successful MFA verification
        await audit_logger.log(
            supabase=supabase,
            action=AuditAction.MFA_VERIFIED,
            user_id=user_id,
            school_id=school_id,
            metadata={"method": result.get("method")}
        )

        # Mark session as MFA verified
        session_id = getattr(current_user, "session_id", None)
        if session_id:
            await session_manager.mark_mfa_verified(supabase, session_id)

    return MFAVerifyResponse(**result)


@router.post("/disable", response_model=MFAVerifyResponse)
async def disable_mfa(
    request: MFADisableRequest,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Disable MFA for the current user.

    Requires verification with current MFA code for security.
    """
    user_id = current_user["id"]
    school_id = current_user.get("school_id")

    # Check if MFA disable is allowed for this user's role
    role = current_user.get("role")
    if role == "system_admin":
        raise HTTPException(
            status_code=403,
            detail="System administrators cannot disable MFA"
        )

    result = await mfa_service.disable_mfa(
        supabase=supabase,
        user_id=user_id,
        code=request.code
    )

    if result["success"]:
        # Log MFA disable event
        await audit_logger.log(
            supabase=supabase,
            action=AuditAction.MFA_DISABLED,
            user_id=user_id,
            school_id=school_id,
            entity_type="user_mfa",
            entity_id=user_id,
            severity="warning"
        )

    return MFAVerifyResponse(**result)


@router.post("/regenerate-backup-codes", response_model=BackupCodesResponse)
async def regenerate_backup_codes(
    request: MFAVerifyRequest,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Generate new backup codes.

    Requires verification with current MFA code.
    Previous backup codes will be invalidated.
    **Save the new backup codes securely - they cannot be retrieved again.**
    """
    user_id = current_user["id"]
    school_id = current_user.get("school_id")

    result = await mfa_service.regenerate_backup_codes(
        supabase=supabase,
        user_id=user_id,
        code=request.code
    )

    if result["success"]:
        # Log backup codes regeneration
        await audit_logger.log(
            supabase=supabase,
            action="auth.mfa_backup_codes_regenerated",
            user_id=user_id,
            school_id=school_id,
            entity_type="user_mfa",
            entity_id=user_id
        )

    return BackupCodesResponse(**result)


@router.get("/required")
async def check_mfa_required(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Check if MFA is required for the current user.

    Based on:
    - User role
    - School security settings
    - System configuration
    """
    user_id = current_user["id"]
    school_id = current_user.get("school_id")

    is_required = await mfa_service.check_mfa_required(
        supabase=supabase,
        user_id=user_id,
        school_id=school_id
    )

    # Also get current MFA status
    status = await mfa_service.get_mfa_status(supabase, user_id)

    return {
        "mfa_required": is_required,
        "mfa_enabled": status["is_enabled"],
        "needs_setup": is_required and not status["is_enabled"]
    }
