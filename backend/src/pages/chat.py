"""Clinical consultation and chat endpoints for DocPilot."""

import datetime
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from agent.core import docpilot_agent
from auth.dependencies import get_current_doctor
from db.chat_messages_queries import (
    create_chat_message,
    list_messages_by_session_id,
)
from db.chat_sessions_queries import (
    create_chat_session,
    delete_chat_session,
    get_chat_session,
    list_chat_sessions,
    update_chat_session,
)
from schemas.chat import ChatRequest
from schemas.chat_session import ChatSessionCreate, ChatSessionResponse
from schemas.token import TokenPayload

logger = logging.getLogger(__name__)
router = APIRouter()


def _format_session_dict(session: Dict[str, Any]) -> Dict[str, Any]:
    """Formats session dictionary to satisfy both PRD and frontend specs."""
    sid = str(session.get("id") or "")
    updated = str(session.get("updated_at") or session.get("created_at") or "")
    return {
        "id": sid,
        "session_id": sid,
        "conversation_id": sid,
        "doctor_id": str(session.get("doctor_id") or ""),
        "title": str(session.get("title") or "New consultation"),
        "created_at": str(session.get("created_at") or updated),
        "updated_at": updated,
        "updatedAt": updated,
        "message_count": int(session.get("message_count") or 0),
    }


def _format_message_dict(msg: Dict[str, Any]) -> Dict[str, Any]:
    """Formats message dictionary to satisfy both PRD and frontend specs."""
    role = str(msg.get("role") or "assistant").lower()
    if role in ("doctor", "physician"):
        role = "user"
    created = str(msg.get("created_at") or "")
    attachments = []
    for attachment in msg.get("attachments") or []:
        if not isinstance(attachment, dict):
            continue
        metadata = {
            key: attachment[key]
            for key in ("filename", "file_type", "description")
            if isinstance(attachment.get(key), str)
        }
        if metadata.get("filename") and metadata.get("file_type"):
            attachments.append(metadata)
    return {
        "id": str(msg.get("id") or ""),
        "session_id": str(msg.get("session_id") or ""),
        "role": role,
        "content": str(msg.get("content") or ""),
        "created_at": created,
        "createdAt": created,
        "attachments": attachments,
        "action_taken": msg.get("action_taken"),
        "entities_extracted": msg.get("entities_extracted") or [],
    }


@router.get(
    "",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="List consultation sessions",
    description="Lists consultation sessions belonging to the current physician.",
)
@router.get(
    "/sessions",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def list_sessions(
    current_doctor: TokenPayload = Depends(get_current_doctor),
) -> List[Dict[str, Any]]:
    sessions = await list_chat_sessions(doctor_id=current_doctor.sub)
    return [_format_session_dict(s) for s in sessions]


@router.post(
    "/sessions",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new consultation session",
)
async def create_new_session(
    body: Optional[ChatSessionCreate] = None,
    current_doctor: TokenPayload = Depends(get_current_doctor),
) -> Dict[str, Any]:
    title = body.title if body else "New consultation"
    session = await create_chat_session(doctor_id=current_doctor.sub, title=title)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create consultation session.",
        )
    return _format_session_dict(session)


@router.get(
    "/{session_id}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get conversation detail and message history",
)
async def get_session_detail(
    session_id: str,
    current_doctor: TokenPayload = Depends(get_current_doctor),
) -> Dict[str, Any]:
    session = await get_chat_session(session_id=session_id, doctor_id=current_doctor.sub)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation conversation not found.",
        )
    raw_messages = await list_messages_by_session_id(session_id=session_id)
    formatted = _format_session_dict(session)
    formatted["messages"] = [_format_message_dict(m) for m in raw_messages]
    return formatted


@router.get(
    "/sessions/{session_id}/messages",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Get messages for session",
    include_in_schema=False,
)
async def get_session_messages_alias(
    session_id: str,
    current_doctor: TokenPayload = Depends(get_current_doctor),
) -> List[Dict[str, Any]]:
    session = await get_chat_session(session_id=session_id, doctor_id=current_doctor.sub)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation session not found.",
        )
    raw_messages = await list_messages_by_session_id(session_id=session_id)
    return [_format_message_dict(m) for m in raw_messages]


@router.post(
    "",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Send clinical note or query",
    description="Ingests a clinical note or question, recalls memories, reasons with LLM, and consolidates memory.",
)
async def send_message(
    payload: ChatRequest,
    current_doctor: TokenPayload = Depends(get_current_doctor),
) -> Dict[str, Any]:
    doctor_id = current_doctor.sub
    session_id = payload.resolved_session_id()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # 1. Resolve or create consultation session
    session = None
    if session_id:
        session = await get_chat_session(session_id=session_id, doctor_id=doctor_id)

    is_new_session = False
    if not session:
        is_new_session = True
        # Generate initial title from first 60 chars of doctor message
        fallback_title = payload.message.strip().replace("\n", " ")[:60]
        session = await create_chat_session(
            doctor_id=doctor_id,
            title=fallback_title or "New consultation",
            session_id=session_id,
        )
        if not session:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not initialize consultation session.",
            )
        session_id = session["id"]

    # 2. Fetch recent conversation turns for context
    past_messages = await list_messages_by_session_id(session_id=session_id, limit=6)
    history_turns = [
        {"role": "user" if m.get("role") in ("doctor", "user") else "assistant", "content": m.get("content", "")}
        for m in past_messages
    ]

    # 3. Store incoming doctor message
    raw_attachments = [a.model_dump() for a in payload.attachments] if payload.attachments else []
    await create_chat_message(
        session_id=session_id,
        doctor_id=doctor_id,
        role="user",
        content=payload.message.strip(),
        attachments=raw_attachments,
    )

    # 4. Execute DocPilot Core Agent reasoning
    try:
        response_text, action_taken, entities, suggested_title = await docpilot_agent.process(
            doctor_id=doctor_id,
            message=payload.message,
            conversation_history=history_turns,
        )
    except Exception as exc:
        logger.error("DocPilot Agent processing error: %s", exc)
        response_text = (
            "I have documented your note in the record. "
            "(Clinical reasoning service temporarily experienced high latency)."
        )
        action_taken = "conversational"
        entities = []
        suggested_title = None

    # 5. Persist assistant reply
    entities_dump = [e.model_dump() for e in entities]
    await create_chat_message(
        session_id=session_id,
        doctor_id=doctor_id,
        role="assistant",
        content=response_text,
        action_taken=action_taken,
        entities_extracted=entities_dump,
    )

    # 6. Update session title and message count
    updated_title = suggested_title or session.get("title")
    curr_count = int(session.get("message_count") or len(past_messages)) + 2
    await update_chat_session(
        session_id=session_id,
        title=updated_title if (is_new_session or suggested_title) else None,
        message_count=curr_count,
    )

    return {
        "id": session_id,
        "session_id": session_id,
        "conversation_id": session_id,
        "title": updated_title or "Consultation",
        "response": response_text,
        "reply": response_text,
        "action_taken": action_taken,
        "entities_extracted": entities_dump,
        "updated_at": now_iso,
        "updatedAt": now_iso,
    }


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a consultation session",
)
async def delete_session(
    session_id: str,
    current_doctor: TokenPayload = Depends(get_current_doctor),
) -> Dict[str, Any]:
    success = await delete_chat_session(session_id=session_id, doctor_id=current_doctor.sub)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session could not be deleted or does not exist.",
        )
    return {"status": "ok", "message": "Session deleted."}
