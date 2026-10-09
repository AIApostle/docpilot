import base64
import json
import pytest

from agent.core import DocPilotCore
from agent.document_parser import (
    ParsedDocument,
    chunk_document_for_indexing,
    parse_document,
)
from agent.prompts import build_clinical_prompt
from pages.chat import _format_message_dict


def test_parse_plain_text_document():
    raw_content = "Patient John Doe. Allergies: Penicillin. Vitals: BP 120/80."
    b64_content = base64.b64encode(raw_content.encode("utf-8")).decode("ascii")

    parsed = parse_document({
        "filename": "clinical_note.txt",
        "file_type": "text/plain",
        "content_base64": b64_content,
    })

    assert parsed.filename == "clinical_note.txt"
    assert parsed.file_type == "text/plain"
    assert "Patient John Doe" in parsed.text_content
    assert parsed.char_count == len(raw_content)
    assert not parsed.is_image


def test_parse_csv_tabular_document():
    csv_raw = "Test Name,Result,Reference Range\nHbA1c,8.2%,<5.7%\nFasting Glucose,145 mg/dL,70-99 mg/dL"
    b64_content = base64.b64encode(csv_raw.encode("utf-8")).decode("ascii")

    parsed = parse_document({
        "filename": "labs.csv",
        "file_type": "text/csv",
        "content_base64": b64_content,
    })

    assert parsed.filename == "labs.csv"
    assert "HbA1c" in parsed.text_content
    assert "8.2%" in parsed.text_content
    assert "|" in parsed.text_content


def test_parse_json_document():
    json_data = {"patient": "Jane Smith", "prescriptions": ["Metformin 500mg BID", "Lisinopril 10mg QD"]}
    b64_content = base64.b64encode(json.dumps(json_data).encode("utf-8")).decode("ascii")

    parsed = parse_document({
        "filename": "medications.json",
        "file_type": "application/json",
        "content_base64": b64_content,
    })

    assert "Jane Smith" in parsed.text_content
    assert "Metformin" in parsed.text_content


def test_parse_image_attachment():
    # 1x1 transparent PNG bytes
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
    b64_content = base64.b64encode(png_bytes).decode("ascii")

    parsed = parse_document({
        "filename": "chest_xray.png",
        "file_type": "image/png",
        "content_base64": b64_content,
        "description": "AP view chest X-ray",
    })

    assert parsed.filename == "chest_xray.png"
    assert parsed.is_image is True
    assert parsed.image_data_url is not None
    assert parsed.image_data_url.startswith("data:image/png;base64,")
    assert "chest_xray.png" in parsed.text_content
    assert "AP view chest X-ray" in parsed.text_content


def test_chunk_document_for_indexing():
    short_doc = ParsedDocument(
        filename="short.txt",
        file_type="text/plain",
        text_content="Brief patient note.",
        char_count=18,
    )
    chunks = chunk_document_for_indexing(short_doc)
    assert len(chunks) == 1
    assert "[Document: short.txt]" in chunks[0]
    assert "Brief patient note." in chunks[0]

    # Long document
    paragraphs = [f"Paragraph {i}: Detailed clinical examination findings for section {i}." for i in range(25)]
    long_doc = ParsedDocument(
        filename="long_consultation.txt",
        file_type="text/plain",
        text_content="\n\n".join(paragraphs),
        char_count=sum(len(p) for p in paragraphs),
    )
    long_chunks = chunk_document_for_indexing(long_doc, max_chunk_chars=300)
    assert len(long_chunks) > 1
    for chunk in long_chunks:
        assert "[Document: long_consultation.txt" in chunk


def test_build_clinical_prompt_includes_attached_documents():
    prompt = build_clinical_prompt(
        doctor_message="What are the patient's lab trends?",
        recalled_memories=["Patient has type 2 diabetes"],
        documents=[
            {
                "filename": "lab_report.pdf",
                "file_type": "application/pdf",
                "text_content": "HbA1c: 7.9% | Fasting blood glucose: 138 mg/dL",
            }
        ],
    )

    assert "<ATTACHED_DOCUMENTS>" in prompt
    assert "lab_report.pdf" in prompt
    assert "HbA1c: 7.9%" in prompt
    assert "<RECALLED_MEMORIES>" in prompt
    assert "What are the patient's lab trends?" in prompt


@pytest.mark.asyncio
async def test_agent_processes_and_indexes_attached_documents(monkeypatch):
    class FakeWalrus:
        def __init__(self):
            self.saved = []

        async def recall(self, **kwargs):
            return ["Patient Maria has hypertension"]

        async def remember(self, **kwargs):
            self.saved.append(kwargs)
            return True

    walrus = FakeWalrus()

    async def fake_get_walrus():
        return walrus

    captured_messages = []

    async def fake_generate_completion(**kwargs):
        captured_messages.extend(kwargs.get("messages", []))
        return json.dumps({
            "response": "Reviewed the CBC report for Maria. WBC is normal at 6.8 K/uL.",
            "action_taken": "update_memory",
            "entities": [
                {
                    "patient_name": "Maria",
                    "category": "lab_result",
                    "detail": "WBC 6.8 K/uL normal",
                }
            ],
            "suggested_title": "Maria - CBC Review",
        })

    monkeypatch.setattr("agent.core.get_walrus_client", fake_get_walrus)
    monkeypatch.setattr("agent.core.generate_chat_completion", fake_generate_completion)

    doc_text = "CBC Report for Maria. WBC: 6.8 K/uL. RBC: 4.5 M/uL. Platelets: 240 K/uL."
    b64_doc = base64.b64encode(doc_text.encode("utf-8")).decode("ascii")

    response_text, action, entities, title = await DocPilotCore().process(
        doctor_id="doctor-abc",
        message="Please analyze this CBC report.",
        memory_enabled=True,
        attachments=[{
            "filename": "cbc_report.txt",
            "file_type": "text/plain",
            "content_base64": b64_doc,
        }],
    )

    # 1. AI saw the documents in prompt
    user_prompt = captured_messages[1]["content"]
    assert "<ATTACHED_DOCUMENTS>" in user_prompt
    assert "cbc_report.txt" in user_prompt
    assert "WBC: 6.8 K/uL" in user_prompt

    # 2. Document was indexed into Walrus
    assert len(walrus.saved) >= 1
    # Check that document index chunk was committed
    saved_contents = [s["content"] for s in walrus.saved]
    assert any("[Document: cbc_report.txt]" in content for content in saved_contents)

    # 3. Action taken was update_memory
    assert action == "update_memory"
    assert len(entities) == 1
    assert entities[0].patient_name == "Maria"
    assert title == "Maria - CBC Review"


def test_format_message_dict_retains_indexed_flag_and_strips_base64():
    msg = _format_message_dict({
        "id": "msg-1",
        "role": "user",
        "content": "Check this file",
        "attachments": [{
            "filename": "labs.pdf",
            "file_type": "application/pdf",
            "content_base64": "top-secret-bytes",
            "indexed": True,
        }],
    })

    assert msg["attachments"] == [{
        "filename": "labs.pdf",
        "file_type": "application/pdf",
        "indexed": True,
    }]
    assert "content_base64" not in msg["attachments"][0]
