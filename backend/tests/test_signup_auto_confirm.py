from types import SimpleNamespace

import pytest

from auth import signup as signup_module
from schemas.signup import SignupRequest


@pytest.mark.asyncio
async def test_signup_auto_confirms_user_and_returns_supabase_session(monkeypatch):
    created_user = SimpleNamespace(id="doctor-123", email="doctor@example.com")
    session = SimpleNamespace(access_token="session-token", token_type="bearer")

    class FakeAdmin:
        payload = None

        async def create_user(self, payload):
            self.payload = payload
            return SimpleNamespace(user=created_user)

    class FakeAuth:
        def __init__(self):
            self.admin = FakeAdmin()
            self.signed_in_credentials = None

        async def sign_in_with_password(self, credentials):
            self.signed_in_credentials = credentials
            return SimpleNamespace(session=session)

    class FakeClient:
        def __init__(self):
            self.auth = FakeAuth()

    async def no_existing_doctor(email):
        return None

    async def create_doctor(**kwargs):
        return kwargs

    fake_client = FakeClient()
    monkeypatch.setattr(signup_module, "get_doctor_by_email", no_existing_doctor)
    monkeypatch.setattr(signup_module, "create_doctor", create_doctor)

    result = await signup_module.signup_doctor(
        SignupRequest(
            email="doctor@example.com",
            password="Clinical123",
            full_name="Dr. Example",
        ),
        client=fake_client,
    )

    assert fake_client.auth.admin.payload["email_confirm"] is True
    assert fake_client.auth.signed_in_credentials["email"] == "doctor@example.com"
    assert result.access_token == "session-token"
    assert result.doctor_id == "doctor-123"
