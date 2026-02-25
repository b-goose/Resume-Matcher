"""Document parsing service using markitdown and LLM."""

import base64
import gzip
import io
import json
import logging
import tempfile
from pathlib import Path
from typing import Any

from markitdown import MarkItDown
from pypdf import PdfReader, PdfWriter

from app.llm import complete_json
from app.prompts import PARSE_RESUME_PROMPT
from app.prompts.templates import RESUME_SCHEMA_EXAMPLE
from app.schemas import ResumeData, normalize_resume_data

logger = logging.getLogger(__name__)
_PDF_METADATA_KEY = "/ResumeMatcherData"
_PDF_METADATA_VERSION = "1"


class _PdfMinerFontBBoxFilter(logging.Filter):
    """Drop noisy pdfminer warnings for malformed FontBBox metadata."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        return "Could not get FontBBox from font descriptor" not in message


logging.getLogger("pdfminer.pdffont").addFilter(_PdfMinerFontBBoxFilter())

_PROJECT_SECTION_HINTS: tuple[str, ...] = (
    "project",
    "projects",
    "project experience",
    "personal projects",
    "side projects",
    "portfolio",
    "项目",
    "项目经历",
    "项目经验",
    "个人项目",
    "作品",
)


def _extract_pdf_text_with_pypdf(pdf_path: Path) -> str:
    """Fallback extractor for PDFs that fail in MarkItDown/pdfminer."""
    reader = PdfReader(str(pdf_path))
    page_text: list[str] = []
    for page in reader.pages:
        extracted = (page.extract_text() or "").strip()
        if extracted:
            page_text.append(extracted)
    return "\n\n".join(page_text).strip()


def _encode_embedded_resume_payload(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    compressed = gzip.compress(raw)
    return base64.urlsafe_b64encode(compressed).decode("ascii")


def _decode_embedded_resume_payload(value: str) -> dict[str, Any] | None:
    try:
        compressed = base64.urlsafe_b64decode(value.encode("ascii"))
        raw = gzip.decompress(compressed)
        payload = json.loads(raw.decode("utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def embed_resume_metadata_in_pdf(
    pdf_bytes: bytes,
    resume_data: dict[str, Any],
    source_resume_id: str | None = None,
) -> bytes:
    """Embed structured resume JSON in PDF metadata for lossless re-import."""
    normalized = normalize_resume_data(resume_data)
    payload: dict[str, Any] = {
        "type": "resume_matcher_embedded_resume",
        "version": _PDF_METADATA_VERSION,
        "resume_data": normalized,
    }
    if source_resume_id:
        payload["source_resume_id"] = source_resume_id

    encoded = _encode_embedded_resume_payload(payload)

    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    metadata: dict[str, str] = {}
    existing = reader.metadata or {}
    for key, value in existing.items():
        if isinstance(key, str) and key.startswith("/") and value is not None:
            metadata[key] = str(value)
    metadata["/ResumeMatcherVersion"] = _PDF_METADATA_VERSION
    metadata[_PDF_METADATA_KEY] = encoded
    writer.add_metadata(metadata)

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def extract_embedded_resume_data(content: bytes, filename: str) -> dict[str, Any] | None:
    """Extract embedded structured resume data from exported PDF metadata."""
    if Path(filename).suffix.lower() != ".pdf":
        return None
    try:
        reader = PdfReader(io.BytesIO(content))
    except Exception:
        return None

    metadata = reader.metadata or {}
    raw_value = metadata.get(_PDF_METADATA_KEY)
    if not isinstance(raw_value, str) or not raw_value.strip():
        return None

    payload = _decode_embedded_resume_payload(raw_value.strip())
    if not payload:
        return None
    if payload.get("type") != "resume_matcher_embedded_resume":
        return None

    resume_data = payload.get("resume_data")
    if not isinstance(resume_data, dict):
        return None

    validated = ResumeData.model_validate(normalize_resume_data(resume_data))
    return validated.model_dump()


def resume_data_to_markdown(resume_data: dict[str, Any]) -> str:
    """Create deterministic markdown snapshot from structured resume data."""
    normalized = normalize_resume_data(resume_data)
    lines: list[str] = []

    personal = normalized.get("personalInfo", {})
    if isinstance(personal, dict):
        name = str(personal.get("name", "")).strip()
        title = str(personal.get("title", "")).strip()
        if name:
            lines.append(f"# {name}")
        if title:
            lines.append(f"## {title}")
        contact_parts = [
            str(personal.get(field, "")).strip()
            for field in ("email", "phone", "location", "linkedin", "github", "website")
            if str(personal.get(field, "")).strip()
        ]
        if contact_parts:
            lines.append(" | ".join(contact_parts))

    summary = str(normalized.get("summary", "")).strip()
    if summary:
        lines.extend(["", "## Summary", summary])

    def _append_item_list(
        heading: str,
        items: list[dict[str, Any]],
        primary: str,
        secondary: str | None = None,
    ) -> None:
        if not items:
            return
        lines.extend(["", f"## {heading}"])
        for item in items:
            main = str(item.get(primary, "")).strip()
            side = str(item.get(secondary, "")).strip() if secondary else ""
            years = str(item.get("years", "")).strip()
            parts = [part for part in [main, side] if part]
            header = " - ".join(parts) if parts else main
            if years:
                header = f"{header} ({years})" if header else years
            if header:
                lines.append(f"- {header}")
            desc = item.get("description", [])
            if isinstance(desc, list):
                for bullet in desc:
                    text = str(bullet).strip()
                    if text:
                        lines.append(f"  - {text}")

    work = normalized.get("workExperience", [])
    if isinstance(work, list):
        _append_item_list("Experience", [x for x in work if isinstance(x, dict)], "title", "company")

    education = normalized.get("education", [])
    if isinstance(education, list):
        _append_item_list("Education", [x for x in education if isinstance(x, dict)], "degree", "institution")

    projects = normalized.get("personalProjects", [])
    if isinstance(projects, list):
        _append_item_list("Projects", [x for x in projects if isinstance(x, dict)], "name", "role")

    additional = normalized.get("additional", {})
    if isinstance(additional, dict):
        skill_blocks: list[tuple[str, str]] = [
            ("Technical Skills", "technicalSkills"),
            ("Languages", "languages"),
            ("Certifications", "certificationsTraining"),
            ("Awards", "awards"),
        ]
        written_heading = False
        for label, key in skill_blocks:
            values = additional.get(key, [])
            if isinstance(values, list):
                cleaned = [str(v).strip() for v in values if str(v).strip()]
                if cleaned:
                    if not written_heading:
                        lines.extend(["", "## Additional"])
                        written_heading = True
                    lines.append(f"- {label}: {', '.join(cleaned)}")

    return "\n".join(lines).strip()


def _looks_like_project_section(section_key: str, section_value: Any) -> bool:
    key = section_key.strip().lower()
    if any(hint in key for hint in _PROJECT_SECTION_HINTS):
        return True
    if not isinstance(section_value, dict):
        return False
    label = str(section_value.get("title") or section_value.get("label") or "").lower()
    return bool(label and any(hint in label for hint in _PROJECT_SECTION_HINTS))


def _coerce_projects_from_custom_sections(result: dict[str, Any]) -> dict[str, Any]:
    """Backfill personalProjects when LLM places projects into customSections."""
    if result.get("personalProjects"):
        return result

    custom_sections = result.get("customSections")
    if not isinstance(custom_sections, dict):
        return result

    recovered_projects: list[dict[str, Any]] = []
    for section_key, section_value in custom_sections.items():
        if not _looks_like_project_section(str(section_key), section_value):
            continue
        if not isinstance(section_value, dict):
            continue
        items = section_value.get("items")
        if not isinstance(items, list):
            continue
        for idx, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or item.get("title") or "").strip()
            if not name:
                continue
            description = item.get("description", [])
            if isinstance(description, str):
                description = [line.strip() for line in description.splitlines() if line.strip()]
            elif not isinstance(description, list):
                description = []
            recovered_projects.append(
                {
                    "id": idx,
                    "name": name,
                    "role": str(item.get("role") or item.get("subtitle") or "").strip(),
                    "years": str(item.get("years") or "").strip(),
                    "github": item.get("github"),
                    "website": item.get("website"),
                    "description": description,
                }
            )

    if recovered_projects:
        result["personalProjects"] = recovered_projects
        logger.info("Recovered %d project entries from customSections", len(recovered_projects))
    return result


async def parse_document(content: bytes, filename: str) -> str:
    """Convert PDF/DOCX to Markdown using markitdown.

    Args:
        content: Raw file bytes
        filename: Original filename for extension detection

    Returns:
        Markdown text content
    """
    suffix = Path(filename).suffix.lower()

    # Write to temp file for markitdown
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        md = MarkItDown()
        try:
            result = md.convert(str(tmp_path))
            extracted_text = (result.text_content or "").strip()
            if extracted_text:
                return extracted_text
            if suffix != ".pdf":
                raise ValueError("Document conversion produced empty text")
            logger.warning(
                "MarkItDown returned empty content for %s; trying PDF fallback extraction",
                filename,
            )
        except Exception as e:
            if suffix != ".pdf":
                raise
            logger.warning(
                "MarkItDown failed for %s; trying PDF fallback extraction: %s",
                filename,
                e,
            )

        fallback_text = _extract_pdf_text_with_pypdf(tmp_path)
        if fallback_text:
            return fallback_text
        raise ValueError("PDF conversion produced empty text")
    finally:
        tmp_path.unlink(missing_ok=True)


async def parse_resume_to_json(markdown_text: str) -> dict[str, Any]:
    """Parse resume markdown to structured JSON using LLM.

    Args:
        markdown_text: Resume content in markdown format

    Returns:
        Structured resume data matching ResumeData schema
    """
    prompt = PARSE_RESUME_PROMPT.format(
        schema=RESUME_SCHEMA_EXAMPLE,
        resume_text=markdown_text,
    )

    result = await complete_json(
        prompt=prompt,
        system_prompt="You are a JSON extraction engine. Output only valid JSON, no explanations.",
    )
    if isinstance(result, dict):
        result = _coerce_projects_from_custom_sections(result)

    # Validate against schema
    validated = ResumeData.model_validate(result)
    return validated.model_dump()
