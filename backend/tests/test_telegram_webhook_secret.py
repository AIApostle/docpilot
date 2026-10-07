import pytest
from fastapi import HTTPException

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

    async def process(**kwargs):
        processed.append(kwargs)
        return "Saved for this doctor.", "update_memory", [], None

    async def send_message(**kwargs):
        return True

    monkeypatch.setattr(telegram_module.settings, "TELEGRAM_SECRET_TOKEN", "expected-secret")
    monkeypatch.setattr(telegram_module, "get_connection_by_telegram_id", get_connection)
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