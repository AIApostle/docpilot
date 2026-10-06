from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ClinicalEntityCategory(str, Enum):
    """Categories of structured clinical information extracted from consultations."""
    VITAL_SIGN = "vital_sign"
    LAB_RESULT = "lab_result"
    MEDICATION_CHANGE = "medication_change"
    DIAGNOSIS = "diagnosis"
    SYMPTOM = "symptom"
    ALLERGY = "allergy"
    PLAN = "plan"
    OTHER = "other"


class ExtractedClinicalEntity(BaseModel):
    """Discrete clinical fact or assertion extracted from a physician note or consultation."""
    model_config = ConfigDict(str_strip_whitespace=True)

    patient_name: str = Field(
        ...,
        description="Full name or emergent identifier of the patient.",
        examples=["John Doe", "Maria Santos"],
    )
    category: str = Field(
        ...,
        description="Clinical classification of the fact (vital_sign, lab_result, medication_change, diagnosis, etc.).",
        examples=["vital_sign", "medication_change"],
    )
    detail: str = Field(
        ...,
        description="Specific clinical detail, metric, or prescription change.",
        examples=["BP 150/92 mmHg", "Amlodipine increased to 10mg daily"],
    )
    confidence: Optional[float] = Field(
        default=1.0,
        description="Extraction confidence score between 0.0 and 1.0.",
    )
