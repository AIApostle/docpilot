"""Centralized Telegram Bot API Client for DocPilot."""

import logging
import hashlib
import hmac
import time
from typing import Any, Dict, Optional
import httpx
from client.config import settings

logger = logging.getLogger(__name__)


def verify_login_widget_payload(payload: Dict[str, Any], now: Optional[int] = None) -> bool:
    """Verify Telegram Login Widget data and reject stale or future-dated payloads."""
    bot_token = settings.TELEGRAM_BOT_TOKEN.strip()
    if not bot_token:
        raise RuntimeError("Telegram bot token is not configured.")

    supplied_hash = payload.get("hash")
    auth_date = payload.get("auth_date")
    if not isinstance(supplied_hash, str) or len(supplied_hash) != 64:
        return False
    if not isinstance(auth_date, int) or isinstance(auth_date, bool):
        return False

    current_time = int(time.time()) if now is None else now
    if auth_date > current_time + 30 or current_time - auth_date > 300:
        return False

    check_string = "\n".join(
        f"{key}={value}"
        for key, value in sorted(payload.items())
        if key != "hash" and value is not None
    )
    secret_key = hashlib.sha256(bot_token.encode("utf-8")).digest()
    expected_hash = hmac.new(
        secret_key,
        check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected_hash, supplied_hash)


class TelegramClient:
    """Manages Telegram Bot API interactions."""

    def __init__(self, bot_token: Optional[str] = None):
        self.bot_token = (bot_token or settings.TELEGRAM_BOT_TOKEN).strip()
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token)

    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "Markdown",
    ) -> bool:
        """Sends a message to a Telegram chat."""
        if not self.is_configured:
            logger.warning("Telegram bot token not configured; cannot send message.")
            return False

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    return True
                # If markdown parsing fails, retry with plain text
                if "can't parse entities" in res.text:
                    payload.pop("parse_mode", None)
                    retry_res = await client.post(url, json=payload)
                    return retry_res.status_code == 200
                logger.error("Telegram sendMessage returned %s: %s", res.status_code, res.text)
                return False
        except Exception as exc:
            logger.error("Failed to send Telegram message to chat %s: %s", chat_id, exc)
            return False

    async def set_webhook(self, webhook_url: str, secret_token: Optional[str] = None) -> bool:
        """Sets the Telegram bot webhook URL."""
        if not self.is_configured:
            return False

        url = f"{self.base_url}/setWebhook"
        payload: Dict[str, Any] = {"url": webhook_url}
        if secret_token:
            payload["secret_token"] = secret_token

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload)
                data = res.json()
                return bool(data.get("ok"))
        except Exception as exc:
            logger.error("Failed to set Telegram webhook to %s: %s", webhook_url, exc)
            return False


telegram_client = TelegramClient()
