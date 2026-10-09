import asyncio
import sys
from pathlib import Path
import pytest
from httpx import ASGITransport, AsyncClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from client.config import settings
from client.keepalive import (
    get_render_target_url,
    ping_endpoint,
    start_keepalive_service,
    stop_keepalive_service,
)
from main import app


def test_get_render_target_url_prefers_render_external_url(monkeypatch):
    monkeypatch.setattr(settings, "RENDER_EXTERNAL_URL", "https://custom-docpilot.onrender.com")
    url = get_render_target_url()
    assert url == "https://custom-docpilot.onrender.com"


def test_get_render_target_url_derives_from_telegram_webhook(monkeypatch):
    monkeypatch.setattr(settings, "RENDER_EXTERNAL_URL", None)
    monkeypatch.setattr(
        settings,
        "TELEGRAM_WEBHOOK_URL",
        "https://docpilot-yxh9.onrender.com/telegram/webhook",
    )
    url = get_render_target_url()
    assert url == "https://docpilot-yxh9.onrender.com"


@pytest.mark.asyncio
async def test_ping_and_health_endpoints_respond_with_status_ok():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test /health
        health_resp = await client.get("/health")
        assert health_resp.status_code == 200
        assert health_resp.json()["status"] == "ok"

        # Test /ping
        ping_resp = await client.get("/ping")
        assert ping_resp.status_code == 200
        assert ping_resp.json()["status"] == "pong"


@pytest.mark.asyncio
async def test_keepalive_service_lifecycle(monkeypatch):
    monkeypatch.setattr(settings, "RENDER_KEEP_ALIVE_ENABLED", True)
    monkeypatch.setattr(settings, "RENDER_EXTERNAL_URL", "https://test.onrender.com")
    monkeypatch.setattr(settings, "RENDER_PING_INTERVAL_SECONDS", 100)

    task = start_keepalive_service()
    assert task is not None
    assert not task.done()

    await stop_keepalive_service()
    assert task.done() or task.cancelled()


def test_render_ping_interval_defaults_to_fourteen_minutes():
    from client.config import ClientSettings

    default_settings = ClientSettings(_env_file=None)
    assert default_settings.RENDER_PING_INTERVAL_SECONDS == 840  # 14 minutes
