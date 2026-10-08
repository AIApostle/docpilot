"""Dedicated database operations for per-doctor MemWal preferences."""

import logging
from typing import Any

from client.supabase_client import get_supabase_data_client

logger = logging.getLogger(__name__)
TABLE_NAME = "doctor_memory_preferences"


class DoctorMemoryPreferenceError(RuntimeError):
    """Raised when a doctor's MemWal preference cannot be read or saved."""


async def get_doctor_memory_enabled(doctor_id: str) -> bool:
    """Returns the doctor's MemWal setting; doctors without a row default to on."""
    try:
        supabase = await get_supabase_data_client()
        res = (
            await supabase.table(TABLE_NAME)
            .select("walrus_memory_enabled")
            .eq("doctor_id", doctor_id)
            .maybe_single()
            .execute()
        )
        if not res or not res.data:
            return True
        enabled = res.data.get("walrus_memory_enabled", True)
        if not isinstance(enabled, bool):
            raise DoctorMemoryPreferenceError("Stored MemWal preference is invalid.")
        return enabled
    except DoctorMemoryPreferenceError:
        raise
    except Exception as exc:
        code = getattr(exc, "code", None)
        err_str = str(exc)
        if code == "PGRST205" or "PGRST205" in err_str or "schema cache" in err_str:
            logger.warning(
                "Table '%s' not found in Supabase schema cache (PGRST205); defaulting to enabled (True) for doctor '%s'.",
                TABLE_NAME,
                doctor_id,
            )
            return True
        logger.error("Failed to read MemWal preference for doctor '%s': %s", doctor_id, exc)
        raise DoctorMemoryPreferenceError("Could not read the MemWal preference.") from exc


async def set_doctor_memory_enabled(doctor_id: str, enabled: bool) -> bool:
    """Creates or updates the authenticated doctor's MemWal setting."""
    try:
        supabase = await get_supabase_data_client()
        res = (
            await supabase.table(TABLE_NAME)
            .upsert(
                {"doctor_id": doctor_id, "walrus_memory_enabled": enabled},
                on_conflict="doctor_id",
            )
            .select("walrus_memory_enabled")
            .execute()
        )
        if not res or not res.data:
            raise DoctorMemoryPreferenceError("MemWal preference was not returned after saving.")
        saved_value: Any = res.data[0].get("walrus_memory_enabled")
        if not isinstance(saved_value, bool):
            raise DoctorMemoryPreferenceError("Stored MemWal preference is invalid.")
        return saved_value
    except DoctorMemoryPreferenceError:
        raise
    except Exception as exc:
        code = getattr(exc, "code", None)
        err_str = str(exc)
        if code == "PGRST205" or "PGRST205" in err_str or "schema cache" in err_str:
            logger.error(
                "Table '%s' not found in Supabase schema cache (PGRST205). Migration must be executed in Supabase.",
                TABLE_NAME,
            )
            raise DoctorMemoryPreferenceError(
                f"Could not save the MemWal preference: table '{TABLE_NAME}' does not exist in Supabase yet. Please execute the SQL migration."
            ) from exc
        logger.error("Failed to update MemWal preference for doctor '%s': %s", doctor_id, exc)
        raise DoctorMemoryPreferenceError("Could not save the MemWal preference.") from exc
