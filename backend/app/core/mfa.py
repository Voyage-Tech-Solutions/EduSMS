"""
EduCore Backend - Multi-Factor Authentication (MFA) Module
TOTP-based MFA implementation compatible with Google Authenticator, Authy, etc.
"""
import pyotp
import qrcode
import secrets
import hashlib
import logging
from io import BytesIO
from base64 import b64encode
from typing import Optional, List, Tuple
from datetime import datetime, timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)


class MFAManager:
    """
    Manages TOTP-based Multi-Factor Authentication.
    Compatible with Google Authenticator, Authy, Microsoft Authenticator, etc.
    """

    def __init__(self):
        self.issuer = settings.APP_NAME
        self.digits = 6
        self.interval = 30  # seconds
        self.backup_code_length = 8
        self.backup_code_count = 10

    def generate_secret(self) -> str:
        """
        Generate a new TOTP secret key.

        Returns:
            Base32-encoded secret key
        """
        return pyotp.random_base32()

    def get_totp(self, secret: str) -> pyotp.TOTP:
        """
        Get a TOTP object for the given secret.

        Args:
            secret: Base32-encoded secret key

        Returns:
            TOTP object
        """
        return pyotp.TOTP(
            secret,
            digits=self.digits,
            interval=self.interval
        )

    def generate_provisioning_uri(
        self,
        secret: str,
        user_email: str,
        user_name: Optional[str] = None
    ) -> str:
        """
        Generate the provisioning URI for authenticator apps.

        Args:
            secret: Base32-encoded secret key
            user_email: User's email address
            user_name: Optional display name

        Returns:
            otpauth:// URI string
        """
        totp = self.get_totp(secret)
        label = user_name if user_name else user_email

        return totp.provisioning_uri(
            name=label,
            issuer_name=self.issuer
        )

    def generate_qr_code(
        self,
        secret: str,
        user_email: str,
        user_name: Optional[str] = None
    ) -> str:
        """
        Generate a QR code image for the TOTP secret.

        Args:
            secret: Base32-encoded secret key
            user_email: User's email address
            user_name: Optional display name

        Returns:
            Base64-encoded PNG image
        """
        uri = self.generate_provisioning_uri(secret, user_email, user_name)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        return b64encode(buffer.getvalue()).decode("utf-8")

    def verify_code(
        self,
        secret: str,
        code: str,
        valid_window: int = 1
    ) -> bool:
        """
        Verify a TOTP code.

        Args:
            secret: Base32-encoded secret key
            code: The 6-digit code to verify
            valid_window: Number of 30-second windows to check (1 = +/- 30 seconds)

        Returns:
            True if the code is valid, False otherwise
        """
        try:
            totp = self.get_totp(secret)
            return totp.verify(code, valid_window=valid_window)
        except Exception as e:
            logger.error(f"TOTP verification error: {e}")
            return False

    def get_current_code(self, secret: str) -> str:
        """
        Get the current TOTP code (for testing purposes).

        Args:
            secret: Base32-encoded secret key

        Returns:
            Current 6-digit code
        """
        totp = self.get_totp(secret)
        return totp.now()

    def generate_backup_codes(self) -> Tuple[List[str], List[str]]:
        """
        Generate backup codes for account recovery.

        Returns:
            Tuple of (plain_codes, hashed_codes)
            - plain_codes: Display to user once
            - hashed_codes: Store in database
        """
        plain_codes = []
        hashed_codes = []

        for _ in range(self.backup_code_count):
            # Generate a random code
            code = secrets.token_hex(self.backup_code_length // 2).upper()
            # Format with dashes for readability: XXXX-XXXX
            formatted_code = f"{code[:4]}-{code[4:]}"
            plain_codes.append(formatted_code)

            # Hash for storage
            hashed = self._hash_backup_code(formatted_code)
            hashed_codes.append(hashed)

        return plain_codes, hashed_codes

    def _hash_backup_code(self, code: str) -> str:
        """
        Hash a backup code for secure storage.

        Args:
            code: Plain text backup code

        Returns:
            SHA-256 hash of the code
        """
        # Normalize the code (remove dashes, lowercase)
        normalized = code.replace("-", "").lower()
        return hashlib.sha256(normalized.encode()).hexdigest()

    def verify_backup_code(
        self,
        code: str,
        hashed_codes: List[str]
    ) -> Tuple[bool, Optional[int]]:
        """
        Verify a backup code against stored hashes.

        Args:
            code: The backup code to verify
            hashed_codes: List of hashed backup codes

        Returns:
            Tuple of (is_valid, index) - index of the used code if valid
        """
        hashed_input = self._hash_backup_code(code)

        for index, stored_hash in enumerate(hashed_codes):
            if secrets.compare_digest(hashed_input, stored_hash):
                return True, index

        return False, None


class MFAService:
    """
    Service layer for MFA operations with database integration.
    """

    def __init__(self):
        self.manager = MFAManager()

    async def setup_mfa(
        self,
        supabase,
        user_id: str,
        user_email: str,
        user_name: Optional[str] = None
    ) -> dict:
        """
        Initialize MFA setup for a user.

        Args:
            supabase: Supabase client
            user_id: User UUID
            user_email: User's email
            user_name: Optional display name

        Returns:
            Setup data including secret and QR code
        """
        # Generate new secret
        secret = self.manager.generate_secret()

        # Check if user already has MFA record
        existing = supabase.table("user_mfa").select("id").eq(
            "user_id", user_id
        ).execute()

        if existing.data:
            # Update existing record
            supabase.table("user_mfa").update({
                "secret_key": secret,
                "is_enabled": False,
                "is_verified": False,
                "backup_codes": None,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("user_id", user_id).execute()
        else:
            # Create new record
            supabase.table("user_mfa").insert({
                "user_id": user_id,
                "secret_key": secret,
                "is_enabled": False,
                "is_verified": False,
                "recovery_email": user_email
            }).execute()

        # Generate QR code
        qr_code = self.manager.generate_qr_code(secret, user_email, user_name)
        provisioning_uri = self.manager.generate_provisioning_uri(
            secret, user_email, user_name
        )

        return {
            "secret": secret,
            "qr_code": qr_code,
            "provisioning_uri": provisioning_uri,
            "message": "Scan the QR code with your authenticator app, then verify with a code"
        }

    async def verify_and_enable_mfa(
        self,
        supabase,
        user_id: str,
        code: str
    ) -> dict:
        """
        Verify TOTP code and enable MFA for the user.

        Args:
            supabase: Supabase client
            user_id: User UUID
            code: TOTP code from authenticator app

        Returns:
            Result including backup codes
        """
        # Get user's MFA record
        result = supabase.table("user_mfa").select(
            "secret_key, is_enabled"
        ).eq("user_id", user_id).single().execute()

        if not result.data:
            return {
                "success": False,
                "error": "MFA not set up. Please start the setup process first."
            }

        if result.data["is_enabled"]:
            return {
                "success": False,
                "error": "MFA is already enabled for this account."
            }

        secret = result.data["secret_key"]

        # Verify the code
        if not self.manager.verify_code(secret, code):
            return {
                "success": False,
                "error": "Invalid verification code. Please try again."
            }

        # Generate backup codes
        plain_codes, hashed_codes = self.manager.generate_backup_codes()

        # Enable MFA
        supabase.table("user_mfa").update({
            "is_enabled": True,
            "is_verified": True,
            "backup_codes": hashed_codes,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("user_id", user_id).execute()

        logger.info(f"MFA enabled for user {user_id}")

        return {
            "success": True,
            "message": "MFA has been successfully enabled",
            "backup_codes": plain_codes,
            "warning": "Save these backup codes in a secure place. They can only be shown once."
        }

    async def verify_mfa_code(
        self,
        supabase,
        user_id: str,
        code: str
    ) -> dict:
        """
        Verify a TOTP code during login.

        Args:
            supabase: Supabase client
            user_id: User UUID
            code: TOTP code or backup code

        Returns:
            Verification result
        """
        # Get user's MFA record
        result = supabase.table("user_mfa").select(
            "secret_key, is_enabled, backup_codes"
        ).eq("user_id", user_id).single().execute()

        if not result.data:
            return {"success": False, "error": "MFA not configured"}

        if not result.data["is_enabled"]:
            return {"success": False, "error": "MFA not enabled"}

        secret = result.data["secret_key"]
        backup_codes = result.data.get("backup_codes") or []

        # First try TOTP verification
        if self.manager.verify_code(secret, code):
            # Update last used timestamp
            supabase.table("user_mfa").update({
                "last_used_at": datetime.utcnow().isoformat()
            }).eq("user_id", user_id).execute()

            return {"success": True, "method": "totp"}

        # Try backup code verification
        is_valid, code_index = self.manager.verify_backup_code(code, backup_codes)

        if is_valid:
            # Remove the used backup code
            backup_codes.pop(code_index)
            supabase.table("user_mfa").update({
                "backup_codes": backup_codes,
                "last_used_at": datetime.utcnow().isoformat()
            }).eq("user_id", user_id).execute()

            remaining_codes = len(backup_codes)
            logger.info(f"Backup code used for user {user_id}. {remaining_codes} remaining.")

            return {
                "success": True,
                "method": "backup_code",
                "remaining_backup_codes": remaining_codes,
                "warning": "You used a backup code. Consider regenerating backup codes." if remaining_codes < 3 else None
            }

        return {"success": False, "error": "Invalid verification code"}

    async def disable_mfa(
        self,
        supabase,
        user_id: str,
        code: str
    ) -> dict:
        """
        Disable MFA for a user after verification.

        Args:
            supabase: Supabase client
            user_id: User UUID
            code: TOTP code for verification

        Returns:
            Result of the operation
        """
        # Verify current MFA first
        verification = await self.verify_mfa_code(supabase, user_id, code)

        if not verification["success"]:
            return {
                "success": False,
                "error": "Invalid verification code. MFA was not disabled."
            }

        # Delete MFA record
        supabase.table("user_mfa").delete().eq("user_id", user_id).execute()

        logger.info(f"MFA disabled for user {user_id}")

        return {
            "success": True,
            "message": "MFA has been disabled for your account"
        }

    async def regenerate_backup_codes(
        self,
        supabase,
        user_id: str,
        code: str
    ) -> dict:
        """
        Regenerate backup codes after verifying current MFA.

        Args:
            supabase: Supabase client
            user_id: User UUID
            code: TOTP code for verification

        Returns:
            New backup codes
        """
        # Get MFA record
        result = supabase.table("user_mfa").select(
            "secret_key, is_enabled"
        ).eq("user_id", user_id).single().execute()

        if not result.data or not result.data["is_enabled"]:
            return {
                "success": False,
                "error": "MFA is not enabled for this account"
            }

        # Verify TOTP code
        if not self.manager.verify_code(result.data["secret_key"], code):
            return {
                "success": False,
                "error": "Invalid verification code"
            }

        # Generate new backup codes
        plain_codes, hashed_codes = self.manager.generate_backup_codes()

        # Update database
        supabase.table("user_mfa").update({
            "backup_codes": hashed_codes,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("user_id", user_id).execute()

        logger.info(f"Backup codes regenerated for user {user_id}")

        return {
            "success": True,
            "backup_codes": plain_codes,
            "message": "New backup codes generated. Previous codes are now invalid.",
            "warning": "Save these backup codes in a secure place. They can only be shown once."
        }

    async def get_mfa_status(
        self,
        supabase,
        user_id: str
    ) -> dict:
        """
        Get MFA status for a user.

        Args:
            supabase: Supabase client
            user_id: User UUID

        Returns:
            MFA status information
        """
        result = supabase.table("user_mfa").select(
            "is_enabled, is_verified, recovery_email, last_used_at, created_at, backup_codes"
        ).eq("user_id", user_id).single().execute()

        if not result.data:
            return {
                "is_enabled": False,
                "is_configured": False
            }

        backup_codes = result.data.get("backup_codes") or []

        return {
            "is_enabled": result.data["is_enabled"],
            "is_configured": True,
            "is_verified": result.data["is_verified"],
            "recovery_email": result.data.get("recovery_email"),
            "last_used_at": result.data.get("last_used_at"),
            "configured_at": result.data["created_at"],
            "backup_codes_remaining": len(backup_codes)
        }

    async def check_mfa_required(
        self,
        supabase,
        user_id: str,
        school_id: Optional[str] = None
    ) -> bool:
        """
        Check if MFA is required for a user based on school settings.

        Args:
            supabase: Supabase client
            user_id: User UUID
            school_id: Optional school UUID

        Returns:
            True if MFA is required
        """
        # Get user role
        user_result = supabase.table("user_profiles").select(
            "role, school_id"
        ).eq("id", user_id).single().execute()

        if not user_result.data:
            return False

        user_role = user_result.data["role"]
        user_school_id = school_id or user_result.data.get("school_id")

        # System admins always require MFA in production
        if user_role == "system_admin" and settings.MFA_ENABLED:
            return True

        if not user_school_id:
            return False

        # Check school security settings
        settings_result = supabase.table("security_settings").select(
            "mfa_required, mfa_required_roles"
        ).eq("school_id", user_school_id).single().execute()

        if not settings_result.data:
            return False

        # Check if MFA is globally required for school
        if settings_result.data.get("mfa_required"):
            return True

        # Check if MFA is required for this role
        mfa_roles = settings_result.data.get("mfa_required_roles") or []
        return user_role in mfa_roles


# Global MFA service instance
mfa_service = MFAService()
