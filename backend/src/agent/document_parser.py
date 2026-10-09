"""Document parser and clinical text extractor for multimodal attachments."""

import base64
import csv
import io
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import zlib
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ParsedDocument(BaseModel):
    """Structured representation of an extracted clinical attachment."""

    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="Detected or provided MIME type")
    text_content: str = Field(default="", description="Extracted textual clinical contents")
    is_image: bool = Field(default=False, description="Whether the file is a clinical image")
    image_data_url: Optional[str] = Field(default=None, description="Data URL for multimodal LLM vision")
    char_count: int = Field(default=0, description="Length of extracted text in characters")
    error: Optional[str] = Field(default=None, description="Extraction warning or error if any")


def _extract_pdf_via_pdftotext(pdf_bytes: bytes) -> Optional[str]:
    """Extracts text from PDF bytes using pdftotext CLI if available."""
    pdftotext_path = shutil.which("pdftotext")
    if not pdftotext_path:
        return None

    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
            tf.write(pdf_bytes)
            tf.flush()
            tmp_path = tf.name

        try:
            result = subprocess.run(
                [pdftotext_path, "-layout", "-enc", "UTF-8", tmp_path, "-"],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    except Exception as exc:
        logger.debug("pdftotext extraction encountered error: %s", exc)

    return None


def _extract_pdf_via_stream_fallback(pdf_bytes: bytes) -> str:
    """Pure-Python stream text extractor fallback for PDF bytes."""
    extracted_fragments: List[str] = []
    # Search for stream ... endstream blocks
    stream_pattern = re.compile(rb"stream[\r\n]+(.*?)[\r\n]+endstream", re.DOTALL)
    for match in stream_pattern.finditer(pdf_bytes):
        stream_data = match.group(1)
        decompressed = stream_data
        try:
            decompressed = zlib.decompress(stream_data)
        except Exception:
            pass

        # Extract (text) Tj
        for string_match in re.findall(rb"\((.*?)\)\s*(?:Tj|'|\")", decompressed, re.DOTALL):
            decoded = string_match.decode("latin-1", errors="ignore").strip()
            if decoded:
                extracted_fragments.append(decoded)

        # Extract [(t1) 12 (t2)] TJ array format
        for array_match in re.findall(rb"\[(.*?)\]\s*TJ", decompressed, re.DOTALL):
            parts = re.findall(rb"\((.*?)\)", array_match)
            joined = "".join(p.decode("latin-1", errors="ignore") for p in parts).strip()
            if joined:
                extracted_fragments.append(joined)

    # Clean and normalize whitespace
    cleaned_lines = []
    current_line = []
    for frag in extracted_fragments:
        if not frag:
            continue
        current_line.append(frag)
        if len(" ".join(current_line)) > 80:
            cleaned_lines.append(" ".join(current_line))
            current_line = []
    if current_line:
        cleaned_lines.append(" ".join(current_line))

    return "\n".join(cleaned_lines).strip()


def _format_csv_content(csv_text: str) -> str:
    """Formats CSV records into a structured clinical table string."""
    try:
        reader = csv.reader(io.StringIO(csv_text))
        rows = [row for row in reader if any(cell.strip() for cell in row)]
        if not rows:
            return csv_text.strip()

        # Format as Markdown table
        header = rows[0]
        col_widths = [max(len(cell.strip()) for cell in col) for col in zip(*rows)]
        # Cap minimum width
        col_widths = [max(w, 4) for w in col_widths]

        lines = []
        header_line = " | ".join(cell.strip().ljust(col_widths[i]) for i, cell in enumerate(header))
        sep_line = "-+-".join("-" * col_widths[i] for i in range(len(header)))
        lines.append(header_line)
        lines.append(sep_line)

        for row in rows[1:]:
            # Pad row if fewer items
            padded = row + [""] * (len(col_widths) - len(row))
            row_line = " | ".join(padded[i].strip().ljust(col_widths[i]) for i in range(len(col_widths)))
            lines.append(row_line)

        return "\n".join(lines)
    except Exception:
        return csv_text.strip()


def parse_document(attachment: Dict[str, Any]) -> ParsedDocument:
    """Extracts clinical text and metadata from an attachment."""
    filename = str(attachment.get("filename") or "untitled_document").strip()
    file_type = str(attachment.get("file_type") or "application/octet-stream").strip().lower()
    content_b64 = attachment.get("content_base64")
    description = attachment.get("description")

    # If already parsed or plain string content given
    if not content_b64:
        raw_text = str(attachment.get("text_content") or description or "").strip()
        return ParsedDocument(
            filename=filename,
            file_type=file_type,
            text_content=raw_text,
            char_count=len(raw_text),
        )

    # Decode base64
    try:
        # Strip data URL prefix if present (e.g. data:application/pdf;base64,...)
        if "," in content_b64:
            content_b64 = content_b64.split(",", 1)[1]
        file_bytes = base64.b64decode(content_b64)
    except Exception as exc:
        logger.error("Failed to base64 decode attachment '%s': %s", filename, exc)
        return ParsedDocument(
            filename=filename,
            file_type=file_type,
            text_content="",
            error=f"Base64 decode error: {exc}",
        )

    # Determine type category
    is_pdf = "pdf" in file_type or filename.lower().endswith(".pdf")
    is_csv = "csv" in file_type or filename.lower().endswith(".csv")
    is_json = "json" in file_type or filename.lower().endswith(".json")
    is_text = (
        "text" in file_type
        or "plain" in file_type
        or "markdown" in file_type
        or any(filename.lower().endswith(ext) for ext in [".txt", ".md", ".note", ".log"])
    )
    is_image = "image" in file_type or any(
        filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"]
    )

    # 1. PDF Extraction
    if is_pdf:
        extracted = _extract_pdf_via_pdftotext(file_bytes)
        if not extracted:
            extracted = _extract_pdf_via_stream_fallback(file_bytes)
        text_content = extracted or "[PDF Document attached; no selectable text layer found]"
        return ParsedDocument(
            filename=filename,
            file_type="application/pdf",
            text_content=text_content,
            char_count=len(text_content),
        )

    # 2. CSV / Tabular Extraction
    if is_csv:
        try:
            raw_text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raw_text = file_bytes.decode("latin-1", errors="replace")
        formatted = _format_csv_content(raw_text)
        return ParsedDocument(
            filename=filename,
            file_type="text/csv",
            text_content=formatted,
            char_count=len(formatted),
        )

    # 3. JSON Extraction
    if is_json:
        try:
            raw_text = file_bytes.decode("utf-8")
            parsed_json = json.loads(raw_text)
            formatted = json.dumps(parsed_json, indent=2)
        except Exception:
            formatted = file_bytes.decode("utf-8", errors="replace")
        return ParsedDocument(
            filename=filename,
            file_type="application/json",
            text_content=formatted,
            char_count=len(formatted),
        )

    # 4. Plain Text Extraction
    if is_text:
        try:
            raw_text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raw_text = file_bytes.decode("latin-1", errors="replace")
        return ParsedDocument(
            filename=filename,
            file_type="text/plain",
            text_content=raw_text.strip(),
            char_count=len(raw_text.strip()),
        )

    # 5. Image Extraction (Multimodal Vision)
    if is_image:
        image_mime = file_type if "image/" in file_type else "image/png"
        data_url = f"data:{image_mime};base64,{base64.b64encode(file_bytes).decode('ascii')}"
        info = f"[Clinical Image: {filename}]"
        try:
            from PIL import Image

            img = Image.open(io.BytesIO(file_bytes))
            info = f"[Clinical Image: {filename} ({img.width}x{img.height} {img.format})]"
        except Exception:
            pass

        if description:
            info += f" Caption/Note: {description}"

        return ParsedDocument(
            filename=filename,
            file_type=image_mime,
            text_content=info,
            is_image=True,
            image_data_url=data_url,
            char_count=len(info),
        )

    # 6. Fallback generic text decode
    try:
        decoded_text = file_bytes.decode("utf-8")
        return ParsedDocument(
            filename=filename,
            file_type=file_type,
            text_content=decoded_text.strip(),
            char_count=len(decoded_text.strip()),
        )
    except Exception:
        summary = f"[Binary attachment: {filename} ({len(file_bytes)} bytes)]"
        if description:
            summary += f" Description: {description}"
        return ParsedDocument(
            filename=filename,
            file_type=file_type,
            text_content=summary,
            char_count=len(summary),
        )


def chunk_document_for_indexing(
    doc: ParsedDocument,
    max_chunk_chars: int = 800,
    overlap_chars: int = 100,
) -> List[str]:
    """Splits a parsed document into semantic chunks suitable for Walrus memory indexing."""
    text = doc.text_content.strip()
    if not text:
        return []

    # Small documents fit into a single indexed memory chunk
    if len(text) <= max_chunk_chars:
        return [f"[Document: {doc.filename}] {text}"]

    # Chunk along paragraph or newline boundaries
    paragraphs = text.split("\n\n")
    chunks: List[str] = []
    current_chunk = []
    current_length = 0

    for para in paragraphs:
        para_clean = para.strip()
        if not para_clean:
            continue

        # If a single paragraph is longer than max_chunk_chars, break by lines or characters
        if len(para_clean) > max_chunk_chars:
            lines = para_clean.split("\n")
            for line in lines:
                line_clean = line.strip()
                if not line_clean:
                    continue
                if current_length + len(line_clean) > max_chunk_chars and current_chunk:
                    chunks.append("\n".join(current_chunk))
                    current_chunk = []
                    current_length = 0
                current_chunk.append(line_clean)
                current_length += len(line_clean) + 1
        else:
            if current_length + len(para_clean) > max_chunk_chars and current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_length = 0
            current_chunk.append(para_clean)
            current_length += len(para_clean) + 2

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    # Add document header to each chunk with part numbering
    total_chunks = len(chunks)
    formatted_chunks = []
    for idx, chunk in enumerate(chunks, 1):
        formatted_chunks.append(
            f"[Document: {doc.filename} (Part {idx}/{total_chunks})] {chunk}"
        )

    return formatted_chunks
