"""Request and response schemas for the authenticated doctor's memory setting."""

from pydantic import BaseModel, ConfigDict, Field


class MemoryPreferenceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    enabled: bool = Field(description="Whether MemWal may be used for retrieval and storage.")


class MemoryPreferenceResponse(BaseModel):
    enabled: bool = Field(description="Whether MemWal is enabled for this doctor.")
