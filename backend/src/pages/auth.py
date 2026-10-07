from fastapi import APIRouter, Depends, status

from auth.dependencies import get_current_doctor
from auth.login import login_doctor
from auth.signup import signup_doctor
from client.supabase_client import get_supabase_client
from schemas.login import LoginRequest, LoginResponse
from schemas.signup import SignupRequest, SignupResponse
from schemas.token import TokenPayload

router = APIRouter()


@router.post(
    "/register",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new physician account",
    description="Registers a new physician using Supabase Auth and returns credentials and access tokens.",
)
async def register(request: SignupRequest) -> SignupResponse:
    return await signup_doctor(request)


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def signup_alias(request: SignupRequest) -> SignupResponse:
    """Convenience alias route matching /register."""
    return await signup_doctor(request)


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate physician credentials",
    description="Validates physician email and password, returning an access token and profile.",
)
async def login(request: LoginRequest) -> LoginResponse:
    return await login_doctor(request)


@router.get(
    "/me",
    response_model=TokenPayload,
    status_code=status.HTTP_200_OK,
    summary="Retrieve current physician profile",
    description="Returns verified token claims and profile for the authenticated physician.",
)
async def get_me(
    current_doctor: TokenPayload = Depends(get_current_doctor),
) -> TokenPayload:
    return current_doctor


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Log out current physician session",
    description="Terminates the active session.",
)
async def logout() -> dict:
    try:
        supabase = await get_supabase_client()
        await supabase.auth.sign_out()
    except Exception:
        pass
    return {"status": "ok", "message": "Successfully logged out."}

