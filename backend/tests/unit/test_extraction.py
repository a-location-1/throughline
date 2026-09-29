import pytest

from throughline.extraction import extract_html, extract_plain, extract_pdf


def test_html_and_plain_text_extract():
    assert "ALICE" in extract_html(b"<p>ALICE</p>", "example.org").text
    assert "ALICE" in extract_plain(b"ALICE", "play.txt").text


def test_pdf_signature_is_required():
    with pytest.raises(ValueError):
        extract_pdf(b"not a pdf", "bad.pdf")
