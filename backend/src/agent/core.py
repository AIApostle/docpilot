"""DocPilot Core Agent coordinator.

Orchestrates semantic memory recall from Walrus, LLM reasoning,
clinical entity extraction, and memory consolidation.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from agent.memory_extractor import clean_extracted_entities, format_memory_delta
from agent.prompts import DOCPILOT_SYSTEM_PROMPT, build_clinical_prompt
from client.llm import generate_chat_completion
from client.walrus import get_walrus_client
from schemas.clinical_entity import ExtractedClinicalEntity

logger = logging.getLogger(__name__)


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
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Tuple[str, str, List[ExtractedClinicalEntity], Optional[str]]:
        """Processes a physician's query or note.

        Args:
            doctor_id: Authenticated doctor's ID (used for Walrus namespace isolation).
            message: Clinical note or query text.
            conversation_history: Optional prior messages in current session.

        Returns:
            Tuple of (response_text, action_taken, extracted_entities, suggested_title)
        """
        walrus = await get_walrus_client()

        # 1. Recall relevant patient memories from Walrus
        recalled_memories = await walrus.recall(
            query=message,
            doctor_id=doctor_id,
            limit=5,
        )

        # 2. Build clinical prompt
        clinical_user_prompt = build_clinical_prompt(
            doctor_message=message,
            recalled_memories=recalled_memories,
        )

        messages = [
            {"role": "system", "content": DOCPILOT_SYSTEM_PROMPT},
        ]

        # Include prior context if provided (keep last few turns)
        if conversation_history:
            for turn in conversation_history[-4:]:
                messages.append({
                    "role": turn.get("role", "user"),
                    "content": turn.get("content", ""),
                })

        messages.append({"role": "user", "content": clinical_user_prompt})

        # 3. Call LLM for clinical reasoning
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
        raw_entities = parsed.get("entities") or []
        suggested_title = parsed.get("suggested_title")

        entities = clean_extracted_entities(raw_entities)

        # 4. Commit new assertions to Walrus memory
        if entities or action_taken == "update_memory":
            delta_content = format_memory_delta(entities, message)
            await walrus.remember(
                content=delta_content,
                doctor_id=doctor_id,
            )
            action_taken = "update_memory"
        elif recalled_memories and action_taken == "conversational":
            action_taken = "recall_memory"

        return response_text, action_taken, entities, suggested_title


# Singleton agent instance
docpilot_agent = DocPilotCore()
