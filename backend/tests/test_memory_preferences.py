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
