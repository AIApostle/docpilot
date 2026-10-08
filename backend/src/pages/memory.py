"""Authenticated endpoints for a doctor's MemWal preference."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from auth.dependencies import get_current_doctor
from db.doctor_memory_preferences_queries import (
    DoctorMemoryPreferenceError,
    get_doctor_memory_enabled,
    set_doctor_memory_enabled,
)
from schemas.memory import MemoryPreferenceResponse, MemoryPreferenceUpdate
from schemas.token import TokenPayload

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/preferences",
    response_model=MemoryPreferenceResponse,
    summary="Get the current doctor's MemWal setting",
)
async def get_memory_preference(
    current_doctor: TokenPayload = Depends(get_current_doctor),
) -> MemoryPreferenceResponse:
    try:
        enabled = await get_doctor_memory_enabled(current_doctor.sub)
    except DoctorMemoryPreferenceError as exc:
        logger.error("MemWal preference is unavailable for doctor %s.", current_doctor.sub)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Memory settings are temporarily unavailable. Please retry.",
        ) from exc
    return MemoryPreferenceResponse(enabled=enabled)


@router.put(
    "/preferences",
    response_model=MemoryPreferenceResponse,
    summary="Update the current doctor's MemWal setting",
)
async def update_memory_preference(
    payload: MemoryPreferenceUpdate,
    current_doctor: TokenPayload = Depends(get_current_doctor),
) -> MemoryPreferenceResponse:
    try:
        enabled = await set_doctor_memory_enabled(current_doctor.sub, payload.enabled)
    except DoctorMemoryPreferenceError as exc:
        logger.error("MemWal preference could not be saved for doctor %s: %s", current_doctor.sub, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc) or "Memory settings could not be saved. Please retry.",
        ) from exc
    return MemoryPreferenceResponse(enabled=enabled)
