import logging
from typing import Optional
from fastapi import HTTPException, status
from supabase import AsyncClient
from supabase_auth.errors import AuthApiError, AuthError

from client.supabase_client import get_supabase_client
from schemas.login import DoctorSummary, LoginRequest, LoginResponse

logger = logging.getLogger(__name__)


async def login_doctor(
    request: LoginRequest,
    client: Optional[AsyncClient] = None,
) -> LoginResponse:
    """Authenticates a physician using the Supabase Python SDK.

    Args:
        request: Validated physician login credentials.
        client: Optional Supabase AsyncClient instance (defaults to singleton).

    Returns:
        LoginResponse with JWT access token and physician profile.

    Raises:
        HTTPException: 401 for invalid credentials, 403 for unconfirmed email,
                       or 500 for unexpected errors.
    """
    supabase = client or await get_supabase_client()

    try:
        # Authenticate via Supabase Auth
        auth_response = await supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password,
        })

        if not auth_response.session or not auth_response.user:
            logger.warning("Supabase sign_in succeeded without valid session or user object.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = auth_response.user
        session = auth_response.session

        doctor_id = user.id
        email = user.email or request.email
        user_metadata = user.user_metadata or {}
        full_name = user_metadata.get("full_name")

        # If full_name is not in metadata, attempt fallback from public.doctors table
        if not full_name:
            try:
                db_res = (
                    await supabase.table("doctors")
                    .select("full_name")
                    .eq("id", doctor_id)
                    .maybe_single()
                    .execute()
                )
                if db_res and db_res.data:
                    full_name = db_res.data.get("full_name")
            except Exception:
                pass

        doctor_summary = DoctorSummary(
            id=doctor_id,
            email=email,
            full_name=full_name,
        )

        return LoginResponse(
            access_token=session.access_token,
            token_type=session.token_type or "bearer",
            doctor=doctor_summary,
        )

    except AuthApiError as exc:
        msg = (exc.message or "").lower()
        logger.warning(
            "Supabase AuthApiError during login for %s: %s (status=%s)",
            request.email,
            exc.message,
            exc.status,
        )

        if "invalid login credentials" in msg or "invalid grant" in msg or exc.status in (400, 401):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if "email not confirmed" in msg or "confirm" in msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email address has not been confirmed yet. Please verify your email.",
            )
        raise HTTPException(
            status_code=exc.status or status.HTTP_400_BAD_REQUEST,
            detail=exc.message or "Authentication failed.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except AuthError as exc:
        logger.error("Supabase AuthError during login: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("Unexpected error during physician login: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected internal error occurred during authentication.",
        )
