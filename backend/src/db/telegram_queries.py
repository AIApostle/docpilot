"""Dedicated database operations for the 'telegram_connections' table in Supabase."""

import logging
import uuid
from typing import Any, Dict, Optional
from client.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)
TABLE_NAME = "telegram_connections"


async def get_connection_by_telegram_id(telegram_user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves the active Telegram connection mapped to a physician by Telegram user ID."""
    supabase = await get_supabase_client()
    try:
        res = (
            await supabase.table(TABLE_NAME)
            .select("*")
            .eq("telegram_user_id", telegram_user_id)
            .eq("is_active", True)
            .maybe_single()
            .execute()
        )
        return res.data if res else None
    except Exception as exc:
        logger.error("Failed to query telegram connection for TG user %s: %s", telegram_user_id, exc)
        return None


async def get_connection_by_doctor_id(doctor_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves the active Telegram connection for a given doctor."""
    supabase = await get_supabase_client()
    try:
        res = (
            await supabase.table(TABLE_NAME)
            .select("*")
            .eq("doctor_id", doctor_id)
            .eq("is_active", True)
            .maybe_single()
            .execute()
        )
        return res.data if res else None
    except Exception as exc:
        logger.error("Failed to query telegram connection for doctor %s: %s", doctor_id, exc)
        return None


async def upsert_telegram_connection(
    doctor_id: str,
    telegram_user_id: int,
    telegram_username: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Links a doctor to exactly one Telegram user and prevents cross-tenant re-use."""
    supabase = await get_supabase_client()
    record_id = f"tg_{uuid.uuid4().hex[:12]}"
    data = {
        "id": record_id,
        "doctor_id": doctor_id,
        "telegram_user_id": telegram_user_id,
        "telegram_username": telegram_username,
        "is_active": True,
    }
    try:
        doctor_connection = await get_connection_by_doctor_id(doctor_id)
        telegram_connection = await get_connection_by_telegram_id(telegram_user_id)

        if telegram_connection and telegram_connection.get("doctor_id") != doctor_id:
            raise ValueError(
                f"Telegram user {telegram_user_id} is already linked to doctor {telegram_connection.get('doctor_id')}."
            )

        if doctor_connection:
            if doctor_connection.get("telegram_user_id") == telegram_user_id:
                res = (
                    await supabase.table(TABLE_NAME)
                    .update({
                        "telegram_username": telegram_username,
                        "is_active": True,
                    })
                    .eq("doctor_id", doctor_id)
                    .execute()
                )
                return res.data[0] if (res and res.data) else doctor_connection

            res = (
                await supabase.table(TABLE_NAME)
                .update({
                    "telegram_user_id": telegram_user_id,
                    "telegram_username": telegram_username,
                    "is_active": True,
                })
                .eq("doctor_id", doctor_id)
                .execute()
            )
            return res.data[0] if (res and res.data) else None

        res = await supabase.table(TABLE_NAME).insert(data).execute()
        return res.data[0] if (res and res.data) else None
    except ValueError as exc:
        logger.warning("Telegram connection conflict for doctor %s: %s", doctor_id, exc)
        raise
    except Exception as exc:
        logger.error("Failed to upsert telegram connection for doctor %s: %s", doctor_id, exc)
        return None


async def deactivate_telegram_connection(doctor_id: str) -> bool:
    """Deactivates a doctor's Telegram connection."""
    supabase = await get_supabase_client()
    try:
        res = (
            await supabase.table(TABLE_NAME)
            .update({"is_active": False})
            .eq("doctor_id", doctor_id)
            .execute()
        )
        return bool(res and res.data)
    except Exception as exc:
        logger.error("Failed to deactivate telegram connection for doctor %s: %s", doctor_id, exc)
        return False
