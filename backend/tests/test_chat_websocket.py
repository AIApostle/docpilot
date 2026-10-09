"""Tests for DocPilot WebSocket chat endpoint and live status streaming."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from auth.jwt import create_access_token
from fastapi import FastAPI
from pages.chat import router as chat_router

app = FastAPI()
app.include_router(chat_router, prefix="/chat")
from schemas.clinical_entity import ExtractedClinicalEntity


@pytest.fixture
def test_doctor_token():
    return create_access_token({"sub": "doc-test-123", "email": "doctor@hospital.org"})


def test_websocket_rejects_unauthenticated_connection():
    client = TestClient(app)
    with client.websocket_connect("/chat/ws") as websocket:
        # Client did not provide query token, send invalid auth payload
        websocket.send_json({"type": "auth", "token": "invalid-token"})
        msg = websocket.receive_json()
        assert msg["type"] == "error"
        assert "Authentication failed" in msg["detail"]


def test_websocket_connects_with_query_token(test_doctor_token):
    client = TestClient(app)
    with client.websocket_connect(f"/chat/ws?token={test_doctor_token}") as websocket:
        msg = websocket.receive_json()
        assert msg["type"] == "connected"
        assert msg["doctor_id"] == "doc-test-123"

        # Ping pong
        websocket.send_json({"type": "ping"})
        pong = websocket.receive_json()
        assert pong["type"] == "pong"


def test_websocket_streams_dynamic_status_updates(test_doctor_token, monkeypatch):
    """Verifies that remembering and documenting have distinct appropriate status updates."""
    client = TestClient(app)

    async def fake_get_pref(doc_id):
        return True

    async def fake_get_session(session_id, doctor_id):
        return {"id": "session-123", "title": "Existing consult"}

    async def fake_create_msg(**kwargs):
        return True

    async def fake_update_session(**kwargs):
        return True

    async def fake_agent_process(doctor_id, message, memory_enabled=True, attachments=None, on_status=None):
        if on_status:
            await on_status("recalling", "Remembering clinical context…")
            await on_status("thinking", "DocPilot is thinking…")
            await on_status("documenting", "Documenting clinical findings…")
        return (
            "Blood pressure is elevated at 145/92 mmHg.",
            "update_memory",
            [ExtractedClinicalEntity(patient_name="John", category="vital_sign", detail="BP 145/92")],
            "John Doe - Vitals",
        )

    monkeypatch.setattr("pages.chat.get_doctor_memory_enabled", fake_get_pref)
    monkeypatch.setattr("pages.chat.get_chat_session", fake_get_session)
    monkeypatch.setattr("pages.chat.create_chat_message", fake_create_msg)
    monkeypatch.setattr("pages.chat.update_chat_session", fake_update_session)
    monkeypatch.setattr("pages.chat.docpilot_agent.process", fake_agent_process)

    with client.websocket_connect(f"/chat/ws?token={test_doctor_token}") as websocket:
        conn = websocket.receive_json()
        assert conn["type"] == "connected"

        websocket.send_json({
            "type": "message",
            "message": "Patient John Doe BP is 145/92",
            "conversation_id": "session-123",
        })

        statuses = []
        final_response = None
        while True:
            frame = websocket.receive_json()
            if frame.get("type") == "status":
                statuses.append(frame)
            elif frame.get("type") == "response":
                final_response = frame
                break

        # Verify distinct status phases
        stages = [s["stage"] for s in statuses]
        messages = [s["message"] for s in statuses]

        assert "recalling" in stages
        assert "thinking" in stages
        assert "documenting" in stages
        assert "Remembering clinical context…" in messages
        assert "DocPilot is thinking…" in messages
        assert "Documenting clinical findings…" in messages

        # Verify final response
        assert final_response is not None
        assert final_response["id"] == "session-123"
        assert "Blood pressure is elevated" in final_response["reply"]
        assert final_response["action_taken"] == "update_memory"
