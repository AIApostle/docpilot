from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from fastapi import HTTPException, status
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from client.config import settings
from schemas.token import TokenPayload


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Creates and cryptographically signs a JWT access token for a doctor.

    Args:
        data: Claims to embed into the token (must include 'sub' / doctor_id).
        expires_delta: Optional custom token expiration duration.

    Returns:
        Encoded and signed JWT string.
    """
    to_encode = data.copy()
    now_utc = datetime.now(timezone.utc)

    if expires_delta:
        expire = now_utc + expires_delta
    else:
        expire = now_utc + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(now_utc.timestamp()),
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> TokenPayload:
    """Decodes and cryptographically verifies a JWT access token.

    Args:
        token: Raw JWT Bearer token string.

    Returns:
        Validated TokenPayload instance.

    Raises:
        HTTPException: 401 if token is expired, invalid, or malformed.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        sub: Optional[str] = payload.get("sub")
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is missing required subject claim (sub).",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return TokenPayload(
            sub=sub,
            email=payload.get("email"),
            full_name=payload.get("full_name"),
            role=payload.get("role", "doctor"),
            exp=payload.get("exp"),
            iat=payload.get("iat"),
        )

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
