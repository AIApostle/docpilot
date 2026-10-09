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
    ) -> Tuple[str, str, List[ExtractedClinicalEntity], Optional[str]]:
        """Processes a physician's query, note, and optional clinical documents.

        Args:
            doctor_id: Authenticated doctor's ID (used for Walrus namespace isolation).
            message: Clinical note or query text.
            memory_enabled: Whether MemWal may be used for recall and writes.
            attachments: Optional list of raw document/image attachments.

        Returns:
            Tuple of (response_text, action_taken, extracted_entities, suggested_title)
        """
        walrus = await get_walrus_client() if memory_enabled else None

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

        # 4. Build clinical prompt containing recalled memories, documents, and message
        clinical_user_prompt = build_clinical_prompt(
            doctor_message=message,
            recalled_memories=recalled_memories,
            documents=parsed_docs,
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

        # 6. Commit new assertions & document references to Walrus memory
        if memory_enabled and walrus is not None and (
            entities
            or has_document_text
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
