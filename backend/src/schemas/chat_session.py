from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ChatSessionCreate(BaseModel):
    """Payload to initiate a new clinical consultation session."""
    model_config = ConfigDict(str_strip_whitespace=True)

    title: Optional[str] = Field(
        default=None,
        description="Optional title for the consultation session. If omitted, generated automatically from initial messages.",
        examples=["Maria Santos - Initial Diabetes Review"],
    )


class ChatSessionResponse(BaseModel):
    """Metadata response representing a doctor's consultation session."""
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    id: str = Field(..., description="Unique consultation session ID (e.g. sess_a1b2c3d4)")
    doctor_id: str = Field(..., description="Doctor ID who owns this consultation session")
    title: str = Field(..., description="Session title or headline summary")
    created_at: str = Field(..., description="ISO 8601 timestamp of session creation")
    updated_at: str = Field(..., description="ISO 8601 timestamp of most recent activity")
    message_count: int = Field(default=0, description="Total count of messages exchanged in this session")
