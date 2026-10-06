from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from schemas.attachment import AttachmentSchema
from schemas.clinical_entity import ExtractedClinicalEntity


class ChatMessageCreate(BaseModel):
    """Payload to append a message to a session."""
    model_config = ConfigDict(str_strip_whitespace=True)

    role: str = Field(..., description="Message author role ('doctor', 'assistant', or 'system')")
    content: str = Field(..., description="Clinical message text or observation")
    attachments: Optional[List[AttachmentSchema]] = Field(
        default=None,
        description="Optional multimodal attachments submitted with the message",
    )


class ChatMessageItem(BaseModel):
    """Historical message item within a consultation session."""
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    id: str = Field(..., description="Unique message ID")
    session_id: str = Field(..., description="Session ID to which this message belongs")
    role: str = Field(..., description="Message author role ('doctor' or 'assistant')")
    content: str = Field(..., description="Clinical message text content")
    attachments: Optional[List[AttachmentSchema]] = Field(
        default=None,
        description="Multimodal files or records attached to this message",
    )
    action_taken: Optional[str] = Field(
        default=None,
        description="Action performed by DocPilot (e.g. 'update_memory', 'recall_memory', 'conversational')",
    )
    entities_extracted: Optional[List[ExtractedClinicalEntity]] = Field(
        default=None,
        description="Structured clinical entities extracted and persisted during this message",
    )
    created_at: str = Field(..., description="ISO 8601 timestamp when message was recorded")
