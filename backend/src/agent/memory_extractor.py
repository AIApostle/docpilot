"""Clinical entity extraction and memory delta synthesis."""

import datetime
import logging
from typing import Any, Dict, List
from schemas.clinical_entity import ExtractedClinicalEntity

logger = logging.getLogger(__name__)


def clean_extracted_entities(raw_list: List[Dict[str, Any]]) -> List[ExtractedClinicalEntity]:
    """Validates and parses raw dictionary entities into ExtractedClinicalEntity schemas."""
    cleaned: List[ExtractedClinicalEntity] = []
    for item in raw_list:
        try:
            name = str(item.get("patient_name") or item.get("name") or "").strip()
            cat = str(item.get("category") or "other").strip()
            detail = str(item.get("detail") or item.get("value") or "").strip()
            if name and detail:
                cleaned.append(
                    ExtractedClinicalEntity(
                        patient_name=name,
                        category=cat,
                        detail=detail,
                        confidence=float(item.get("confidence", 1.0)),
                    )
                )
        except Exception as exc:
            logger.debug("Skipping unparseable entity item %s: %s", item, exc)
    return cleaned


def format_memory_delta(
    entities: List[ExtractedClinicalEntity],
    raw_message: str,
) -> str:
    """Formats clinical assertions into structured, search-optimized memory strings for Walrus."""
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    if not entities:
        return f"[{now_str}] Clinical Consultation Note: {raw_message.strip()}"

    # Group entities by patient
    patients: Dict[str, List[str]] = {}
    for ent in entities:
        patients.setdefault(ent.patient_name, []).append(f"{ent.category}: {ent.detail}")

    lines = []
    for pat, facts in patients.items():
        joined_facts = "; ".join(facts)
        lines.append(f"[{now_str}] Patient: {pat} | {joined_facts}")

    return "\n".join(lines)
