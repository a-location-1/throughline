from io import BytesIO

import pytest
from pypdf import PdfWriter

from throughline.extraction import MAX_PAGES, extract_html, extract_plain, extract_pdf


def test_html_and_plain_text_extract():
    assert "ALICE" in extract_html(b"<p>ALICE</p>", "example.org").text
    assert "ALICE" in extract_plain(b"ALICE", "play.txt").text


def test_html_extraction_omits_footnotes_and_page_numbers():
    html = b"""
    <p><span class="pagenum">12</span></p>
    <p>Dialogue<a class="fnanchor" href="#footnote">[1]</a></p>
    <div class="footnotes"><p id="footnote">[1] Editorial note.</p></div>
    """

    text = extract_html(html, "play.html").text

    assert "Dialogue" in text
    assert "Editorial note" not in text
    assert "12" not in text
    assert "[1]" not in text


def test_html_extraction_keeps_inline_scene_characters_together():
    html = b"""
    <p class="scenedesc">Enter a <span class="charname">Servant</span>
    and <span class="charname">Page</span>.</p>
    """

    text = extract_html(html, "play.html").text

    assert "Enter a Servant and Page." in text


def test_pdf_signature_is_required():
    with pytest.raises(ValueError):
        extract_pdf(b"not a pdf", "bad.pdf")


def test_pdf_page_limit_is_enforced():
    writer = PdfWriter()
    for _ in range(MAX_PAGES + 1):
        writer.add_blank_page(width=612, height=792)
    data = BytesIO()
    writer.write(data)

    with pytest.raises(ValueError, match="too many pages"):
        extract_pdf(data.getvalue(), "large.pdf")
