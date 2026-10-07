"""Telegram Bot integration endpoints for DocPilot."""

import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, Header, HTTPException, status

from agent.core import docpilot_agent
from auth.dependencies import get_current_doctor
from client.config import settings
from client.telegram import telegram_client
from db.telegram_queries import (
    deactivate_telegram_connection,
    get_connection_by_telegram_id,
    upsert_telegram_connection,
)
from schemas.telegram import TelegramConnectRequest, TelegramConnectResponse
from schemas.token import TokenPayload

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/connect",
    response_model=TelegramConnectResponse,
    status_code=status.HTTP_200_OK,
    summary="Link Telegram account to physician",
    description="Maps a Telegram user ID to the authenticated physician profile for rounds and bedside note capture.",
)
async def connect_telegram(
    request: TelegramConnectRequest,
    current_doctor: TokenPayload = Depends(get_current_doctor),
) -> TelegramConnectResponse:
    try:
        res = await upsert_telegram_connection(
            doctor_id=current_doctor.sub,
            telegram_user_id=request.telegram_user_id,
            telegram_username=request.telegram_username,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if not res:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register Telegram connection.",
        )
    return TelegramConnectResponse(
        status="connected",
        doctor_id=current_doctor.sub,
        telegram_user_id=request.telegram_user_id,
    )


@router.post(
    "/disconnect",
    status_code=status.HTTP_200_OK,
    summary="Unlink Telegram account",
)
async def disconnect_telegram(
    current_doctor: TokenPayload = Depends(get_current_doctor),
) -> Dict[str, Any]:
    await deactivate_telegram_connection(doctor_id=current_doctor.sub)
    return {"status": "disconnected", "doctor_id": current_doctor.sub}


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="Telegram webhook receiver",
    description="Receives real-time updates from the Telegram Bot API and processes bedside clinical notes.",
)
async def telegram_webhook(
    update: Dict[str, Any],
    x_telegram_bot_api_secret_token: str = Header(default=""),
) -> Dict[str, bool]:
    # Secret token verification if configured
    if settings.TELEGRAM_SECRET_TOKEN:
        if x_telegram_bot_api_secret_token != settings.TELEGRAM_SECRET_TOKEN:
            logger.warning("Rejected Telegram webhook with invalid secret token.")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid secret token.")

    message_data = update.get("message") or update.get("edited_message")
    if not message_data:
        return {"ok": True}

    from_user = message_data.get("from") or {}
    telegram_user_id = from_user.get("id")
    chat_id = (message_data.get("chat") or {}).get("id") or telegram_user_id
    text = (message_data.get("text") or "").strip()

    if not telegram_user_id or not text:
        return {"ok": True}

    # Resolve linked physician
    conn = await get_connection_by_telegram_id(telegram_user_id=telegram_user_id)
    if not conn:
        welcome_msg = (
            "👩‍⚕️ *Welcome to DocPilot bedside assistant!*\n\n"
            "Your Telegram account is not yet linked to a physician profile.\n"
            f"Your Telegram User ID is: `{telegram_user_id}`\n\n"
            "Please link this ID in your DocPilot web dashboard or API to begin documenting visits."
        )
        await telegram_client.send_message(chat_id=chat_id, text=welcome_msg)
        return {"ok": True}

    doctor_id = conn["doctor_id"]

    # Handle standard bot commands
    if text.startswith("/start"):
        await telegram_client.send_message(
            chat_id=chat_id,
            text="👋 *DocPilot is active.*\nSend clinical notes, patient updates, or queries. All memories are private to your practice.",
        )
        return {"ok": True}

    # Process clinical note through DocPilot Core
    try:
        reply_text, action, entities, _ = await docpilot_agent.process(
            doctor_id=doctor_id,
            message=text,
        )
        await telegram_client.send_message(chat_id=chat_id, text=reply_text)
    except Exception as exc:
        logger.error("Error processing Telegram note for doctor %s: %s", doctor_id, exc)
        await telegram_client.send_message(
            chat_id=chat_id,
            text="⚠️ An error occurred while processing your clinical note. Please try again shortly.",
        )

    return {"ok": True}
