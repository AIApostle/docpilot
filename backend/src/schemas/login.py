from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class DoctorSummary(BaseModel):
    """Basic doctor profile information returned upon authentication."""
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    id: str = Field(..., description="Unique physician identifier (e.g. doc_9f83b2e1)")
    email: EmailStr = Field(..., description="Physician's verified email address")
    full_name: Optional[str] = Field(None, description="Physician's full name and clinical title")


class LoginRequest(BaseModel):
    """Doctor login payload with strict input validation."""
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr = Field(
        ...,
        description="Physician account email address",
        examples=["dr.smith@hospital.org"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Account password",
        examples=["SecurePassword123!"],
    )


class LoginResponse(BaseModel):
    """Response payload returned upon successful doctor authentication."""
    access_token: str = Field(..., description="Signed JWT Bearer access token")
    token_type: str = Field(default="bearer", description="Token scheme (Bearer)")
    doctor: DoctorSummary = Field(..., description="Authenticated physician profile summary")