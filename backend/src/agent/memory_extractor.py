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
    """Formats clinical assertions and physician profile data into structured, search-optimized memory strings for Walrus."""
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    if not entities:
        msg_lower = raw_message.lower()
        if any(term in msg_lower for term in ("doctor", "dr.", "dr ", "physician")):
            return f"[{now_str}] Physician Profile / Identity Note: {raw_message.strip()}"
        return f"[{now_str}] Clinical Consultation Note: {raw_message.strip()}"

    doctor_entities: List[ExtractedClinicalEntity] = []
    patients: Dict[str, List[str]] = {}

    for ent in entities:
        cat_lower = str(ent.category).strip().lower()
        pat_lower = str(ent.patient_name).strip().lower()
        if (
            cat_lower in ("doctor_profile", "doctor_preference")
            or pat_lower in ("doctor", "physician", "doctor profile", "physician profile")
        ):
            doctor_entities.append(ent)
        else:
            patients.setdefault(ent.patient_name, []).append(f"{ent.category}: {ent.detail}")

    lines = []
    if doctor_entities:
        doc_facts = "; ".join(f"{e.category}: {e.detail}" for e in doctor_entities)
        doc_names = [
            e.patient_name
            for e in doctor_entities
            if e.patient_name.strip().lower() not in ("doctor", "physician", "doctor profile", "physician profile")
        ]
        name_suffix = f" ({doc_names[0]})" if doc_names else ""
        lines.append(f"[{now_str}] Physician Profile / Identity{name_suffix}: {doc_facts}")

    for pat, facts in patients.items():
        joined_facts = "; ".join(facts)
        lines.append(f"[{now_str}] Patient: {pat} | {joined_facts}")

    return "\n".join(lines)

