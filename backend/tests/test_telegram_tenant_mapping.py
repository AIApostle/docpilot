import pytest

from db.telegram_queries import upsert_telegram_connection


@pytest.mark.asyncio
async def test_upsert_rejects_reused_telegram_user_for_different_doctor(monkeypatch):
    async def fake_get_connection_by_doctor_id(doctor_id):
        return None

    async def fake_get_connection_by_telegram_id(telegram_user_id):
        return {"doctor_id": "doctor-b", "telegram_user_id": telegram_user_id, "is_active": True}

    monkeypatch.setattr("db.telegram_queries.get_connection_by_doctor_id", fake_get_connection_by_doctor_id)
    monkeypatch.setattr("db.telegram_queries.get_connection_by_telegram_id", fake_get_connection_by_telegram_id)

    with pytest.raises(ValueError, match="already linked to doctor"):
        await upsert_telegram_connection("doctor-a", 123456, "dr_a")


@pytest.mark.asyncio
async def test_upsert_allows_single_doctor_link(monkeypatch):
    async def fake_get_connection_by_doctor_id(doctor_id):
        return None

    async def fake_get_connection_by_telegram_id(telegram_user_id):
        return None

    class FakeSupabase:
        def table(self, table_name):
            return self

        def insert(self, payload):
            self.payload = payload
            return self

        async def execute(self):
            return type("Resp", (), {"data": [self.payload]})()

    fake_client = FakeSupabase()

    monkeypatch.setattr("db.telegram_queries.get_connection_by_doctor_id", fake_get_connection_by_doctor_id)
    monkeypatch.setattr("db.telegram_queries.get_connection_by_telegram_id", fake_get_connection_by_telegram_id)
    monkeypatch.setattr("db.telegram_queries.get_supabase_data_client", lambda: _async_fake_supabase_client(fake_client))

    async def _async_fake_supabase_client(client):
        return client

    result = await upsert_telegram_connection("doctor-a", 456789, "dr_b")

    assert result["doctor_id"] == "doctor-a"
    assert result["telegram_user_id"] == 456789
    assert result["is_active"] is True
