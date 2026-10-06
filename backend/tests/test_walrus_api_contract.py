import pytest

from client.walrus import WalrusClient


@pytest.mark.asyncio
async def test_walrus_initialize_uses_current_memwal_api(monkeypatch):
    captured = {}

    class FakeMemWal:
        @classmethod
        async def create(cls, **kwargs):
            captured.update(kwargs)
            return cls()

        async def remember(self, text, namespace=None, idempotency_key=None):
            return {"ok": True}

        async def recall(self, query, limit=10, namespace=None, max_distance=None):
            return {"results": []}

    class FakeMemWalMock:
        async def remember(self, text, namespace=None, idempotency_key=None):
            return {"ok": True}

        async def recall(self, query, limit=10, namespace=None, max_distance=None):
            return {"results": []}

    fake_memwal = type("FakeMemwalModule", (), {"MemWal": FakeMemWal, "MemWalMock": FakeMemWalMock, "ENV_PRESETS": {"dev": "https://relayer.dev.memwal.ai"}})

    monkeypatch.setattr("client.config.settings.WALRUS_ENABLED", True)
    monkeypatch.setattr("client.config.settings.WALRUS_DELEGATE_KEY", "test-delegate-key")
    monkeypatch.setattr("client.config.settings.WALRUS_ACCOUNT_ID", "test-account")
    monkeypatch.setattr("client.config.settings.WALRUS_SERVER_URL", "https://relayer.dev.memwal.ai")
    monkeypatch.setattr("client.config.settings.WALRUS_ENV", "dev")

    monkeypatch.setitem(__import__("sys").modules, "memwal", fake_memwal)

    client = WalrusClient()
    await client.initialize()

    assert captured["key"] == "test-delegate-key"
    assert "delegate_private_key" not in captured
    assert client._client is not None
