import pytest
from pydantic import ValidationError

from pages import memory as memory_page
from schemas.memory import MemoryPreferenceUpdate
from schemas.token import TokenPayload


@pytest.mark.asyncio
async def test_memory_preference_routes_use_the_authenticated_doctor(monkeypatch):
    calls = []

    async def fake_get(doctor_id):
        calls.append(("get", doctor_id))
        return True

    async def fake_set(doctor_id, enabled):
        calls.append(("set", doctor_id, enabled))
        return enabled

    monkeypatch.setattr(memory_page, "get_doctor_memory_enabled", fake_get)
    monkeypatch.setattr(memory_page, "set_doctor_memory_enabled", fake_set)
    doctor = TokenPayload(sub="doctor-auth-id")

    current = await memory_page.get_memory_preference(doctor)
    updated = await memory_page.update_memory_preference(
        MemoryPreferenceUpdate(enabled=False),
        doctor,
    )

    assert current.enabled is True
    assert updated.enabled is False
    assert calls == [
        ("get", "doctor-auth-id"),
        ("set", "doctor-auth-id", False),
    ]


def test_memory_preference_rejects_non_boolean_values():
    with pytest.raises(ValidationError):
        MemoryPreferenceUpdate(enabled="false")


@pytest.mark.asyncio
async def test_get_doctor_memory_enabled_defaults_to_true_on_pgrst205(monkeypatch):
    from db.doctor_memory_preferences_queries import get_doctor_memory_enabled

    class FakeAPIError(Exception):
        code = "PGRST205"

    class FailingSupabase:
        def table(self, _name):
            raise FakeAPIError("Could not find table in schema cache")

    async def fake_client():
        return FailingSupabase()

    monkeypatch.setattr("db.doctor_memory_preferences_queries.get_supabase_data_client", fake_client)

    result = await get_doctor_memory_enabled("doctor-test-id")
    assert result is True


@pytest.mark.asyncio
async def test_set_doctor_memory_enabled_raises_helpful_error_on_pgrst205(monkeypatch):
    from db.doctor_memory_preferences_queries import DoctorMemoryPreferenceError, set_doctor_memory_enabled

    class FakeAPIError(Exception):
        code = "PGRST205"

    class FailingSupabase:
        def table(self, _name):
            raise FakeAPIError("Could not find table in schema cache")

    async def fake_client():
        return FailingSupabase()

    monkeypatch.setattr("db.doctor_memory_preferences_queries.get_supabase_data_client", fake_client)

    with pytest.raises(DoctorMemoryPreferenceError) as exc_info:
        await set_doctor_memory_enabled("doctor-test-id", False)
    assert "does not exist in Supabase yet" in str(exc_info.value)

