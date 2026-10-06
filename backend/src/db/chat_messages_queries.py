"""Dedicated database operations for the 'docpilot_chat_messages' table in Supabase."""

import datetime
import logging
import uuid
from typing import Any, Dict, List, Optional
from client.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)
TABLE_NAME = "docpilot_chat_messages"


async def create_chat_message(
    session_id: str,
    doctor_id: str,
    role: str,
    content: str,
    attachments: Optional[List[Dict[str, Any]]] = None,
    action_taken: Optional[str] = None,
    entities_extracted: Optional[List[Dict[str, Any]]] = None,
    message_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Inserts a new clinical message into the consultation thread."""
    supabase = await get_supabase_client()
    msg_id = message_id or f"msg_{uuid.uuid4().hex[:12]}"
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    data = {
        "id": msg_id,
        "session_id": session_id,
        "doctor_id": doctor_id,
        "role": role,
        "content": content,
        "attachments": attachments or [],
        "action_taken": action_taken,
        "entities_extracted": entities_extracted or [],
        "created_at": now,
    }

    try:
        res = await supabase.table(TABLE_NAME).insert(data).execute()
        return res.data[0] if (res and res.data) else data
    except Exception as exc:
        logger.error("Failed to insert message into session %s: %s", session_id, exc)
        return None


async def list_messages_by_session_id(
    session_id: str,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """Retrieves chronological messages for a consultation session."""
    supabase = await get_supabase_client()
    try:
        res = (
            await supabase.table(TABLE_NAME)
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=False)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return res.data if (res and res.data) else []
    except Exception as exc:
        logger.error("Failed to list messages for session %s: %s", session_id, exc)
        return []


async def count_messages_by_session_id(session_id: str) -> int:
    """Returns the total number of messages recorded in a session."""
    supabase = await get_supabase_client()
    try:
        res = (
            await supabase.table(TABLE_NAME)
            .select("id", count="exact")
            .eq("session_id", session_id)
            .execute()
        )
        return res.count if (res and res.count is not None) else len(res.data or [])
    except Exception as exc:
        logger.error("Failed to count messages for session %s: %s", session_id, exc)
        return 0
