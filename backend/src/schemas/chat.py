"""Pydantic schemas for clinical chat and conversation interactions."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from schemas.attachment import AttachmentSchema
from schemas.clinical_entity import ExtractedClinicalEntity


class ChatRequest(BaseModel):
    """Clinical chat message payload from doctor."""
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)

    message: str = Field(..., description="Doctor's clinical note, query, or observation text.")
    session_id: Optional[str] = Field(
        default=None,
        description="Active consultation session identifier. If omitted, a new session is spawned.",
    )
    conversation_id: Optional[str] = Field(
        default=None,
        alias="conversation_id",
        description="Alias for session_id matching frontend chat contract.",
    )
    attachments: Optional[List[AttachmentSchema]] = Field(
        default=None,
        description="Optional multimodal medical records, lab reports, or images.",
    )

    def resolved_session_id(self) -> Optional[str]:
        return self.session_id or self.conversation_id


class ChatResponse(BaseModel):
    """Clinical assistant response payload returned to the physician."""
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)

    session_id: str = Field(..., description="Unique consultation session ID.")
    id: str = Field(..., description="Session identifier alias matching frontend contract.")
    response: str = Field(..., description="DocPilot clinical response text.")
    reply: str = Field(..., description="Clinical reply text alias matching frontend contract.")
    title: Optional[str] = Field(default=None, description="Updated session title or summary.")
    action_taken: Optional[str] = Field(
        default=None,
        description="Action performed (e.g., 'update_memory', 'recall_memory', 'conversational').",
    )
    entities_extracted: Optional[List[ExtractedClinicalEntity]] = Field(
        default=None,
        description="Clinical entities identified and persisted to memory during this interaction.",
    )
    updated_at: Optional[str] = Field(
        default=None,
        description="ISO 8601 timestamp of session update.",
    )


class ChatSummaryItem(BaseModel):
    """Summary item representing a doctor's consultation thread for listing."""
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    id: str = Field(..., description="Consultation ID")
    title: str = Field(..., description="Conversation title")
    updated_at: str = Field(..., description="Last updated timestamp")
    message_count: int = Field(default=0, description="Total messages count")


class ChatDetailMessage(BaseModel):
    """Message item inside a detailed conversation thread."""
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    id: str = Field(..., description="Message ID")
    role: str = Field(..., description="Role: 'user' (doctor) or 'assistant'")
    content: str = Field(..., description="Message content")
    created_at: str = Field(..., description="Timestamp")
    attachments: Optional[List[Dict[str, Any]]] = Field(default=None)


class ChatDetailResponse(BaseModel):
    """Detailed conversation with full message history."""
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    id: str = Field(..., description="Conversation ID")
    title: str = Field(..., description="Conversation title")
    updated_at: str = Field(..., description="Last updated timestamp")
    messages: List[ChatDetailMessage] = Field(default_factory=list)
