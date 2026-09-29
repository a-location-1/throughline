"""HTML, plain-text and selectable-text PDF extraction."""

from __future__ import annotations

import io
import re
from dataclasses import dataclass

from bs4 import BeautifulSoup
from pypdf import PdfReader

from .acquisition import MAX_BYTES

MAX_PAGES = 200
MAX_TEXT = 12 * 1024 * 1024


@dataclass
class ExtractedText:
    text: str
    source_name: str
    page_count: int | None = None
    byte_count: int = 0


def extract_html(data: bytes, source_name: str) -> ExtractedText:
    text = BeautifulSoup(data, "html.parser").get_text("\n", strip=True)
    if not text.strip():
        raise ValueError("empty source")
    return ExtractedText(text, source_name, byte_count=len(data))


def extract_plain(data: bytes, source_name: str) -> ExtractedText:
    text = data.decode("utf-8", errors="replace")
    if not text.strip():
        raise ValueError("empty source")
    return ExtractedText(text, source_name, byte_count=len(data))


def extract_pdf(data: bytes, source_name: str) -> ExtractedText:
    if len(data) > MAX_BYTES or not data.startswith(b"%PDF"):
        raise ValueError("invalid PDF")
    reader = PdfReader(io.BytesIO(data), strict=False)
    if len(reader.pages) > MAX_PAGES:
        raise ValueError("too many pages")
    pages: list[str] = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
        if sum(len(page_text) for page_text in pages) > MAX_TEXT:
            raise ValueError("extracted text too large")
    text = "\n".join(pages)
    if not re.search(r"\w", text):
        raise ValueError("image-only PDF")
    return ExtractedText(
        text, source_name, page_count=len(reader.pages), byte_count=len(data)
    )
