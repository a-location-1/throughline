import pytest

from throughline.extraction import extract_html, extract_plain, extract_pdf


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


def test_pdf_signature_is_required():
    with pytest.raises(ValueError):
        extract_pdf(b"not a pdf", "bad.pdf")
