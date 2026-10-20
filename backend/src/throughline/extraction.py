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
# Keep malformed content streams from making pypdf walk an effectively
# unbounded number of operators.  This is deliberately well above the
# operator count of normal playtext PDFs.
MAX_OPERATORS = 500_000


@dataclass
class ExtractedText:
    text: str
    source_name: str
    page_count: int | None = None
    byte_count: int = 0


def extract_html(data: bytes, source_name: str) -> ExtractedText:
    soup = BeautifulSoup(data, "html.parser")
    for selector in (".footnotes", ".fnanchor", ".pagenum"):
        for element in soup.select(selector):
            element.decompose()
    for element in soup.select(".scenedesc"):
        element.replace_with(f"\n{element.get_text(' ', strip=True)}\n")
    text = re.sub(r"\s+([.,;:!?])", r"\1", soup.get_text("\n", strip=True))
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
    # Strict parsing avoids the recovery paths which can repeatedly traverse
    # malformed xref/object structures.  The API already maps parser errors to
    # its normal unreadable-source response.
    reader = PdfReader(io.BytesIO(data), strict=True)
    if len(reader.pages) > MAX_PAGES:
        raise ValueError("too many pages")
    pages: list[str] = []
    total_text = 0
    operator_count = 0

    def before_operator(*_args: object) -> None:
        nonlocal operator_count
        operator_count += 1
        if operator_count > MAX_OPERATORS:
            raise ValueError("PDF content too complex")

    def on_text(text: str, *_args: object) -> None:
        nonlocal total_text
        total_text += len(text)
        if total_text > MAX_TEXT:
            raise ValueError("extracted text too large")

    for page in reader.pages:
        pages.append(
            page.extract_text(
                visitor_operand_before=before_operator,
                visitor_text=on_text,
            )
            or ""
        )
        if total_text > MAX_TEXT:
            raise ValueError("extracted text too large")
    text = "\n".join(pages)
    if not re.search(r"\w", text):
        raise ValueError("image-only PDF")
    return ExtractedText(
        text, source_name, page_count=len(reader.pages), byte_count=len(data)
    )
