import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.auth.jwt import decode_access_token
from src.client.supabase_client import get_supabase_client
from src.schemas.token import TokenPayload

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=True)


async def get_current_doctor(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenPayload:
    """FastAPI security dependency to authenticate and resolve the current physician.

    Supports both:
    1. DocPilot application JWTs signed with SECRET_KEY.
    2. Supabase Auth access tokens verified with the Supabase Auth server.

    Returns:
        Validated TokenPayload representing the authenticated physician.

    Raises:
        HTTPException: 401 if credentials are missing, invalid, or expired.
    """
    token = credentials.credentials.strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization Bearer token is missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 1. First attempt: decode as DocPilot application JWT
    try:
        return decode_access_token(token)
    except HTTPException as app_jwt_err:
        logger.debug(
            "Application JWT decode did not succeed (%s), falling back to Supabase verification...",
            app_jwt_err.detail,
        )

    # 2. Second attempt: verify with Supabase Auth if client is configured
    try:
        supabase = await get_supabase_client()
        user_response = await supabase.auth.get_user(token)

        if user_response and user_response.user:
            user = user_response.user
            user_metadata = user.user_metadata or {}
            return TokenPayload(
                sub=user.id,
                email=user.email,
                full_name=user_metadata.get("full_name"),
                role="doctor",
            )
    except Exception as supabase_err:
        logger.debug("Supabase token verification failed: %s", supabase_err)

    # If both verification mechanisms failed, raise 401
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_doctor_id(
    current_doctor: TokenPayload = Depends(get_current_doctor),
) -> str:
    """Convenience dependency returning the authenticated physician's ID."""
    return current_doctor.sub
