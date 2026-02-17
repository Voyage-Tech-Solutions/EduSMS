"""
EduCore Backend - Messaging API
Internal messaging system for school communication
"""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# MODELS
# ============================================================

class MessageCreate(BaseModel):
    """Create a new message"""
    recipient_ids: List[UUID]
    subject: str
    body: str
    priority: str = "normal"  # low, normal, high, urgent
    reply_to_id: Optional[UUID] = None
    attachments: List[str] = []


class MessageReply(BaseModel):
    """Reply to a message"""
    body: str
    attachments: List[str] = []


class ConversationCreate(BaseModel):
    """Create a conversation thread"""
    participant_ids: List[UUID]
    title: Optional[str] = None
    initial_message: str


# ============================================================
# INBOX
# ============================================================

@router.get("/inbox")
async def get_inbox(
    folder: str = "inbox",  # inbox, sent, drafts, archive, trash
    is_read: Optional[bool] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get messages in inbox or other folders"""
    user_id = current_user.get("id")

    if folder == "sent":
        query = supabase.table("messages").select(
            "*, recipients:message_recipients(user:recipient_id(first_name, last_name, role))"
        ).eq("sender_id", user_id).eq("is_draft", False)
    else:
        query = supabase.table("message_recipients").select(
            "*, message:message_id(*, sender:sender_id(first_name, last_name, role))"
        ).eq("recipient_id", user_id)

        if folder == "inbox":
            query = query.eq("folder", "inbox")
        elif folder == "archive":
            query = query.eq("folder", "archive")
        elif folder == "trash":
            query = query.eq("folder", "trash")

        if is_read is not None:
            query = query.eq("is_read", is_read)

    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

    result = query.execute()

    # Get unread count
    unread = supabase.table("message_recipients").select(
        "id", count="exact"
    ).eq("recipient_id", user_id).eq("is_read", False).eq("folder", "inbox").execute()

    return {
        "messages": result.data or [],
        "unread_count": unread.count or 0,
        "folder": folder,
        "limit": limit,
        "offset": offset
    }


@router.get("/unread-count")
async def get_unread_count(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get unread message count"""
    user_id = current_user.get("id")

    result = supabase.table("message_recipients").select(
        "id", count="exact"
    ).eq("recipient_id", user_id).eq("is_read", False).eq("folder", "inbox").execute()

    return {"unread_count": result.count or 0}


# ============================================================
# MESSAGE OPERATIONS
# ============================================================

@router.get("/{message_id}")
async def get_message(
    message_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get message details"""
    user_id = current_user.get("id")

    # Check if user is sender or recipient
    message = supabase.table("messages").select(
        "*, sender:sender_id(first_name, last_name, email, role), recipients:message_recipients(user:recipient_id(first_name, last_name, email, role), is_read, read_at)"
    ).eq("id", str(message_id)).single().execute()

    if not message.data:
        raise HTTPException(status_code=404, detail="Message not found")

    # Mark as read if recipient
    recipient = supabase.table("message_recipients").select("id, is_read").eq(
        "message_id", str(message_id)
    ).eq("recipient_id", user_id).single().execute()

    if recipient.data and not recipient.data.get("is_read"):
        supabase.table("message_recipients").update({
            "is_read": True,
            "read_at": datetime.utcnow().isoformat()
        }).eq("id", recipient.data["id"]).execute()

    # Get thread if reply
    thread = []
    if message.data.get("reply_to_id"):
        thread_result = supabase.table("messages").select(
            "id, subject, body, created_at, sender:sender_id(first_name, last_name)"
        ).eq("thread_id", message.data.get("thread_id")).order("created_at").execute()
        thread = thread_result.data or []

    return {
        **message.data,
        "thread": thread
    }


@router.post("")
async def send_message(
    message: MessageCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Send a new message"""
    user_id = current_user.get("id")
    school_id = current_user.get("school_id")

    # Create thread if new message
    thread_id = None
    if message.reply_to_id:
        original = supabase.table("messages").select("thread_id").eq(
            "id", str(message.reply_to_id)
        ).single().execute()
        if original.data:
            thread_id = original.data.get("thread_id")

    if not thread_id:
        # Create new thread
        thread = supabase.table("message_threads").insert({
            "school_id": school_id
        }).execute()
        thread_id = thread.data[0]["id"] if thread.data else None

    # Create message
    message_data = {
        "school_id": school_id,
        "sender_id": user_id,
        "subject": message.subject,
        "body": message.body,
        "priority": message.priority,
        "reply_to_id": str(message.reply_to_id) if message.reply_to_id else None,
        "thread_id": thread_id,
        "attachments": message.attachments,
        "is_draft": False
    }

    result = supabase.table("messages").insert(message_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to send message")

    msg_id = result.data[0]["id"]

    # Create recipient records
    recipients_data = [
        {
            "message_id": msg_id,
            "recipient_id": str(rid),
            "is_read": False,
            "folder": "inbox"
        }
        for rid in message.recipient_ids
    ]

    supabase.table("message_recipients").insert(recipients_data).execute()

    return {
        "id": msg_id,
        "status": "sent",
        "recipients": len(message.recipient_ids)
    }


@router.post("/{message_id}/reply")
async def reply_to_message(
    message_id: UUID,
    reply: MessageReply,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Reply to a message"""
    user_id = current_user.get("id")
    school_id = current_user.get("school_id")

    # Get original message
    original = supabase.table("messages").select(
        "sender_id, subject, thread_id"
    ).eq("id", str(message_id)).single().execute()

    if not original.data:
        raise HTTPException(status_code=404, detail="Original message not found")

    # Create reply
    reply_data = {
        "school_id": school_id,
        "sender_id": user_id,
        "subject": f"Re: {original.data['subject']}",
        "body": reply.body,
        "reply_to_id": str(message_id),
        "thread_id": original.data.get("thread_id"),
        "attachments": reply.attachments,
        "is_draft": False
    }

    result = supabase.table("messages").insert(reply_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to send reply")

    # Add original sender as recipient
    supabase.table("message_recipients").insert({
        "message_id": result.data[0]["id"],
        "recipient_id": original.data["sender_id"],
        "is_read": False,
        "folder": "inbox"
    }).execute()

    return {"id": result.data[0]["id"], "status": "sent"}


@router.post("/{message_id}/archive")
async def archive_message(
    message_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Move message to archive"""
    user_id = current_user.get("id")

    supabase.table("message_recipients").update({
        "folder": "archive"
    }).eq("message_id", str(message_id)).eq("recipient_id", user_id).execute()

    return {"success": True}


@router.post("/{message_id}/trash")
async def trash_message(
    message_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Move message to trash"""
    user_id = current_user.get("id")

    supabase.table("message_recipients").update({
        "folder": "trash"
    }).eq("message_id", str(message_id)).eq("recipient_id", user_id).execute()

    return {"success": True}


@router.delete("/{message_id}")
async def delete_message(
    message_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Permanently delete message"""
    user_id = current_user.get("id")

    # Only delete recipient record (message stays for other recipients)
    supabase.table("message_recipients").delete().eq(
        "message_id", str(message_id)
    ).eq("recipient_id", user_id).execute()

    return {"success": True}


# ============================================================
# BULK OPERATIONS
# ============================================================

@router.post("/bulk/mark-read")
async def bulk_mark_read(
    message_ids: List[UUID],
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Mark multiple messages as read"""
    user_id = current_user.get("id")

    supabase.table("message_recipients").update({
        "is_read": True,
        "read_at": datetime.utcnow().isoformat()
    }).in_("message_id", [str(mid) for mid in message_ids]).eq("recipient_id", user_id).execute()

    return {"success": True, "count": len(message_ids)}


@router.post("/bulk/archive")
async def bulk_archive(
    message_ids: List[UUID],
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Archive multiple messages"""
    user_id = current_user.get("id")

    supabase.table("message_recipients").update({
        "folder": "archive"
    }).in_("message_id", [str(mid) for mid in message_ids]).eq("recipient_id", user_id).execute()

    return {"success": True, "count": len(message_ids)}


@router.post("/bulk/delete")
async def bulk_delete(
    message_ids: List[UUID],
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete multiple messages"""
    user_id = current_user.get("id")

    supabase.table("message_recipients").delete().in_(
        "message_id", [str(mid) for mid in message_ids]
    ).eq("recipient_id", user_id).execute()

    return {"success": True, "count": len(message_ids)}


# ============================================================
# CONTACTS
# ============================================================

@router.get("/contacts")
async def get_contacts(
    role: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get available contacts for messaging"""
    school_id = current_user.get("school_id")
    user_id = current_user.get("id")

    contacts = []

    # Get teachers
    if not role or role == "teacher":
        teachers = supabase.table("teachers").select(
            "id, first_name, last_name, email, position"
        ).eq("school_id", school_id).eq("is_active", True).execute()

        for t in (teachers.data or []):
            contacts.append({
                "id": t["id"],
                "name": f"{t['first_name']} {t['last_name']}",
                "email": t.get("email"),
                "role": "teacher",
                "position": t.get("position")
            })

    # Get staff (from user profiles with staff role)
    if not role or role == "staff":
        staff = supabase.table("user_profiles").select(
            "id, first_name, last_name, email"
        ).eq("school_id", school_id).eq("role", "office_admin").execute()

        for s in (staff.data or []):
            contacts.append({
                "id": s["id"],
                "name": f"{s['first_name']} {s['last_name']}",
                "email": s.get("email"),
                "role": "staff"
            })

    # Get parents (if user is teacher/admin)
    user_role = current_user.get("role")
    if (not role or role == "parent") and user_role in ["teacher", "office_admin", "principal"]:
        parents = supabase.table("user_profiles").select(
            "id, first_name, last_name, email"
        ).eq("school_id", school_id).eq("role", "parent").execute()

        for p in (parents.data or []):
            contacts.append({
                "id": p["id"],
                "name": f"{p['first_name']} {p['last_name']}",
                "email": p.get("email"),
                "role": "parent"
            })

    # Filter by search
    if search:
        search_lower = search.lower()
        contacts = [c for c in contacts if search_lower in c["name"].lower()]

    # Remove current user
    contacts = [c for c in contacts if c["id"] != user_id]

    return {"contacts": contacts}


# ============================================================
# CONVERSATIONS
# ============================================================

@router.get("/conversations")
async def get_conversations(
    limit: int = Query(default=20, le=50),
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get conversation threads"""
    user_id = current_user.get("id")

    # Get threads where user is participant
    threads = supabase.table("conversation_participants").select(
        "conversation:conversation_id(id, title, created_at, last_message_at, last_message)"
    ).eq("user_id", user_id).order("conversation(last_message_at)", desc=True).limit(limit).execute()

    conversations = []
    for t in (threads.data or []):
        if t.get("conversation"):
            conv = t["conversation"]
            # Get other participants
            participants = supabase.table("conversation_participants").select(
                "user:user_id(first_name, last_name)"
            ).eq("conversation_id", conv["id"]).neq("user_id", user_id).execute()

            conversations.append({
                **conv,
                "participants": [p["user"] for p in (participants.data or []) if p.get("user")]
            })

    return {"conversations": conversations}


@router.post("/conversations")
async def create_conversation(
    conversation: ConversationCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a new conversation"""
    user_id = current_user.get("id")
    school_id = current_user.get("school_id")

    # Create conversation
    conv_data = {
        "school_id": school_id,
        "title": conversation.title,
        "created_by": user_id,
        "last_message": conversation.initial_message[:100],
        "last_message_at": datetime.utcnow().isoformat()
    }

    result = supabase.table("conversations").insert(conv_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create conversation")

    conv_id = result.data[0]["id"]

    # Add participants (including sender)
    all_participants = set([user_id] + [str(p) for p in conversation.participant_ids])
    participants_data = [
        {"conversation_id": conv_id, "user_id": pid}
        for pid in all_participants
    ]
    supabase.table("conversation_participants").insert(participants_data).execute()

    # Add initial message
    supabase.table("conversation_messages").insert({
        "conversation_id": conv_id,
        "sender_id": user_id,
        "body": conversation.initial_message
    }).execute()

    return {"conversation_id": conv_id}


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: UUID,
    limit: int = Query(default=50, le=100),
    before_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get messages in a conversation"""
    user_id = current_user.get("id")

    # Verify user is participant
    participant = supabase.table("conversation_participants").select("id").eq(
        "conversation_id", str(conversation_id)
    ).eq("user_id", user_id).single().execute()

    if not participant.data:
        raise HTTPException(status_code=403, detail="Not a participant in this conversation")

    query = supabase.table("conversation_messages").select(
        "*, sender:sender_id(first_name, last_name)"
    ).eq("conversation_id", str(conversation_id))

    if before_id:
        query = query.lt("id", str(before_id))

    query = query.order("created_at", desc=True).limit(limit)

    result = query.execute()

    return {"messages": list(reversed(result.data or []))}


@router.post("/conversations/{conversation_id}/messages")
async def send_conversation_message(
    conversation_id: UUID,
    body: str,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Send message in a conversation"""
    user_id = current_user.get("id")

    # Verify user is participant
    participant = supabase.table("conversation_participants").select("id").eq(
        "conversation_id", str(conversation_id)
    ).eq("user_id", user_id).single().execute()

    if not participant.data:
        raise HTTPException(status_code=403, detail="Not a participant")

    # Add message
    result = supabase.table("conversation_messages").insert({
        "conversation_id": str(conversation_id),
        "sender_id": user_id,
        "body": body
    }).execute()

    # Update conversation
    supabase.table("conversations").update({
        "last_message": body[:100],
        "last_message_at": datetime.utcnow().isoformat()
    }).eq("id", str(conversation_id)).execute()

    return result.data[0] if result.data else None
