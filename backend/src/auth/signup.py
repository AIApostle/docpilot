import logging
from typing import Optional
from fastapi import HTTPException, status
from supabase import AsyncClient
from supabase_auth.errors import AuthApiError, AuthError

from client.supabase_client import get_supabase_client
from db.doctors_queries import create_doctor, get_doctor_by_email
from schemas.signup import SignupRequest, SignupResponse

logger = logging.getLogger(__name__)


async def signup_doctor(
    request: SignupRequest,
    client: Optional[AsyncClient] = None,
) -> SignupResponse:
    """Registers a new physician using the Supabase Python SDK.

    Enforces strict duplicate email prevention across both the application's
    relational 'doctors' table and Supabase Auth identity provider.

    Args:
        request: Validated physician registration payload.
        client: Optional Supabase AsyncClient instance (defaults to singleton).

    Returns:
        SignupResponse containing doctor identifier and authentication tokens.

    Raises:
        HTTPException: 409 if email already registered, 422 for password policy errors,
                       or 500 for unexpected errors.
    """
    normalized_email = request.email.strip().lower()

    # 1. Pre-check: Verify email is not already registered in public.doctors table
    existing_doctor = await get_doctor_by_email(normalized_email)
    if existing_doctor:
        logger.warning(
            "Registration rejected: email '%s' already exists in doctors database.",
            normalized_email,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A physician account with this email address already exists. Please log in instead.",
        )

    supabase = client or await get_supabase_client()

    # 2. Pre-check: Verify email does not exist in Supabase Auth via admin directory
    try:
        if hasattr(supabase.auth, "admin") and hasattr(supabase.auth.admin, "list_users"):
            admin_users = await supabase.auth.admin.list_users()
            if admin_users:
                for u in admin_users:
                    if getattr(u, "email", "").strip().lower() == normalized_email:
                        logger.warning(
                            "Registration rejected: email '%s' already exists in Supabase Auth users.",
                            normalized_email,
                        )
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="A physician account with this email address already exists. Please log in instead.",
                        )
    except HTTPException:
        raise
    except Exception as admin_err:
        logger.debug("Admin list_users pre-check bypassed: %s", admin_err)

    try:
        # 3. Register user with Supabase Auth
        auth_response = await supabase.auth.sign_up({
            "email": normalized_email,
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

        # 4. Check for existing identity in Supabase Auth
        # When an email already exists and email confirmations are active,
        # Supabase Auth returns a dummy user with empty identities list ([]).
        identities = getattr(auth_response.user, "identities", None)
        if identities is not None and len(identities) == 0:
            logger.warning(
                "Registration rejected: Supabase Auth returned empty identities for '%s' (account already exists).",
                normalized_email,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A physician account with this email address already exists. Please log in instead.",
            )

        doctor_id = auth_response.user.id
        email = auth_response.user.email or normalized_email
        full_name = request.full_name

        # Session token (available immediately if email auto-confirm is enabled in Supabase,
        # otherwise generate an application access token for initial onboarding)
        if auth_response.session:
            access_token = auth_response.session.access_token
            token_type = auth_response.session.token_type or "bearer"
        else:
            from .jwt import create_access_token
            access_token = create_access_token({
                "sub": doctor_id,
                "email": email,
                "full_name": full_name,
                "role": "doctor",
            })
            token_type = "bearer"

        # 5. Persist to public.doctors table enforcing unique email constraint
        try:
            await create_doctor(
                doctor_id=doctor_id,
                email=email,
                full_name=full_name,
                hashed_password="[MANAGED_BY_SUPABASE_AUTH]",
            )
        except Exception as db_err:
            err_str = str(db_err).lower()
            if "unique" in err_str or "duplicate" in err_str or "already exists" in err_str:
                logger.warning(
                    "Registration rejected: database uniqueness constraint failed for email '%s': %s",
                    email,
                    db_err,
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A physician account with this email address already exists. Please log in instead.",
                )
            logger.warning("Could not sync doctor to public.doctors table: %s", db_err)

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

        if (
            "already registered" in msg
            or "already exists" in msg
            or "user already exists" in msg
            or "email address has already been registered" in msg
            or "duplicate" in msg
            or (exc.status in (400, 409, 422) and ("registered" in msg or "exists" in msg or "user" in msg))
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A physician account with this email address already exists. Please log in instead.",
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
