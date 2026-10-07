"""Dedicated database operations for the 'doctors' table in Supabase."""

import logging
from typing import Any, Dict, Optional
from client.supabase_client import get_supabase_data_client

logger = logging.getLogger(__name__)
TABLE_NAME = "doctors"


async def get_doctor_by_id(doctor_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a doctor record by their unique ID."""
    supabase = await get_supabase_data_client()
    try:
        res = (
            await supabase.table(TABLE_NAME)
            .select("*")
            .eq("id", doctor_id)
            .maybe_single()
            .execute()
        )
        return res.data if res else None
    except Exception as exc:
        logger.error("Failed to query doctor by ID '%s': %s", doctor_id, exc)
        return None


async def get_doctor_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieves a doctor record by their email address."""
    supabase = await get_supabase_data_client()
    try:
        res = (
            await supabase.table(TABLE_NAME)
            .select("*")
            .eq("email", email.strip().lower())
            .maybe_single()
            .execute()
        )
        return res.data if res else None
    except Exception as exc:
        logger.error("Failed to query doctor by email '%s': %s", email, exc)
        return None


async def create_doctor(
    doctor_id: str,
    email: str,
    full_name: Optional[str] = None,
    hashed_password: str = "[MANAGED_BY_SUPABASE_AUTH]",
) -> Optional[Dict[str, Any]]:
    """Inserts a new doctor record into the public.doctors table.
    
    Raises exception on duplicate key/unique constraint violations.
    """
    supabase = await get_supabase_data_client()
    data = {
        "id": doctor_id,
        "email": email.strip().lower(),
        "hashed_password": hashed_password,
    }
    if full_name is not None:
        data["full_name"] = full_name.strip()

    try:
        res = await supabase.table(TABLE_NAME).insert(data).execute()
        return res.data[0] if (res and res.data) else None
    except Exception as exc:
        logger.error("Failed to insert doctor '%s': %s", doctor_id, exc)
        raise exc


async def upsert_doctor(
    doctor_id: str,
    email: str,
    full_name: Optional[str] = None,
    hashed_password: str = "[MANAGED_BY_SUPABASE_AUTH]",
) -> Optional[Dict[str, Any]]:
    """Inserts or updates a doctor record in the public.doctors table."""
    supabase = await get_supabase_data_client()
    data = {
        "id": doctor_id,
        "email": email.strip().lower(),
        "hashed_password": hashed_password,
    }
    if full_name is not None:
        data["full_name"] = full_name.strip()

    try:
        res = await supabase.table(TABLE_NAME).upsert(data).execute()
        return res.data[0] if (res and res.data) else None
    except Exception as exc:
        logger.error("Failed to upsert doctor '%s': %s", doctor_id, exc)
        return None


async def update_doctor_profile(
    doctor_id: str,
    full_name: str,
) -> Optional[Dict[str, Any]]:
    """Updates profile metadata for a physician."""
    supabase = await get_supabase_data_client()
    try:
        res = (
            await supabase.table(TABLE_NAME)
            .update({"full_name": full_name.strip()})
            .eq("id", doctor_id)
            .execute()
        )
        return res.data[0] if (res and res.data) else None
    except Exception as exc:
        logger.error("Failed to update profile for doctor '%s': %s", doctor_id, exc)
        return None
