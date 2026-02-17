"""
EduCore Backend - Session Management System
Handles user sessions, device tracking, and session security
"""
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
import json

from pydantic import BaseModel
from user_agents import parse as parse_user_agent

from app.core.config import settings
from app.core.cache import cache

logger = logging.getLogger(__name__)


class SessionInfo(BaseModel):
    """Session information model"""
    id: str
    user_id: str
    ip_address: Optional[str] = None
    device_type: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    is_current: bool = False
    is_mfa_verified: bool = False
    created_at: datetime
    last_activity: datetime
    expires_at: datetime


class SessionManager:
    """
    Manages user sessions with support for:
    - Multiple concurrent sessions
    - Device tracking
    - Session revocation
    - Activity tracking
    """

    def __init__(self):
        self.session_duration = timedelta(hours=24)
        self.refresh_threshold = timedelta(hours=1)
        self.max_sessions = settings.MAX_CONCURRENT_SESSIONS

    def _hash_token(self, token: str) -> str:
        """Hash a session token for storage"""
        return hashlib.sha256(token.encode()).hexdigest()

    def _generate_token(self) -> str:
        """Generate a secure session token"""
        return secrets.token_urlsafe(32)

    def _parse_user_agent(self, user_agent: str) -> Dict[str, str]:
        """Parse user agent string into device info"""
        try:
            ua = parse_user_agent(user_agent)
            return {
                "device_type": "mobile" if ua.is_mobile else "tablet" if ua.is_tablet else "desktop",
                "browser": f"{ua.browser.family} {ua.browser.version_string}",
                "os": f"{ua.os.family} {ua.os.version_string}",
                "device": ua.device.family if ua.device.family != "Other" else None
            }
        except Exception:
            return {
                "device_type": "unknown",
                "browser": "unknown",
                "os": "unknown",
                "device": None
            }

    async def create_session(
        self,
        supabase,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        is_mfa_verified: bool = False,
        location: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create a new session for a user.

        Args:
            supabase: Supabase client
            user_id: User UUID
            ip_address: Client IP address
            user_agent: Client user agent string
            is_mfa_verified: Whether MFA was completed
            location: Optional location data

        Returns:
            Session data including token
        """
        # Generate tokens
        session_token = self._generate_token()
        refresh_token = self._generate_token()

        # Parse device info
        device_info = self._parse_user_agent(user_agent or "")

        now = datetime.utcnow()
        expires_at = now + self.session_duration

        # Check and enforce max sessions limit
        await self._enforce_session_limit(supabase, user_id)

        # Create session record
        session_data = {
            "user_id": user_id,
            "token_hash": self._hash_token(session_token),
            "refresh_token_hash": self._hash_token(refresh_token),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "device_info": device_info,
            "location": location or {},
            "is_active": True,
            "is_mfa_verified": is_mfa_verified,
            "last_activity": now.isoformat(),
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat()
        }

        result = supabase.table("user_sessions").insert(session_data).execute()

        if not result.data:
            raise Exception("Failed to create session")

        session_id = result.data[0]["id"]

        # Cache session for fast validation
        cache.set(
            "session",
            self._hash_token(session_token),
            {
                "session_id": session_id,
                "user_id": user_id,
                "is_mfa_verified": is_mfa_verified,
                "expires_at": expires_at.isoformat()
            },
            ttl=int(self.session_duration.total_seconds())
        )

        logger.info(f"Session created for user {user_id} from {ip_address}")

        return {
            "session_id": session_id,
            "session_token": session_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at.isoformat(),
            "device_info": device_info
        }

    async def _enforce_session_limit(self, supabase, user_id: str):
        """Remove oldest sessions if limit exceeded"""
        # Get active sessions count
        result = supabase.table("user_sessions").select(
            "id, created_at"
        ).eq("user_id", user_id).eq("is_active", True).order(
            "created_at", desc=False
        ).execute()

        sessions = result.data or []

        if len(sessions) >= self.max_sessions:
            # Revoke oldest sessions
            sessions_to_revoke = sessions[:len(sessions) - self.max_sessions + 1]
            for session in sessions_to_revoke:
                await self.revoke_session(
                    supabase,
                    session["id"],
                    reason="max_sessions_exceeded"
                )

    async def validate_session(
        self,
        supabase,
        session_token: str,
        update_activity: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Validate a session token.

        Args:
            supabase: Supabase client
            session_token: Session token to validate
            update_activity: Whether to update last activity timestamp

        Returns:
            Session data if valid, None otherwise
        """
        token_hash = self._hash_token(session_token)

        # Check cache first
        cached = cache.get("session", token_hash)
        if cached:
            expires_at = datetime.fromisoformat(cached["expires_at"])
            if expires_at > datetime.utcnow():
                if update_activity:
                    # Update last activity in background
                    await self._update_activity(supabase, cached["session_id"])
                return cached
            else:
                # Session expired, remove from cache
                cache.delete("session", token_hash)

        # Check database
        result = supabase.table("user_sessions").select(
            "id, user_id, is_mfa_verified, expires_at, is_active"
        ).eq("token_hash", token_hash).single().execute()

        if not result.data:
            return None

        session = result.data

        if not session["is_active"]:
            return None

        expires_at = datetime.fromisoformat(session["expires_at"].replace("Z", ""))
        if expires_at < datetime.utcnow():
            # Session expired
            await self.revoke_session(supabase, session["id"], reason="expired")
            return None

        # Cache the valid session
        session_data = {
            "session_id": session["id"],
            "user_id": session["user_id"],
            "is_mfa_verified": session["is_mfa_verified"],
            "expires_at": session["expires_at"]
        }

        remaining_seconds = int((expires_at - datetime.utcnow()).total_seconds())
        cache.set("session", token_hash, session_data, ttl=remaining_seconds)

        if update_activity:
            await self._update_activity(supabase, session["id"])

        return session_data

    async def _update_activity(self, supabase, session_id: str):
        """Update session last activity timestamp"""
        try:
            supabase.table("user_sessions").update({
                "last_activity": datetime.utcnow().isoformat()
            }).eq("id", session_id).execute()
        except Exception as e:
            logger.error(f"Failed to update session activity: {e}")

    async def refresh_session(
        self,
        supabase,
        refresh_token: str,
        ip_address: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Refresh a session using refresh token.

        Args:
            supabase: Supabase client
            refresh_token: Refresh token
            ip_address: Current IP address

        Returns:
            New session tokens if valid
        """
        token_hash = self._hash_token(refresh_token)

        # Find session by refresh token
        result = supabase.table("user_sessions").select(
            "id, user_id, is_mfa_verified, expires_at, is_active, token_hash"
        ).eq("refresh_token_hash", token_hash).single().execute()

        if not result.data:
            return None

        session = result.data

        if not session["is_active"]:
            return None

        # Generate new tokens
        new_session_token = self._generate_token()
        new_refresh_token = self._generate_token()
        new_expires = datetime.utcnow() + self.session_duration

        # Update session with new tokens
        supabase.table("user_sessions").update({
            "token_hash": self._hash_token(new_session_token),
            "refresh_token_hash": self._hash_token(new_refresh_token),
            "expires_at": new_expires.isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "ip_address": ip_address
        }).eq("id", session["id"]).execute()

        # Invalidate old cache entry
        cache.delete("session", session["token_hash"])

        # Cache new session
        cache.set(
            "session",
            self._hash_token(new_session_token),
            {
                "session_id": session["id"],
                "user_id": session["user_id"],
                "is_mfa_verified": session["is_mfa_verified"],
                "expires_at": new_expires.isoformat()
            },
            ttl=int(self.session_duration.total_seconds())
        )

        logger.info(f"Session refreshed for user {session['user_id']}")

        return {
            "session_token": new_session_token,
            "refresh_token": new_refresh_token,
            "expires_at": new_expires.isoformat()
        }

    async def revoke_session(
        self,
        supabase,
        session_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Revoke a specific session.

        Args:
            supabase: Supabase client
            session_id: Session UUID to revoke
            reason: Reason for revocation

        Returns:
            True if successful
        """
        try:
            # Get token hash for cache invalidation
            result = supabase.table("user_sessions").select(
                "token_hash"
            ).eq("id", session_id).single().execute()

            if result.data:
                cache.delete("session", result.data["token_hash"])

            # Update session as revoked
            supabase.table("user_sessions").update({
                "is_active": False,
                "revoked_at": datetime.utcnow().isoformat(),
                "revoked_reason": reason
            }).eq("id", session_id).execute()

            logger.info(f"Session {session_id} revoked: {reason}")
            return True

        except Exception as e:
            logger.error(f"Failed to revoke session: {e}")
            return False

    async def revoke_all_sessions(
        self,
        supabase,
        user_id: str,
        except_session_id: Optional[str] = None,
        reason: Optional[str] = None
    ) -> int:
        """
        Revoke all sessions for a user.

        Args:
            supabase: Supabase client
            user_id: User UUID
            except_session_id: Session to keep (current session)
            reason: Reason for revocation

        Returns:
            Number of sessions revoked
        """
        # Get all active sessions
        query = supabase.table("user_sessions").select(
            "id, token_hash"
        ).eq("user_id", user_id).eq("is_active", True)

        if except_session_id:
            query = query.neq("id", except_session_id)

        result = query.execute()
        sessions = result.data or []

        # Invalidate cache entries
        for session in sessions:
            cache.delete("session", session["token_hash"])

        # Bulk update
        update_query = supabase.table("user_sessions").update({
            "is_active": False,
            "revoked_at": datetime.utcnow().isoformat(),
            "revoked_reason": reason or "bulk_revocation"
        }).eq("user_id", user_id).eq("is_active", True)

        if except_session_id:
            update_query = update_query.neq("id", except_session_id)

        update_query.execute()

        logger.info(f"Revoked {len(sessions)} sessions for user {user_id}")
        return len(sessions)

    async def get_user_sessions(
        self,
        supabase,
        user_id: str,
        current_session_id: Optional[str] = None
    ) -> List[SessionInfo]:
        """
        Get all active sessions for a user.

        Args:
            supabase: Supabase client
            user_id: User UUID
            current_session_id: ID of current session (for marking)

        Returns:
            List of session information
        """
        result = supabase.table("user_sessions").select(
            "id, ip_address, device_info, location, is_mfa_verified, "
            "created_at, last_activity, expires_at"
        ).eq("user_id", user_id).eq("is_active", True).order(
            "last_activity", desc=True
        ).execute()

        sessions = []
        for session in (result.data or []):
            device_info = session.get("device_info") or {}
            sessions.append(SessionInfo(
                id=session["id"],
                user_id=user_id,
                ip_address=session.get("ip_address"),
                device_type=device_info.get("device_type"),
                browser=device_info.get("browser"),
                os=device_info.get("os"),
                location=session.get("location"),
                is_current=session["id"] == current_session_id,
                is_mfa_verified=session.get("is_mfa_verified", False),
                created_at=session["created_at"],
                last_activity=session["last_activity"],
                expires_at=session["expires_at"]
            ))

        return sessions

    async def mark_mfa_verified(
        self,
        supabase,
        session_id: str
    ) -> bool:
        """Mark a session as MFA verified"""
        try:
            # Update database
            supabase.table("user_sessions").update({
                "is_mfa_verified": True
            }).eq("id", session_id).execute()

            # Update cache
            result = supabase.table("user_sessions").select(
                "token_hash, user_id, expires_at"
            ).eq("id", session_id).single().execute()

            if result.data:
                cache.set(
                    "session",
                    result.data["token_hash"],
                    {
                        "session_id": session_id,
                        "user_id": result.data["user_id"],
                        "is_mfa_verified": True,
                        "expires_at": result.data["expires_at"]
                    }
                )

            return True
        except Exception as e:
            logger.error(f"Failed to mark MFA verified: {e}")
            return False

    async def cleanup_expired_sessions(self, supabase) -> int:
        """
        Clean up expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        try:
            # Get expired sessions
            result = supabase.table("user_sessions").select(
                "id, token_hash"
            ).eq("is_active", True).lt(
                "expires_at", datetime.utcnow().isoformat()
            ).execute()

            sessions = result.data or []

            # Invalidate cache
            for session in sessions:
                cache.delete("session", session["token_hash"])

            # Update as inactive
            supabase.table("user_sessions").update({
                "is_active": False,
                "revoked_at": datetime.utcnow().isoformat(),
                "revoked_reason": "expired"
            }).eq("is_active", True).lt(
                "expires_at", datetime.utcnow().isoformat()
            ).execute()

            logger.info(f"Cleaned up {len(sessions)} expired sessions")
            return len(sessions)

        except Exception as e:
            logger.error(f"Session cleanup error: {e}")
            return 0


# Global session manager instance
session_manager = SessionManager()
