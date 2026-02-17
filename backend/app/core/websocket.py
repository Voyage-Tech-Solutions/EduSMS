"""
EduCore Backend - WebSocket Manager
Real-time communication infrastructure for notifications and live updates
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Set, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.core.cache import get_redis_client

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """WebSocket message types"""
    # System messages
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"

    # Notifications
    NOTIFICATION = "notification"
    ANNOUNCEMENT = "announcement"
    ALERT = "alert"

    # Real-time updates
    DATA_UPDATE = "data_update"
    ATTENDANCE_UPDATE = "attendance_update"
    GRADE_UPDATE = "grade_update"
    PAYMENT_UPDATE = "payment_update"

    # Presence
    USER_ONLINE = "user_online"
    USER_OFFLINE = "user_offline"
    TYPING = "typing"

    # Chat (future)
    CHAT_MESSAGE = "chat_message"


@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection"""
    websocket: WebSocket
    user_id: str
    school_id: Optional[str] = None
    role: Optional[str] = None
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    subscriptions: Set[str] = field(default_factory=set)


class WebSocketManager:
    """
    Manages WebSocket connections and message broadcasting.

    Features:
    - Connection management per user and school
    - Channel-based subscriptions
    - Redis pub/sub for horizontal scaling
    - Presence tracking
    - Heartbeat monitoring
    """

    def __init__(self):
        # Connection storage
        self.connections: Dict[str, ConnectionInfo] = {}  # connection_id -> ConnectionInfo
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> set of connection_ids
        self.school_connections: Dict[str, Set[str]] = {}  # school_id -> set of connection_ids
        self.channel_subscriptions: Dict[str, Set[str]] = {}  # channel -> set of connection_ids

        # Redis for pub/sub (horizontal scaling)
        self.redis = get_redis_client()
        self.pubsub = None
        self._pubsub_task = None

        # Heartbeat settings
        self.heartbeat_interval = 30  # seconds
        self._heartbeat_task = None

    async def start(self):
        """Start the WebSocket manager background tasks"""
        # Start Redis pub/sub listener
        if self.redis:
            await self._start_pubsub()

        # Start heartbeat task
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info("WebSocket manager started")

    async def stop(self):
        """Stop the WebSocket manager"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()

        if self._pubsub_task:
            self._pubsub_task.cancel()

        if self.pubsub:
            await self.pubsub.unsubscribe()

        # Close all connections
        for conn_id in list(self.connections.keys()):
            await self.disconnect(conn_id)

        logger.info("WebSocket manager stopped")

    async def _start_pubsub(self):
        """Start Redis pub/sub for distributed messaging"""
        try:
            self.pubsub = self.redis.pubsub()
            await self.pubsub.subscribe("edusms:ws:broadcast")
            self._pubsub_task = asyncio.create_task(self._pubsub_listener())
            logger.info("Redis pub/sub started for WebSocket")
        except Exception as e:
            logger.error(f"Failed to start Redis pub/sub: {e}")

    async def _pubsub_listener(self):
        """Listen for messages from Redis pub/sub"""
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await self._handle_pubsub_message(data)
                    except Exception as e:
                        logger.error(f"Error handling pub/sub message: {e}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Pub/sub listener error: {e}")

    async def _handle_pubsub_message(self, data: Dict):
        """Handle a message received from Redis pub/sub"""
        target_type = data.get("target_type")
        target_id = data.get("target_id")
        message = data.get("message")

        if target_type == "user":
            await self._send_to_user(target_id, message)
        elif target_type == "school":
            await self._send_to_school(target_id, message)
        elif target_type == "channel":
            await self._send_to_channel(target_id, message)
        elif target_type == "broadcast":
            await self._broadcast_local(message)

    async def _heartbeat_loop(self):
        """Send periodic heartbeats to detect stale connections"""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                await self._send_heartbeats()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

    async def _send_heartbeats(self):
        """Send heartbeat to all connections"""
        stale_connections = []
        now = datetime.utcnow()

        for conn_id, conn_info in list(self.connections.items()):
            try:
                # Check if connection is stale (no activity in 2x heartbeat interval)
                if (now - conn_info.last_activity).total_seconds() > self.heartbeat_interval * 2:
                    stale_connections.append(conn_id)
                    continue

                # Send ping
                if conn_info.websocket.client_state == WebSocketState.CONNECTED:
                    await conn_info.websocket.send_json({
                        "type": MessageType.PING,
                        "timestamp": now.isoformat()
                    })
            except Exception:
                stale_connections.append(conn_id)

        # Clean up stale connections
        for conn_id in stale_connections:
            await self.disconnect(conn_id)

    def _generate_connection_id(self, user_id: str) -> str:
        """Generate a unique connection ID"""
        import secrets
        return f"{user_id}:{secrets.token_hex(8)}"

    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        school_id: Optional[str] = None,
        role: Optional[str] = None
    ) -> str:
        """
        Register a new WebSocket connection.

        Args:
            websocket: The WebSocket instance
            user_id: User's UUID
            school_id: User's school UUID
            role: User's role

        Returns:
            Connection ID
        """
        await websocket.accept()

        conn_id = self._generate_connection_id(user_id)

        # Store connection info
        self.connections[conn_id] = ConnectionInfo(
            websocket=websocket,
            user_id=user_id,
            school_id=school_id,
            role=role
        )

        # Index by user
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(conn_id)

        # Index by school
        if school_id:
            if school_id not in self.school_connections:
                self.school_connections[school_id] = set()
            self.school_connections[school_id].add(conn_id)

        # Send connected message
        await self._send_to_connection(conn_id, {
            "type": MessageType.CONNECTED,
            "connection_id": conn_id,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Broadcast user online status to school
        if school_id:
            await self.broadcast_to_school(school_id, {
                "type": MessageType.USER_ONLINE,
                "user_id": user_id,
                "role": role
            }, exclude_user=user_id)

        # Update presence in Redis
        if self.redis:
            self.redis.sadd(f"edusms:online:{school_id or 'global'}", user_id)
            self.redis.setex(f"edusms:presence:{user_id}", 3600, json.dumps({
                "online": True,
                "last_seen": datetime.utcnow().isoformat(),
                "school_id": school_id
            }))

        logger.info(f"WebSocket connected: {conn_id} (user: {user_id})")
        return conn_id

    async def disconnect(self, conn_id: str):
        """
        Disconnect and clean up a WebSocket connection.

        Args:
            conn_id: Connection ID to disconnect
        """
        if conn_id not in self.connections:
            return

        conn_info = self.connections[conn_id]
        user_id = conn_info.user_id
        school_id = conn_info.school_id

        # Remove from indices
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(conn_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

                # User is fully offline - update presence
                if self.redis:
                    self.redis.srem(f"edusms:online:{school_id or 'global'}", user_id)
                    self.redis.setex(f"edusms:presence:{user_id}", 3600, json.dumps({
                        "online": False,
                        "last_seen": datetime.utcnow().isoformat(),
                        "school_id": school_id
                    }))

                # Broadcast offline status
                if school_id:
                    await self.broadcast_to_school(school_id, {
                        "type": MessageType.USER_OFFLINE,
                        "user_id": user_id
                    })

        if school_id and school_id in self.school_connections:
            self.school_connections[school_id].discard(conn_id)
            if not self.school_connections[school_id]:
                del self.school_connections[school_id]

        # Remove from channel subscriptions
        for channel in list(conn_info.subscriptions):
            await self.unsubscribe(conn_id, channel)

        # Close WebSocket
        try:
            if conn_info.websocket.client_state == WebSocketState.CONNECTED:
                await conn_info.websocket.close()
        except Exception:
            pass

        # Remove connection
        del self.connections[conn_id]

        logger.info(f"WebSocket disconnected: {conn_id}")

    async def subscribe(self, conn_id: str, channel: str):
        """Subscribe a connection to a channel"""
        if conn_id not in self.connections:
            return

        self.connections[conn_id].subscriptions.add(channel)

        if channel not in self.channel_subscriptions:
            self.channel_subscriptions[channel] = set()
        self.channel_subscriptions[channel].add(conn_id)

        logger.debug(f"Connection {conn_id} subscribed to {channel}")

    async def unsubscribe(self, conn_id: str, channel: str):
        """Unsubscribe a connection from a channel"""
        if conn_id in self.connections:
            self.connections[conn_id].subscriptions.discard(channel)

        if channel in self.channel_subscriptions:
            self.channel_subscriptions[channel].discard(conn_id)
            if not self.channel_subscriptions[channel]:
                del self.channel_subscriptions[channel]

    async def _send_to_connection(self, conn_id: str, message: Dict) -> bool:
        """Send a message to a specific connection"""
        if conn_id not in self.connections:
            return False

        try:
            conn_info = self.connections[conn_id]
            if conn_info.websocket.client_state == WebSocketState.CONNECTED:
                await conn_info.websocket.send_json(message)
                conn_info.last_activity = datetime.utcnow()
                return True
        except Exception as e:
            logger.error(f"Error sending to {conn_id}: {e}")
            await self.disconnect(conn_id)

        return False

    async def _send_to_user(self, user_id: str, message: Dict) -> int:
        """Send a message to all connections of a user"""
        if user_id not in self.user_connections:
            return 0

        sent = 0
        for conn_id in list(self.user_connections[user_id]):
            if await self._send_to_connection(conn_id, message):
                sent += 1

        return sent

    async def _send_to_school(
        self,
        school_id: str,
        message: Dict,
        exclude_user: Optional[str] = None
    ) -> int:
        """Send a message to all connections in a school"""
        if school_id not in self.school_connections:
            return 0

        sent = 0
        for conn_id in list(self.school_connections[school_id]):
            conn_info = self.connections.get(conn_id)
            if conn_info and conn_info.user_id != exclude_user:
                if await self._send_to_connection(conn_id, message):
                    sent += 1

        return sent

    async def _send_to_channel(self, channel: str, message: Dict) -> int:
        """Send a message to all subscribers of a channel"""
        if channel not in self.channel_subscriptions:
            return 0

        sent = 0
        for conn_id in list(self.channel_subscriptions[channel]):
            if await self._send_to_connection(conn_id, message):
                sent += 1

        return sent

    async def _broadcast_local(self, message: Dict) -> int:
        """Broadcast a message to all local connections"""
        sent = 0
        for conn_id in list(self.connections.keys()):
            if await self._send_to_connection(conn_id, message):
                sent += 1
        return sent

    async def send_to_user(self, user_id: str, message: Dict) -> int:
        """
        Send a message to a specific user (all their connections).
        Uses Redis pub/sub for distributed systems.
        """
        # Try local first
        sent = await self._send_to_user(user_id, message)

        # Publish to Redis for other instances
        if self.redis:
            self.redis.publish("edusms:ws:broadcast", json.dumps({
                "target_type": "user",
                "target_id": user_id,
                "message": message
            }))

        return sent

    async def broadcast_to_school(
        self,
        school_id: str,
        message: Dict,
        exclude_user: Optional[str] = None
    ) -> int:
        """Broadcast a message to all users in a school"""
        sent = await self._send_to_school(school_id, message, exclude_user)

        if self.redis:
            self.redis.publish("edusms:ws:broadcast", json.dumps({
                "target_type": "school",
                "target_id": school_id,
                "message": message
            }))

        return sent

    async def broadcast_to_channel(self, channel: str, message: Dict) -> int:
        """Broadcast a message to all subscribers of a channel"""
        sent = await self._send_to_channel(channel, message)

        if self.redis:
            self.redis.publish("edusms:ws:broadcast", json.dumps({
                "target_type": "channel",
                "target_id": channel,
                "message": message
            }))

        return sent

    async def broadcast_all(self, message: Dict) -> int:
        """Broadcast a message to all connected users"""
        sent = await self._broadcast_local(message)

        if self.redis:
            self.redis.publish("edusms:ws:broadcast", json.dumps({
                "target_type": "broadcast",
                "target_id": None,
                "message": message
            }))

        return sent

    async def send_notification(
        self,
        user_id: str,
        title: str,
        body: str,
        notification_type: str = "info",
        data: Optional[Dict] = None
    ) -> int:
        """Send a notification to a user"""
        return await self.send_to_user(user_id, {
            "type": MessageType.NOTIFICATION,
            "title": title,
            "body": body,
            "notification_type": notification_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def send_alert(
        self,
        school_id: str,
        title: str,
        body: str,
        severity: str = "info",
        target_roles: Optional[List[str]] = None
    ) -> int:
        """Send an alert to a school"""
        message = {
            "type": MessageType.ALERT,
            "title": title,
            "body": body,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat()
        }

        if target_roles:
            # Filter by role
            sent = 0
            if school_id in self.school_connections:
                for conn_id in list(self.school_connections[school_id]):
                    conn_info = self.connections.get(conn_id)
                    if conn_info and conn_info.role in target_roles:
                        if await self._send_to_connection(conn_id, message):
                            sent += 1
            return sent

        return await self.broadcast_to_school(school_id, message)

    def get_online_users(self, school_id: Optional[str] = None) -> Set[str]:
        """Get set of online user IDs"""
        if self.redis:
            key = f"edusms:online:{school_id or 'global'}"
            return set(self.redis.smembers(key))

        # Fallback to local data
        if school_id and school_id in self.school_connections:
            return {
                self.connections[conn_id].user_id
                for conn_id in self.school_connections[school_id]
                if conn_id in self.connections
            }

        return set(self.user_connections.keys())

    def get_connection_count(self, school_id: Optional[str] = None) -> int:
        """Get total connection count"""
        if school_id:
            return len(self.school_connections.get(school_id, set()))
        return len(self.connections)

    async def handle_message(self, conn_id: str, message: Dict):
        """Handle an incoming message from a client"""
        if conn_id not in self.connections:
            return

        conn_info = self.connections[conn_id]
        conn_info.last_activity = datetime.utcnow()

        msg_type = message.get("type")

        if msg_type == MessageType.PONG:
            # Heartbeat response - already updated last_activity
            pass

        elif msg_type == "subscribe":
            channel = message.get("channel")
            if channel:
                await self.subscribe(conn_id, channel)

        elif msg_type == "unsubscribe":
            channel = message.get("channel")
            if channel:
                await self.unsubscribe(conn_id, channel)

        else:
            logger.debug(f"Unhandled message type: {msg_type}")


# Global WebSocket manager instance
ws_manager = WebSocketManager()
