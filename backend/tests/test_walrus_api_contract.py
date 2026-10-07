import pytest

from client.walrus import WalrusClient


@pytest.mark.asyncio
async def test_walrus_initialize_uses_current_memwal_api(monkeypatch):
    captured = {}

    class FakeMemWal:
        @classmethod
        def create(cls, **kwargs):
            captured.update(kwargs)
            return cls()

        async def remember_and_wait(self, text, namespace=None, timeout_ms=None):
            captured["remembered_text"] = text
            captured["remember_namespace"] = namespace
            captured["remember_timeout_ms"] = timeout_ms
            return {"ok": True}

        async def recall(self, query, limit=10, namespace=None, max_distance=None):
            return {"results": []}

    class FakeMemWalMock:
        async def remember(self, text, namespace=None, idempotency_key=None):
            return {"ok": True}

        async def recall(self, query, limit=10, namespace=None, max_distance=None):
            return {"results": []}

    fake_memwal = type("FakeMemwalModule", (), {"MemWal": FakeMemWal, "MemWalMock": FakeMemWalMock})

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
    assert captured["env"] == "dev"
    assert client._client is not None
    assert await client.remember("private clinical note", "doctor-a") is True
    assert captured["remember_namespace"] == "doctor_doctor_a"
    assert captured["remember_timeout_ms"] == 60_000


@pytest.mark.asyncio
async def test_walrus_initialize_fails_instead_of_falling_back_to_mock(monkeypatch):
    class FakeMemWal:
        @classmethod
        def create(cls, **kwargs):
            raise ConnectionError("relayer unavailable")

    fake_memwal = type(
        "FakeMemwalModule",
        (),
        {"MemWal": FakeMemWal},
    )
    monkeypatch.setattr("client.config.settings.WALRUS_ENABLED", True)
    monkeypatch.setattr("client.config.settings.WALRUS_DELEGATE_KEY", "test-delegate-key")
    monkeypatch.setattr("client.config.settings.WALRUS_ACCOUNT_ID", "test-account")
    monkeypatch.setitem(__import__("sys").modules, "memwal", fake_memwal)

    client = WalrusClient()

    with pytest.raises(RuntimeError, match="Live Walrus memory initialization failed"):
        await client.initialize()

    assert client._client is None


@pytest.mark.asyncio
async def test_walrus_recall_and_write_errors_are_not_silently_ignored():
    class BrokenMemWal:
        async def recall(self, **kwargs):
            raise ConnectionError("relayer unavailable")

        async def remember_and_wait(self, *args, **kwargs):
            raise ConnectionError("relayer unavailable")

    client = WalrusClient()
    client._client = BrokenMemWal()

    with pytest.raises(RuntimeError, match="Failed to recall clinical memory"):
        await client.recall("check history", "doctor-a")
    with pytest.raises(RuntimeError, match="Failed to persist clinical memory"):
        await client.remember("clinical note", "doctor-a")
