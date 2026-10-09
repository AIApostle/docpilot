"""Clinical consultation and chat endpoints for DocPilot."""

import datetime
import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status

from agent.core import docpilot_agent
from auth.dependencies import authenticate_token_string, get_current_doctor
from client.walrus import WalrusUnavailableError
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
from db.doctor_memory_preferences_queries import DoctorMemoryPreferenceError, get_doctor_memory_enabled
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
        if "indexed" in attachment and isinstance(attachment["indexed"], bool):
            metadata["indexed"] = attachment["indexed"]
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
    raw_messages = await list_messages_by_session_id(
        session_id=session_id,
        doctor_id=current_doctor.sub,
    )
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
    raw_messages = await list_messages_by_session_id(
        session_id=session_id,
        doctor_id=current_doctor.sub,
    )
    return [_format_message_dict(m) for m in raw_messages]


async def process_chat_turn(
    doctor_id: str,
    message: str,
    session_id: Optional[str] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
    on_status: Optional[Callable[[str, str], Awaitable[None]]] = None,
) -> Dict[str, Any]:
    """Processes a single consultation message turn for doctor, shared by HTTP and WebSocket."""
    try:
        memory_enabled = await get_doctor_memory_enabled(doctor_id)
    except DoctorMemoryPreferenceError as exc:
        logger.error("Could not load MemWal preference for doctor %s.", doctor_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Memory settings are temporarily unavailable. Please retry.",
        ) from exc

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # 1. Resolve or create consultation session
    session = None
    if session_id:
        session = await get_chat_session(session_id=session_id, doctor_id=doctor_id)

    is_new_session = False
    if not session:
        is_new_session = True
        # Generate initial title from first 60 chars of doctor message
        fallback_title = message.strip().replace("\n", " ")[:60]
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

    raw_attachments = [dict(a) for a in (attachments or [])]

    # Process through agent without injecting Supabase doctor profile into prompt
    try:
        response_text, action_taken, entities, suggested_title = await docpilot_agent.process(
            doctor_id=doctor_id,
            message=message,
            memory_enabled=memory_enabled,
            attachments=raw_attachments,
            on_status=on_status,
        )
    except WalrusUnavailableError as exc:
        logger.error("Persistent Walrus memory unavailable for doctor %s.", doctor_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Persistent clinical memory is unavailable. Your message was not processed; please retry later.",
        ) from exc
    except Exception as exc:
        logger.error("DocPilot Agent processing error: %s", exc)
        response_text = "I couldn't complete that request. Please try again."
        action_taken = "conversational"
        entities = []
        suggested_title = None

    # Enrich attachments with indexing metadata for clinical audit
    persisted_attachments = []
    for att in raw_attachments:
        att_item = dict(att)
        if memory_enabled:
            att_item["indexed"] = True
        persisted_attachments.append(att_item)

    # Persist the turn only after memory and reasoning processing completed.
    await create_chat_message(
        session_id=session_id,
        doctor_id=doctor_id,
        role="user",
        content=message.strip(),
        attachments=persisted_attachments,
    )

    entities_dump = [e.model_dump() for e in entities]
    await create_chat_message(
        session_id=session_id,
        doctor_id=doctor_id,
        role="assistant",
        content=response_text,
        action_taken=action_taken,
        entities_extracted=entities_dump,
    )

    # Update session title and message count
    updated_title = suggested_title or session.get("title")
    curr_count = int(session.get("message_count") or 0) + 2
    await update_chat_session(
        session_id=session_id,
        doctor_id=doctor_id,
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
        "memory_enabled": memory_enabled,
    }


@router.post(
    "",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Send clinical note or query",
    description="Processes a clinical note or question using the authenticated doctor's MemWal setting.",
)
async def send_message(
    payload: ChatRequest,
    current_doctor: TokenPayload = Depends(get_current_doctor),
) -> Dict[str, Any]:
    raw_attachments = [a.model_dump() for a in payload.attachments] if payload.attachments else []
    return await process_chat_turn(
        doctor_id=current_doctor.sub,
        message=payload.message,
        session_id=payload.resolved_session_id(),
        attachments=raw_attachments,
    )


@router.websocket("/ws")
async def chat_websocket(websocket: WebSocket):
    """WebSocket endpoint powering bidirectional, real-time chat between physician and DocPilot."""
    token = websocket.query_params.get("token")
    doctor: Optional[TokenPayload] = None
    if token:
        doctor = await authenticate_token_string(token)

    if not doctor:
        await websocket.accept()
        try:
            init_msg = await websocket.receive_json()
            if init_msg.get("type") == "auth" and init_msg.get("token"):
                doctor = await authenticate_token_string(str(init_msg["token"]))
        except Exception:
            pass

        if not doctor:
            await websocket.send_json({
                "type": "error",
                "detail": "Authentication failed. Valid Bearer token required.",
            })
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    else:
        await websocket.accept()

    await websocket.send_json({
        "type": "connected",
        "doctor_id": doctor.sub,
    })

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type") or "message"
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue
            if msg_type != "message":
                continue

            message_text = str(data.get("message") or "").strip()
            raw_attachments = data.get("attachments") or []
            session_id = data.get("conversation_id") or data.get("session_id")
            if not message_text and not raw_attachments:
                await websocket.send_json({
                    "type": "error",
                    "detail": "Message or attachments required.",
                })
                continue

            async def send_status(stage: str, status_msg: str):
                try:
                    await websocket.send_json({
                        "type": "status",
                        "status": stage,
                        "stage": stage,
                        "message": status_msg,
                    })
                except Exception as ws_err:
                    logger.debug("Failed to send WebSocket status update: %s", ws_err)

            try:
                result = await process_chat_turn(
                    doctor_id=doctor.sub,
                    message=message_text,
                    session_id=session_id,
                    attachments=raw_attachments,
                    on_status=send_status,
                )
                await websocket.send_json({
                    "type": "response",
                    **result,
                })
            except HTTPException as http_exc:
                await websocket.send_json({
                    "type": "error",
                    "detail": http_exc.detail,
                    "status_code": http_exc.status_code,
                })
            except Exception as turn_exc:
                logger.error("Error processing WebSocket message for %s: %s", doctor.sub, turn_exc)
                await websocket.send_json({
                    "type": "error",
                    "detail": "Could not process consultation message. Please try again.",
                })
    except WebSocketDisconnect:
        logger.info("Doctor %s disconnected from consultation websocket.", doctor.sub)
    except Exception as exc:
        logger.debug("WebSocket connection terminated: %s", exc)


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
