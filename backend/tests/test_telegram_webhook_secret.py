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