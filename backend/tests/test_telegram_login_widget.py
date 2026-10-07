import hashlib
import hmac

import pytest
from fastapi import HTTPException

from client.telegram import verify_login_widget_payload
from pages import telegram as telegram_module
from schemas.telegram import TelegramConnectRequest
from schemas.token import TokenPayload


def signed_widget_payload(bot_token: str, **fields):
    check_string = "\n".join(f"{key}={value}" for key, value in sorted(fields.items()))
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    fields["hash"] = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()
    return fields


def test_widget_signature_verifies_and_rejects_tampering(monkeypatch):
    token = "test-bot-token"
    monkeypatch.setattr("client.config.settings.TELEGRAM_BOT_TOKEN", token)
    payload = signed_widget_payload(
        token,
        id=123456789,
        first_name="Ada Lovelace ",
        username="ada",
        auth_date=1_700_000_000,
    )

    assert verify_login_widget_payload(payload, now=1_700_000_100)
    payload["first_name"] = "Ada Lovelace"
    assert not verify_login_widget_payload(payload, now=1_700_000_100)


@pytest.mark.asyncio
async def test_widget_config_exposes_username_without_bot_token(monkeypatch):
    monkeypatch.setattr(telegram_module.settings, "TELEGRAM_BOT_USERNAME", "@docpilot_AIbot")

    config = await telegram_module.telegram_widget_config()

    assert config.bot_username == "docpilot_AIbot"
    assert "token" not in config.model_dump()


@pytest.mark.parametrize("auth_date", [1_699_999_699, 1_700_000_131])
def test_widget_signature_rejects_stale_or_future_payload(monkeypatch, auth_date):
    token = "test-bot-token"
    monkeypatch.setattr("client.config.settings.TELEGRAM_BOT_TOKEN", token)
    payload = signed_widget_payload(token, id=123456789, first_name="Ada", auth_date=auth_date)

    assert not verify_login_widget_payload(payload, now=1_700_000_100)


@pytest.mark.asyncio
async def test_connect_links_only_verified_widget_identity(monkeypatch):
    token = "test-bot-token"
    monkeypatch.setattr(telegram_module.settings, "TELEGRAM_BOT_TOKEN", token)
    connected = {}

    async def upsert(doctor_id, telegram_user_id, telegram_username):
        connected.update({
            "doctor_id": doctor_id,
            "telegram_user_id": telegram_user_id,
            "telegram_username": telegram_username,
        })
        return {"id": "connection-1"}

    monkeypatch.setattr(telegram_module, "upsert_telegram_connection", upsert)
    payload = TelegramConnectRequest(**signed_widget_payload(
        token,
        id=123456789,
        first_name="Ada",
        username="ada",
        auth_date=1_700_000_000,
    ))
    monkeypatch.setattr("client.telegram.time.time", lambda: 1_700_000_100)

    result = await telegram_module.connect_telegram(payload, TokenPayload(sub="doctor-1"))

    assert connected == {
        "doctor_id": "doctor-1",
        "telegram_user_id": 123456789,
        "telegram_username": "ada",
    }
    assert result.telegram_user_id == 123456789


@pytest.mark.asyncio
async def test_connect_rejects_invalid_widget_signature(monkeypatch):
    monkeypatch.setattr(telegram_module.settings, "TELEGRAM_BOT_TOKEN", "test-bot-token")
    payload = TelegramConnectRequest(
        id=123456789,
        first_name="Ada",
        auth_date=1_700_000_000,
        hash="0" * 64,
    )

    with pytest.raises(HTTPException) as error:
        await telegram_module.connect_telegram(payload, TokenPayload(sub="doctor-1"))

    assert error.value.status_code == 401