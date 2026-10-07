import pytest
from fastapi import HTTPException

from client import telegram as telegram_client_module
from pages import telegram as telegram_module


@pytest.mark.asyncio
async def test_telegram_webhook_requires_configured_secret(monkeypatch):
    monkeypatch.setattr(telegram_module.settings, "TELEGRAM_SECRET_TOKEN", "")

    with pytest.raises(HTTPException) as error:
        await telegram_module.telegram_webhook({}, "")

    assert error.value.status_code == 503


@pytest.mark.asyncio
async def test_telegram_webhook_rejects_invalid_secret(monkeypatch):
    monkeypatch.setattr(telegram_module.settings, "TELEGRAM_SECRET_TOKEN", "expected-secret")

    with pytest.raises(HTTPException) as error:
        await telegram_module.telegram_webhook({}, "wrong-secret")

    assert error.value.status_code == 403


@pytest.mark.asyncio
async def test_telegram_webhook_accepts_valid_secret(monkeypatch):
    monkeypatch.setattr(telegram_module.settings, "TELEGRAM_SECRET_TOKEN", "expected-secret")

    assert await telegram_module.telegram_webhook({}, "expected-secret") == {"ok": True}


@pytest.mark.asyncio
async def test_linked_telegram_message_uses_linked_doctor_memory_identity(monkeypatch):
    processed = []

    async def get_connection(telegram_user_id):
        assert telegram_user_id == 987654
        return {"doctor_id": "doctor-123"}

    async def get_memory_enabled(doctor_id):
        assert doctor_id == "doctor-123"
        return True

    async def process(**kwargs):
        processed.append(kwargs)
        return "Saved for this doctor.", "update_memory", [], None

    async def send_message(**kwargs):
        return True

    monkeypatch.setattr(telegram_module.settings, "TELEGRAM_SECRET_TOKEN", "expected-secret")
    monkeypatch.setattr(telegram_module, "get_connection_by_telegram_id", get_connection)
    monkeypatch.setattr(telegram_module, "get_doctor_memory_enabled", get_memory_enabled)
    monkeypatch.setattr(telegram_module.docpilot_agent, "process", process)
    monkeypatch.setattr(telegram_module.telegram_client, "send_message", send_message)

    response = await telegram_module.telegram_webhook(
        {
            "message": {
                "from": {"id": 987654},
                "chat": {"id": 987654},
                "text": "Please remember the patient's allergy.",
            }
        },
        "expected-secret",
    )

    assert response == {"ok": True}
    assert processed[0]["doctor_id"] == "doctor-123"
    assert processed[0]["memory_enabled"] is True


@pytest.mark.asyncio
async def test_webhook_setup_uses_configured_live_url_and_secret(monkeypatch):
    captured = {}

    class FakeTelegramClient:
        is_configured = True

        async def set_webhook(self, **kwargs):
            captured.update(kwargs)
            return True

    monkeypatch.setattr(telegram_module.settings, "TELEGRAM_WEBHOOK_URL", "https://docpilot-yxh9.onrender.com/telegram/webhook")
    monkeypatch.setattr(telegram_module.settings, "TELEGRAM_SECRET_TOKEN", "a" * 64)
    monkeypatch.setattr(telegram_client_module, "telegram_client", FakeTelegramClient())

    assert await telegram_client_module.configure_telegram_webhook() is True
    assert captured["webhook_url"] == "https://docpilot-yxh9.onrender.com/telegram/webhook"
    assert captured["secret_token"] == "a" * 64
    assert captured["allowed_updates"] == ["message", "edited_message"]
