from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TokenPayload(BaseModel):
    """Payload decoded from an authenticated doctor JWT."""
    model_config = ConfigDict(str_strip_whitespace=True)

    sub: str = Field(..., description="Doctor ID (e.g. doc_9f83b2e1 or uuid)")
    email: Optional[str] = Field(None, description="Doctor email address")
    full_name: Optional[str] = Field(None, description="Doctor full name and title")
    role: str = Field(default="doctor", description="User role in the system")
    exp: Optional[int] = Field(None, description="Token expiration timestamp (epoch seconds)")
    iat: Optional[int] = Field(None, description="Token issued-at timestamp (epoch seconds)")


class TokenResponse(BaseModel):
    """Standard OAuth2 / Bearer token response."""
    access_token: str = Field(..., description="Signed JWT Bearer access token")
    token_type: str = Field(default="bearer", description="Token authorization type")
    expires_in: Optional[int] = Field(None, description="Token lifetime in seconds")
