"""Pydantic schemas for Telegram webhook and account linking."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class TelegramConnectRequest(BaseModel):
    """Payload to link a doctor's account to a Telegram user ID."""
    model_config = ConfigDict(str_strip_whitespace=True)

    telegram_user_id: int = Field(..., description="Unique Telegram user ID.")
    telegram_username: Optional[str] = Field(default=None, description="Optional Telegram handle without @.")


class TelegramConnectResponse(BaseModel):
    """Result of linking Telegram to physician."""
    model_config = ConfigDict(str_strip_whitespace=True)

    status: str = Field(default="connected", description="Connection status.")
    doctor_id: str = Field(..., description="Doctor ID linked.")
    telegram_user_id: int = Field(..., description="Telegram user ID.")


class TelegramWebhookUpdate(BaseModel):
    """Simplified Telegram Update payload structure."""
    model_config = ConfigDict(extra="ignore")

    update_id: int
    message: Optional[Dict[str, Any]] = None
