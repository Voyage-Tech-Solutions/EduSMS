"""
EduCore Backend - Real-time WebSocket API
WebSocket endpoints for real-time updates and notifications
"""
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from jose import jwt, JWTError

from app.core.config import settings
from app.core.websocket import ws_manager, MessageType
from app.db.supabase import get_supabase_admin

logger = logging.getLogger(__name__)
router = APIRouter()


async def authenticate_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
) -> Optional[dict]:
    """
    Authenticate a WebSocket connection using JWT token.

    Args:
        websocket: The WebSocket connection
        token: JWT token from query parameter

    Returns:
        User data if authenticated, None otherwise
    """
    if not token:
        return None

    try:
        # Verify JWT token
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )

        user_id = payload.get("sub")
        if not user_id:
            return None

        # Get user profile
        supabase = get_supabase_admin()
        result = supabase.table("user_profiles").select(
            "id, email, role, school_id, first_name, last_name"
        ).eq("id", user_id).single().execute()

        if result.data:
            return result.data

    except JWTError as e:
        logger.warning(f"WebSocket auth failed: {e}")
    except Exception as e:
        logger.error(f"WebSocket auth error: {e}")

    return None


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    Main WebSocket endpoint for real-time updates.

    Connect with: ws://host/api/v1/ws?token=<jwt_token>

    Message format:
    {
        "type": "message_type",
        "data": {...}
    }

    Available message types:
    - subscribe: Subscribe to a channel
    - unsubscribe: Unsubscribe from a channel
    - pong: Heartbeat response
    """
    # Authenticate
    user = await authenticate_websocket(websocket, token)

    if not user:
        await websocket.close(code=4001, reason="Authentication required")
        return

    user_id = user["id"]
    school_id = user.get("school_id")
    role = user.get("role")

    # Connect
    conn_id = await ws_manager.connect(
        websocket=websocket,
        user_id=user_id,
        school_id=school_id,
        role=role
    )

    try:
        # Auto-subscribe to user-specific channels
        await ws_manager.subscribe(conn_id, f"user:{user_id}")

        if school_id:
            await ws_manager.subscribe(conn_id, f"school:{school_id}")

            # Role-based channels
            if role in ["principal", "office_admin"]:
                await ws_manager.subscribe(conn_id, f"school:{school_id}:admin")
            if role == "teacher":
                await ws_manager.subscribe(conn_id, f"school:{school_id}:teachers")
            if role == "parent":
                await ws_manager.subscribe(conn_id, f"school:{school_id}:parents")

        # Message loop
        while True:
            try:
                data = await websocket.receive_json()
                await ws_manager.handle_message(conn_id, data)
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket message error: {e}")
                await websocket.send_json({
                    "type": MessageType.ERROR,
                    "message": "Invalid message format"
                })

    finally:
        await ws_manager.disconnect(conn_id)


@router.websocket("/ws/anonymous")
async def anonymous_websocket_endpoint(websocket: WebSocket):
    """
    Anonymous WebSocket for public updates (e.g., school announcements).
    Limited functionality compared to authenticated connections.
    """
    await websocket.accept()

    try:
        # Wait for school code
        data = await websocket.receive_json()
        school_code = data.get("school_code")

        if not school_code:
            await websocket.close(code=4002, reason="School code required")
            return

        # Get school ID from code
        supabase = get_supabase_admin()
        result = supabase.table("schools").select("id").eq(
            "code", school_code
        ).eq("is_active", True).single().execute()

        if not result.data:
            await websocket.close(code=4004, reason="School not found")
            return

        school_id = result.data["id"]

        # Subscribe to public announcements only
        await websocket.send_json({
            "type": MessageType.CONNECTED,
            "school_id": school_id
        })

        # Message loop - only listen, limited sending
        while True:
            try:
                data = await websocket.receive_json()
                # Anonymous connections can only send pong
                if data.get("type") == "pong":
                    pass
            except WebSocketDisconnect:
                break

    except Exception as e:
        logger.error(f"Anonymous WebSocket error: {e}")
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


@router.get("/online-users")
async def get_online_users(
    school_id: Optional[str] = Query(None)
):
    """Get list of online users (admin only)"""
    online = ws_manager.get_online_users(school_id)
    return {
        "online_users": list(online),
        "count": len(online)
    }


@router.get("/connection-stats")
async def get_connection_stats(
    school_id: Optional[str] = Query(None)
):
    """Get WebSocket connection statistics"""
    return {
        "total_connections": ws_manager.get_connection_count(school_id),
        "online_users": len(ws_manager.get_online_users(school_id))
    }
