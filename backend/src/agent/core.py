"""DocPilot Core Agent coordinator.

Orchestrates semantic memory recall from Walrus, LLM reasoning,
clinical entity extraction, and memory consolidation.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from agent.document_parser import ParsedDocument, chunk_document_for_indexing, parse_document
from agent.memory_extractor import clean_extracted_entities, format_memory_delta
from agent.prompts import DOCPILOT_STATIC_SYSTEM_PROMPT, DOCPILOT_SYSTEM_PROMPT, build_clinical_prompt
from client.llm import generate_chat_completion
from client.walrus import get_walrus_client
from schemas.clinical_entity import ExtractedClinicalEntity

logger = logging.getLogger(__name__)
_EXPLICIT_MEMORY_INTENT = re.compile(
    r"\b(?:remember that|please remember|don't forget|do not forget|keep in mind|"
    r"save this|store this|remember this|for future reference)\b",
    re.IGNORECASE,
)
_DOCTOR_IDENTITY_QUERY_PATTERN = re.compile(
    r"\b(?:who am i|what(?:'s| is) my name|do you (?:know|remember) (?:who i am|my name)|who is speaking|what is my identity)\b",
    re.IGNORECASE,
)


def extract_doctor_intro_name(message: str) -> Optional[str]:
    """Extracts physician name from self-introduction messages (e.g. 'I am doctor saviour', 'Call me Dr. Smith')."""
    # 1. "I am Doctor Saviour", "I'm Dr. Smith", "Call me Dr. Saviour", "My name is Doctor Saviour"
    m = re.search(
        r"\b(?:i am|i'm|my name is|call me|this is)\s+(?:dr\.?|doctor)\s+([A-Za-z0-9_.\- ]+)",
        message,
        re.IGNORECASE,
    )
    if m:
        raw_name = m.group(1).strip().rstrip(".,!?;:")
        words = raw_name.split()
        name_parts = []
        for w in words[:3]:
            if w.lower() in ("and", "the", "a", "an", "here", "today", "who", "with", "from", "at", "please"):
                break
            name_parts.append(w)
        if name_parts:
            return f"Dr. {' '.join(name_parts).title()}"

    # 2. "Dr. Saviour here", "Doctor Saviour speaking"
    m2 = re.search(
        r"\b(?:dr\.?|doctor)\s+([A-Za-z0-9_.\-]+)\s+(?:here|speaking|on call)\b",
        message,
        re.IGNORECASE,
    )
    if m2:
        return f"Dr. {m2.group(1).strip().rstrip('.,!?;:').title()}"

    return None


def extract_doctor_name_from_context(
    doctor_profile: Optional[Dict[str, Any]] = None,
    recalled_memories: Optional[List[str]] = None,
) -> Optional[str]:
    """Attempts to identify the attending physician's name from profile or recalled memories."""
    if doctor_profile:
        name = doctor_profile.get("full_name") or doctor_profile.get("name")
        if name and str(name).strip():
            return str(name).strip()

    if recalled_memories:
        for mem in recalled_memories:
            m = re.search(r"Physician Profile / Identity \(([^)]+)\)", mem)
            if m:
                return m.group(1).strip()
            m2 = re.search(
                r"(?:doctor_profile|Physician identity is)\s*:\s*(?:Physician identity is\s*)?(Dr\.?\s+[A-Za-z0-9_.\-]+)",
                mem,
                re.IGNORECASE,
            )
            if m2:
                return m2.group(1).strip()

    return None


def _requests_persistent_memory(message: str) -> bool:
    return bool(_EXPLICIT_MEMORY_INTENT.search(message))


def _parse_llm_json(raw_text: str) -> Dict[str, Any]:
    """Robustly extracts JSON payload from LLM completion text."""
    trimmed = raw_text.strip()

    # Direct parse attempt
    try:
        return json.loads(trimmed)
    except Exception:
        pass

    # Extract markdown ```json ... ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", trimmed, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    # Find first { and last }
    first_brace = trimmed.find("{")
    last_brace = trimmed.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(trimmed[first_brace : last_brace + 1])
        except Exception:
            pass

    # Fallback to treating entire text as conversational response
    return {
        "response": trimmed,
        "action_taken": "conversational",
        "entities": [],
        "suggested_title": None,
    }


class DocPilotCore:
    """Core clinical reasoning agent for DocPilot."""

    def __init__(self):
        pass

    async def process(
        self,
        doctor_id: str,
        message: str,
        memory_enabled: bool = True,
        attachments: Optional[List[Dict[str, Any]]] = None,
        doctor_profile: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, str, List[ExtractedClinicalEntity], Optional[str]]:
        """Processes a physician's query, note, and optional clinical documents.

        Args:
            doctor_id: Authenticated doctor's ID (used for Walrus namespace isolation).
            message: Clinical note or query text.
            memory_enabled: Whether MemWal may be used for recall and writes.
            attachments: Optional list of raw document/image attachments.
            doctor_profile: Optional dictionary containing doctor's profile (name, email, specialty).

        Returns:
            Tuple of (response_text, action_taken, extracted_entities, suggested_title)
        """
        walrus = await get_walrus_client() if memory_enabled else None

        # 0. Resolve doctor profile from Supabase if not explicitly provided
        if doctor_profile is None and doctor_id:
            try:
                from db.doctors_queries import get_doctor_by_id
                rec = await get_doctor_by_id(doctor_id)
                if rec:
                    doctor_profile = dict(rec)
            except Exception as exc:
                logger.debug("Could not auto-fetch doctor profile for %s: %s", doctor_id, exc)

        # Detect message intent: self-introduction vs self-identity query
        intro_doctor_name = extract_doctor_intro_name(message)
        is_doctor_intro = intro_doctor_name is not None
        is_identity_query = bool(_DOCTOR_IDENTITY_QUERY_PATTERN.search(message))

        if is_doctor_intro and intro_doctor_name:
            doctor_profile = dict(doctor_profile or {})
            doctor_profile["full_name"] = intro_doctor_name
            try:
                from db.doctors_queries import update_doctor_profile
                await update_doctor_profile(doctor_id, intro_doctor_name)
            except Exception as exc:
                logger.debug("Could not persist doctor profile name to Supabase: %s", exc)

        # 1. Parse and extract text from attached documents
        parsed_docs: List[ParsedDocument] = []
        if attachments:
            for att in attachments:
                parsed_docs.append(parse_document(att))

        # 2. Index documents into Walrus persistent memory
        has_document_text = False
        if memory_enabled and walrus is not None and parsed_docs:
            for doc in parsed_docs:
                if doc.text_content and not doc.text_content.startswith("[Binary attachment"):
                    has_document_text = True
                    chunks = chunk_document_for_indexing(doc)
                    for chunk in chunks:
                        try:
                            await walrus.remember(content=chunk, doctor_id=doctor_id)
                            logger.info(
                                "Indexed document '%s' chunk into Walrus for doctor %s.",
                                doc.filename,
                                doctor_id,
                            )
                        except Exception as exc:
                            logger.warning(
                                "Failed to index chunk of document '%s' to Walrus: %s",
                                doc.filename,
                                exc,
                            )

        # 3. Recall relevant memories for the doctor
        recalled_memories = []
        if walrus is not None:
            recall_query = message.strip()
            if is_identity_query:
                recall_query = f"{recall_query} physician profile doctor identity name Dr attending physician"
            doc_names = [d.filename for d in parsed_docs if d.filename]
            if doc_names and not recall_query:
                recall_query = f"Clinical documents: {', '.join(doc_names)}"
            elif doc_names:
                recall_query = f"{recall_query} {' '.join(doc_names)}"

            if recall_query:
                recalled_memories = await walrus.recall(
                    query=recall_query,
                    doctor_id=doctor_id,
                    limit=5,
                )

        # 4. Build clinical prompt containing physician profile, recalled memories, documents, and message
        clinical_user_prompt = build_clinical_prompt(
            doctor_message=message,
            recalled_memories=recalled_memories,
            documents=parsed_docs,
            doctor_profile=doctor_profile,
        )

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": DOCPILOT_SYSTEM_PROMPT if memory_enabled else DOCPILOT_STATIC_SYSTEM_PROMPT},
        ]

        has_images = any(d.is_image and d.image_data_url for d in parsed_docs)
        if has_images:
            content_parts: List[Dict[str, Any]] = [
                {"type": "text", "text": clinical_user_prompt}
            ]
            for d in parsed_docs:
                if d.is_image and d.image_data_url:
                    content_parts.append({
                        "type": "image_url",
                        "image_url": {"url": d.image_data_url},
                    })
            messages.append({"role": "user", "content": content_parts})
        else:
            messages.append({"role": "user", "content": clinical_user_prompt})

        # 5. Call LLM for clinical reasoning
        try:
            raw_output = await generate_chat_completion(
                messages=messages,
                temperature=0.2,
                response_format={"type": "json_object"},
            )
        except Exception as exc:
            logger.warning("LLM json_object format failed (%s), retrying without format...", exc)
            raw_output = await generate_chat_completion(
                messages=messages,
                temperature=0.2,
            )

        parsed = _parse_llm_json(raw_output)
        response_text = parsed.get("response") or "Clinical note noted and reviewed."
        action_taken = parsed.get("action_taken") or "conversational"
        normalized_action = str(action_taken).strip().lower().replace(" ", "_").replace("-", "_")
        raw_entities = parsed.get("entities") or []
        suggested_title = parsed.get("suggested_title")

        entities = clean_extracted_entities(raw_entities) if memory_enabled else []

        # Ensure doctor identity is documented when physician introduces themselves
        if memory_enabled and is_doctor_intro and intro_doctor_name:
            has_doc_entity = any(
                str(e.category).lower() in ("doctor_profile", "doctor_preference")
                for e in entities
            )
            if not has_doc_entity:
                entities.append(
                    ExtractedClinicalEntity(
                        patient_name=intro_doctor_name,
                        category="doctor_profile",
                        detail=f"Physician identity is {intro_doctor_name}",
                        confidence=1.0,
                    )
                )
            if not suggested_title:
                suggested_title = f"Physician Profile - {intro_doctor_name}"

        # Grounding safeguard: ensure 'Who am I?' answers identify the physician, not DocPilot
        known_doctor_name = extract_doctor_name_from_context(
            doctor_profile=doctor_profile,
            recalled_memories=recalled_memories,
        )
        if is_identity_query:
            resp_lower = response_text.lower()
            needs_correction = False
            if "i am docpilot" in resp_lower or "you are docpilot" in resp_lower or "it is docpilot" in resp_lower:
                needs_correction = True
            elif known_doctor_name and known_doctor_name.lower() not in resp_lower:
                needs_correction = True

            if needs_correction:
                if known_doctor_name:
                    response_text = f"You are {known_doctor_name}. How can I assist you with your consultations today?"
                elif not memory_enabled:
                    response_text = (
                        "You are the attending physician. MemWal persistent memory is currently disabled for this session."
                    )
                else:
                    response_text = (
                        "You are the attending physician, but your name hasn't been documented in persistent memory yet. "
                        "How should I address you, Doctor?"
                    )
            if recalled_memories or known_doctor_name:
                action_taken = "recall_memory"

        # 6. Commit new assertions, physician profile, & document references to Walrus memory
        if memory_enabled and walrus is not None and (
            entities
            or has_document_text
            or is_doctor_intro
            or normalized_action in {"update_memory", "save_new_memory", "save_memory"}
            or _requests_persistent_memory(message)
        ):
            delta_content = format_memory_delta(entities, message)
            if parsed_docs:
                doc_labels = ", ".join(d.filename for d in parsed_docs)
                delta_content += f"\n[Referenced Documents: {doc_labels}]"
            await walrus.remember(
                content=delta_content,
                doctor_id=doctor_id,
            )
            action_taken = "update_memory"
        elif memory_enabled and recalled_memories and action_taken == "conversational":
            action_taken = "recall_memory"
        elif not memory_enabled:
            action_taken = (
                "clarification_needed"
                if normalized_action == "clarification_needed"
                else "conversational"
            )

        return response_text, action_taken, entities, suggested_title


# Singleton agent instance
docpilot_agent = DocPilotCore()

