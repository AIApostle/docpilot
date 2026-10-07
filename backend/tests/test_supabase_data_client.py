from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from client import supabase_client


@pytest.mark.asyncio
async def test_data_client_uses_service_role_key(monkeypatch):
    fake_client = object()
    create_client = AsyncMock(return_value=fake_client)
    monkeypatch.setattr(supabase_client, "_data_supabase_client", None)
    monkeypatch.setattr(supabase_client.settings, "SUPABASE_URL", "https://project.supabase.co")
    monkeypatch.setattr(supabase_client.settings, "SUPABASE_SERVICE_ROLE_KEY", "service-role")
    monkeypatch.setattr(supabase_client.settings, "SUPABASE_KEY", "anon-key")
    monkeypatch.setattr(supabase_client.settings, "SUPABASE_ANON_KEY", "anon-key")
    monkeypatch.setattr(supabase_client, "create_async_client", create_client)

    assert await supabase_client.get_supabase_data_client() is fake_client

    create_client.assert_awaited_once_with(
        supabase_url="https://project.supabase.co",
        supabase_key="service-role",
    )


@pytest.mark.asyncio
async def test_data_client_requires_service_role_key(monkeypatch):
    monkeypatch.setattr(supabase_client, "_data_supabase_client", None)
    monkeypatch.setattr(supabase_client.settings, "SUPABASE_URL", "https://project.supabase.co")
    monkeypatch.setattr(supabase_client.settings, "SUPABASE_SERVICE_ROLE_KEY", "")

    with pytest.raises(HTTPException) as error:
        await supabase_client.get_supabase_data_client()

    assert error.value.status_code == 503
