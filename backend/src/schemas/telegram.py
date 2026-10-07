"""Pydantic schemas for Telegram webhook and account linking."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class TelegramConnectRequest(BaseModel):
    """Signed Telegram Login Widget payload; the backend verifies its hash."""
    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., gt=0, description="Telegram user ID from the signed widget payload.")
    first_name: str = Field(..., min_length=1, max_length=256)
    last_name: Optional[str] = Field(default=None, max_length=256)
    username: Optional[str] = Field(default=None, max_length=64)
    photo_url: Optional[str] = Field(default=None, max_length=2048)
    auth_date: int = Field(..., gt=0)
    hash: str = Field(..., min_length=64, max_length=64, pattern=r"^[0-9a-fA-F]{64}$")


class TelegramWidgetConfig(BaseModel):
    """Public configuration needed to render the Telegram Login Widget."""
    bot_username: str


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
