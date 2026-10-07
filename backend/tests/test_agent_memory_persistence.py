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

    monkeypatch.setattr(chat_page, "create_chat_session", fake_create_session)
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
