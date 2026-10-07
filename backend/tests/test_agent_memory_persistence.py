import json

import pytest
from fastapi import HTTPException

from agent.core import DocPilotCore
from client.walrus import WalrusUnavailableError
from pages import chat as chat_page
from schemas.chat import ChatRequest
from schemas.token import TokenPayload


@pytest.mark.asyncio
async def test_explicit_remember_request_persists_without_extracted_entities(monkeypatch):
    class FakeWalrus:
        def __init__(self):
            self.saved = []

        async def recall(self, **kwargs):
            return []

        async def remember(self, **kwargs):
            self.saved.append(kwargs)
            return True

    walrus = FakeWalrus()

    async def fake_get_walrus_client():
        return walrus

    async def fake_generate_chat_completion(**kwargs):
        return json.dumps({
            "response": "I will remember that preference.",
            "action_taken": "conversational",
            "entities": [],
            "suggested_title": None,
        })

    monkeypatch.setattr("agent.core.get_walrus_client", fake_get_walrus_client)
    monkeypatch.setattr("agent.core.generate_chat_completion", fake_generate_chat_completion)

    result = await DocPilotCore().process(
        doctor_id="doctor-123",
        message="Please remember that I prefer concise summaries.",
    )

    assert len(walrus.saved) == 1
    assert walrus.saved[0]["doctor_id"] == "doctor-123"
    assert "prefer concise summaries" in walrus.saved[0]["content"]
    assert result[1] == "update_memory"


@pytest.mark.asyncio
async def test_memory_off_skips_memwal_and_previous_turns(monkeypatch):
    async def fail_if_memwal_is_initialized():
        raise AssertionError("MemWal must not be initialized while memory is off")

    captured = {}

    async def fake_generate_chat_completion(**kwargs):
        captured["messages"] = kwargs["messages"]
        return json.dumps({
            "response": "I cannot retain that for another conversation.",
            "action_taken": "update_memory",
            "entities": [{
                "patient_name": "Patient A",
                "category": "allergy",
                "detail": "Latex",
            }],
            "suggested_title": None,
        })

    monkeypatch.setattr("agent.core.get_walrus_client", fail_if_memwal_is_initialized)
    monkeypatch.setattr("agent.core.generate_chat_completion", fake_generate_chat_completion)

    result = await DocPilotCore().process(
        doctor_id="doctor-123",
        message="Please remember that I prefer concise summaries.",
        memory_enabled=False,
    )

    assert "MemWal memory is OFF" in captured["messages"][0]["content"]
    assert len(captured["messages"]) == 2
    assert result[1] == "conversational"
    assert result[2] == []


@pytest.mark.asyncio
async def test_chat_returns_unavailable_without_saving_turn_when_walrus_fails(monkeypatch):
    stored_messages = []

    async def fake_create_session(**kwargs):
        return {"id": "temporary-session", "doctor_id": kwargs["doctor_id"], "title": kwargs["title"]}

    async def fake_list_messages(**kwargs):
        return []

    async def fake_create_message(**kwargs):
        stored_messages.append(kwargs)

    async def fake_process(**kwargs):
        raise WalrusUnavailableError("credentials missing")

    async def fake_memory_enabled(doctor_id):
        assert doctor_id == "doctor-123"
        return True

    monkeypatch.setattr(chat_page, "create_chat_session", fake_create_session)
    monkeypatch.setattr(chat_page, "get_doctor_memory_enabled", fake_memory_enabled)
    monkeypatch.setattr(chat_page, "list_messages_by_session_id", fake_list_messages)
    monkeypatch.setattr(chat_page, "create_chat_message", fake_create_message)
    monkeypatch.setattr(chat_page.docpilot_agent, "process", fake_process)

    with pytest.raises(HTTPException) as error:
        await chat_page.send_message(
            ChatRequest(message="Remember this clinical fact."),
            TokenPayload(sub="doctor-123"),
        )

    assert error.value.status_code == 503
    assert stored_messages == []


@pytest.mark.asyncio
async def test_chat_does_not_load_previous_turns_when_memory_is_off(monkeypatch):
    process_call = {}

    async def fake_memory_enabled(doctor_id):
        assert doctor_id == "doctor-123"
        return False

    async def fake_create_session(**kwargs):
        return {"id": "temporary-session", "doctor_id": kwargs["doctor_id"], "title": kwargs["title"]}

    async def fail_if_history_is_loaded(**kwargs):
        raise AssertionError("Prior turns must not be loaded while memory is off")

    async def fake_create_message(**kwargs):
        return None

    async def fake_update_session(**kwargs):
        return None

    async def fake_process(**kwargs):
        process_call.update(kwargs)
        return "Stateless reply.", "conversational", [], None

    monkeypatch.setattr(chat_page, "get_doctor_memory_enabled", fake_memory_enabled)
    monkeypatch.setattr(chat_page, "create_chat_session", fake_create_session)
    monkeypatch.setattr(chat_page, "list_messages_by_session_id", fail_if_history_is_loaded)
    monkeypatch.setattr(chat_page, "create_chat_message", fake_create_message)
    monkeypatch.setattr(chat_page, "update_chat_session", fake_update_session)
    monkeypatch.setattr(chat_page.docpilot_agent, "process", fake_process)

    response = await chat_page.send_message(
        ChatRequest(message="What do I need to know?"),
        TokenPayload(sub="doctor-123"),
    )

    assert process_call["memory_enabled"] is False
    assert "conversation_history" not in process_call
    assert response["memory_enabled"] is False
