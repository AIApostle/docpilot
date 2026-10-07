from typing import Optional
import re
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class SignupRequest(BaseModel):
    """Physician registration payload with strict clinical security and input validation."""
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr = Field(
        ...,
        description="Physician professional email address",
        examples=["dr.smith@hospital.org"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Account password (minimum 8 characters, must include at least one letter and one number)",
        examples=["SecurePassword123!"],
    )
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Physician's full name, including clinical title",
        examples=["Dr. Sarah Smith, MD"],
    )

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Za-z]", value):
            raise ValueError("Password must contain at least one letter.")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit.")
        return value


# Alias preserving lowercase naming if referenced elsewhere
signupRequest = SignupRequest


class SignupResponse(BaseModel):
    """Response payload returned upon successful physician account creation."""
    doctor_id: str = Field(..., description="Unique physician identifier (e.g. doc_9f83b2e1)")
    email: EmailStr = Field(..., description="Registered physician email address")
    full_name: Optional[str] = Field(None, description="Physician's full name")
    access_token: str = Field(..., description="Signed JWT Bearer access token")
    token_type: str = Field(default="bearer", description="Token scheme (Bearer)")