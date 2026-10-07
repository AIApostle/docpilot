from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class AttachmentSchema(BaseModel):
    """Multimodal clinical attachment (PDF lab report, clinical image, or audio recording)."""
    model_config = ConfigDict(str_strip_whitespace=True)

    filename: str = Field(..., description="File name including extension (e.g. lab_results.pdf, ecg.png)")
    file_type: str = Field(..., description="MIME type of the attachment (e.g. application/pdf, image/png, audio/ogg)")
    content_base64: Optional[str] = Field(None, description="Base64-encoded raw contents of the attachment")
    url: Optional[str] = Field(None, description="Optional hosted URL of the attachment if stored in cloud storage")
    description: Optional[str] = Field(None, description="Physician summary or caption of the attachment")
