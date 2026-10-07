"""Dedicated database operations for the 'chat_sessions' table in Supabase."""

import datetime
import logging
import uuid
from typing import Any, Dict, List, Optional
from client.supabase_client import get_supabase_data_client

logger = logging.getLogger(__name__)
TABLE_NAME = "chat_sessions"


async def create_chat_session(
    doctor_id: str,
    title: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Creates a new consultation session for a physician."""
    supabase = await get_supabase_data_client()
    sess_id = session_id or f"sess_{uuid.uuid4().hex[:12]}"
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    session_title = (title or "New consultation").strip()

    data = {
        "id": sess_id,
        "doctor_id": doctor_id,
        "title": session_title,
        "created_at": now,
        "updated_at": now,
        "message_count": 0,
    }

    try:
        res = await supabase.table(TABLE_NAME).insert(data).execute()
        return res.data[0] if (res and res.data) else data
    except Exception as exc:
        logger.error("Failed to create chat session for doctor %s: %s", doctor_id, exc)
        return None


async def get_chat_session(
    session_id: str,
    doctor_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Retrieves a single chat session by ID, optionally verifying physician ownership."""
    supabase = await get_supabase_data_client()
    try:
        query = supabase.table(TABLE_NAME).select("*").eq("id", session_id)
        if doctor_id:
            query = query.eq("doctor_id", doctor_id)
        res = await query.maybe_single().execute()
        return res.data if res else None
    except Exception as exc:
        logger.error("Failed to query chat session %s: %s", session_id, exc)
        return None


async def list_chat_sessions(
    doctor_id: str,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """Lists consultation sessions belonging to a specific doctor in reverse chronological order."""
    supabase = await get_supabase_data_client()
    try:
        res = (
            await supabase.table(TABLE_NAME)
            .select("*")
            .eq("doctor_id", doctor_id)
            .order("updated_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return res.data if (res and res.data) else []
    except Exception as exc:
        logger.error("Failed to list chat sessions for doctor %s: %s", doctor_id, exc)
        return []


async def update_chat_session(
    session_id: str,
    doctor_id: str,
    title: Optional[str] = None,
    message_count: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """Updates session metadata such as title, last updated timestamp, and message count."""
    supabase = await get_supabase_data_client()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    updates: Dict[str, Any] = {"updated_at": now}
    if title is not None:
        updates["title"] = title.strip()
    if message_count is not None:
        updates["message_count"] = message_count

    try:
        res = (
            await supabase.table(TABLE_NAME)
            .update(updates)
            .eq("id", session_id)
            .eq("doctor_id", doctor_id)
            .execute()
        )
        return res.data[0] if (res and res.data) else None
    except Exception as exc:
        logger.error("Failed to update chat session %s: %s", session_id, exc)
        return None


async def delete_chat_session(session_id: str, doctor_id: str) -> bool:
    """Deletes a chat session and its cascaded messages for a physician."""
    supabase = await get_supabase_data_client()
    try:
        res = (
            await supabase.table(TABLE_NAME)
            .delete()
            .eq("id", session_id)
            .eq("doctor_id", doctor_id)
            .execute()
        )
        return bool(res and res.data)
    except Exception as exc:
        logger.error("Failed to delete chat session %s: %s", session_id, exc)
        return False
