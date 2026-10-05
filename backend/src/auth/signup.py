import logging
from typing import Optional
from fastapi import HTTPException, status
from supabase import AsyncClient
from supabase_auth.errors import AuthApiError, AuthError

from src.client.supabase_client import get_supabase_client
from src.schemas.signup import SignupRequest, SignupResponse

logger = logging.getLogger(__name__)


async def signup_doctor(
    request: SignupRequest,
    client: Optional[AsyncClient] = None,
) -> SignupResponse:
    """Registers a new physician using the Supabase Python SDK.

    Args:
        request: Validated physician registration payload.
        client: Optional Supabase AsyncClient instance (defaults to singleton).

    Returns:
        SignupResponse containing doctor identifier and authentication tokens.

    Raises:
        HTTPException: 409 if email already registered, 422 for password policy errors,
                       or 500 for unexpected errors.
    """
    supabase = client or await get_supabase_client()

    try:
        # Register user with Supabase Auth
        auth_response = await supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {
                    "full_name": request.full_name,
                    "role": "doctor",
                }
            },
        })

        if not auth_response.user:
            logger.error("Supabase sign_up completed without returning a user object.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration could not be completed with the identity provider.",
            )

        doctor_id = auth_response.user.id
        email = auth_response.user.email or request.email
        full_name = request.full_name

        # Session token (available immediately if email auto-confirm is enabled in Supabase,
        # otherwise generate an application access token for initial onboarding)
        if auth_response.session:
            access_token = auth_response.session.access_token
            token_type = auth_response.session.token_type or "bearer"
        else:
            from src.auth.jwt import create_access_token
            access_token = create_access_token({
                "sub": doctor_id,
                "email": email,
                "full_name": full_name,
                "role": "doctor",
            })
            token_type = "bearer"

        # Best-effort sync to public.doctors table for relational foreign keys
        try:
            await supabase.table("doctors").upsert({
                "id": doctor_id,
                "email": email,
                "full_name": full_name,
                "hashed_password": "[MANAGED_BY_SUPABASE_AUTH]",
            }).execute()
        except Exception as db_err:
            # If the table does not exist yet or RLS policy restricts direct insert,
            # log warning without breaking registration flow
            logger.warning(
                "Could not sync doctor to public.doctors table: %s", db_err
            )

        return SignupResponse(
            doctor_id=doctor_id,
            email=email,
            full_name=full_name,
            access_token=access_token,
            token_type=token_type,
        )

    except AuthApiError as exc:
        msg = (exc.message or "").lower()
        logger.warning("Supabase AuthApiError during signup: %s (status=%s)", exc.message, exc.status)

        if "already registered" in msg or "already exists" in msg or exc.status == 422 and "registered" in msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A physician account with this email address already exists.",
            )
        if "weak password" in msg or "password" in msg:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Password error: {exc.message}",
            )
        raise HTTPException(
            status_code=exc.status or status.HTTP_400_BAD_REQUEST,
            detail=exc.message or "Registration failed.",
        )

    except AuthError as exc:
        logger.error("Supabase AuthError during signup: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("Unexpected error during physician signup: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected internal error occurred during account creation.",
        )
