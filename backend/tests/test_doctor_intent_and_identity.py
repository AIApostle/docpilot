"""Unit and integration tests for message intent classification, physician identity grounding, and profile documentation."""

import json
from unittest.mock import AsyncMock, patch
import pytest

from agent.core import (
    DocPilotCore,
    extract_doctor_intro_name,
    extract_doctor_name_from_context,
)
from agent.memory_extractor import format_memory_delta
from agent.prompts import build_clinical_prompt
from schemas.clinical_entity import ExtractedClinicalEntity


def test_extract_doctor_intro_name():
    assert extract_doctor_intro_name("i am doctor saviour") == "Dr. Saviour"
    assert extract_doctor_intro_name("I am Doctor Saviour") == "Dr. Saviour"
    assert extract_doctor_intro_name("I'm Dr. Saviour") == "Dr. Saviour"
    assert extract_doctor_intro_name("My name is doctor saviour") == "Dr. Saviour"
    assert extract_doctor_intro_name("Call me Dr. Saviour") == "Dr. Saviour"
    assert extract_doctor_intro_name("Doctor Saviour here") == "Dr. Saviour"
    assert extract_doctor_intro_name("I am Dr. John Smith and I have patient notes") == "Dr. John Smith"
    # Not an introduction
    assert extract_doctor_intro_name("Patient John Doe BP 120/80") is None
    assert extract_doctor_intro_name("who am i") is None


def test_extract_doctor_name_from_context():
    # Doctor details must come strictly from memory, not database profile
    assert extract_doctor_name_from_context(doctor_profile={"full_name": "Dr. Saviour"}) is None

    # From recalled memories
    memories = [
        "[2026-10-09 03:00 UTC] Physician Profile / Identity (Dr. Saviour): doctor_profile: Physician identity is Dr. Saviour"
    ]
    assert extract_doctor_name_from_context(recalled_memories=memories) == "Dr. Saviour"


def test_format_memory_delta_separates_doctor_from_patient():
    entities = [
        ExtractedClinicalEntity(
            patient_name="Dr. Saviour",
            category="doctor_profile",
            detail="Physician identity is Dr. Saviour",
        ),
        ExtractedClinicalEntity(
            patient_name="John Doe",
            category="vital_sign",
            detail="BP 140/90 mmHg",
        ),
    ]
    delta = format_memory_delta(entities, "I am Dr. Saviour. John Doe BP is 140/90.")
    assert "Physician Profile / Identity (Dr. Saviour): doctor_profile: Physician identity is Dr. Saviour" in delta
    assert "Patient: John Doe | vital_sign: BP 140/90 mmHg" in delta
    assert "Patient: Dr. Saviour" not in delta


def test_build_clinical_prompt_does_not_attach_physician_profile():
    # Physician profile must NOT be attached to the prompt
    prompt = build_clinical_prompt(
        doctor_message="who am i",
        doctor_profile={"full_name": "Dr. Saviour", "email": "saviour@hospital.org"},
        recalled_memories=["Physician identity is Dr. Saviour"],
    )
    assert "<PHYSICIAN_PROFILE>" not in prompt
    assert "- Attending Physician Name" not in prompt
    assert "<RECALLED_MEMORIES>" in prompt
    assert "Physician identity is Dr. Saviour" in prompt
    assert "who am i" in prompt


@pytest.mark.asyncio
async def test_doctor_introduction_saves_memory_and_updates_profile(monkeypatch):
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
            "response": "Welcome, Dr. Saviour. How can I assist you with your clinical consultations today?",
            "action_taken": "update_memory",
            "entities": [{
                "patient_name": "Dr. Saviour",
                "category": "doctor_profile",
                "detail": "Physician identity is Dr. Saviour",
            }],
            "suggested_title": "Physician Profile - Dr. Saviour",
        })

    monkeypatch.setattr("agent.core.get_walrus_client", fake_get_walrus_client)
    monkeypatch.setattr("agent.core.generate_chat_completion", fake_generate_chat_completion)

    with patch("db.doctors_queries.update_doctor_profile", new_callable=AsyncMock) as mock_update_db:
        resp, action, entities, title = await DocPilotCore().process(
            doctor_id="doc-saviour-1",
            message="i am doctor saviour",
            memory_enabled=True,
        )

    assert "Dr. Saviour" in resp
    assert action == "update_memory"
    assert len(entities) == 1
    assert entities[0].category == "doctor_profile"
    assert entities[0].patient_name == "Dr. Saviour"
    assert len(walrus.saved) == 1
    assert "Physician Profile / Identity (Dr. Saviour)" in walrus.saved[0]["content"]


@pytest.mark.asyncio
async def test_who_am_i_query_identifies_doctor_not_docpilot(monkeypatch):
    class FakeWalrus:
        async def recall(self, **kwargs):
            # Recalls previous introduction
            assert "physician profile" in kwargs["query"]
            return [
                "[2026-10-09 03:00 UTC] Physician Profile / Identity (Dr. Saviour): doctor_profile: Physician identity is Dr. Saviour"
            ]

        async def remember(self, **kwargs):
            return True

    async def fake_get_walrus_client():
        return FakeWalrus()

    # Suppose the LLM initially returned a response mistakenly identifying as DocPilot
    async def fake_generate_chat_completion(**kwargs):
        return json.dumps({
            "response": "I am DocPilot, an elite clinical AI assistant.",
            "action_taken": "conversational",
            "entities": [],
            "suggested_title": None,
        })

    monkeypatch.setattr("agent.core.get_walrus_client", fake_get_walrus_client)
    monkeypatch.setattr("agent.core.generate_chat_completion", fake_generate_chat_completion)

    resp, action, entities, title = await DocPilotCore().process(
        doctor_id="doc-saviour-1",
        message="who am i",
        memory_enabled=True,
    )

    # Must be corrected to identify Dr. Saviour!
    assert "Dr. Saviour" in resp
    assert "I am DocPilot" not in resp
    assert action == "recall_memory"


@pytest.mark.asyncio
async def test_who_are_you_query_identifies_assistant(monkeypatch):
    class FakeWalrus:
        async def recall(self, **kwargs):
            return []

        async def remember(self, **kwargs):
            return True

    async def fake_get_walrus_client():
        return FakeWalrus()

    async def fake_generate_chat_completion(**kwargs):
        return json.dumps({
            "response": "I am DocPilot, your clinical AI assistant with persistent patient memory.",
            "action_taken": "conversational",
            "entities": [],
            "suggested_title": None,
        })

    monkeypatch.setattr("agent.core.get_walrus_client", fake_get_walrus_client)
    monkeypatch.setattr("agent.core.generate_chat_completion", fake_generate_chat_completion)

    resp, action, entities, title = await DocPilotCore().process(
        doctor_id="doc-saviour-1",
        message="who are you",
        memory_enabled=True,
    )

    assert "DocPilot" in resp
    assert action == "conversational"


@pytest.mark.asyncio
async def test_stateless_who_am_i_respects_doctor_profile(monkeypatch):
    async def fake_generate_chat_completion(**kwargs):
        return json.dumps({
            "response": "You are Dr. Saviour.",
            "action_taken": "conversational",
            "entities": [],
            "suggested_title": None,
        })

    monkeypatch.setattr("agent.core.generate_chat_completion", fake_generate_chat_completion)

    resp, action, entities, title = await DocPilotCore().process(
        doctor_id="doc-saviour-1",
        message="who am i",
        memory_enabled=False,
        doctor_profile={"full_name": "Dr. Saviour"},
    )

    assert "Dr. Saviour" in resp
    assert action == "conversational"
