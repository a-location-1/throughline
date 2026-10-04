from throughline.errors import failure


def test_failure_is_actionable_and_generic():
    item = failure("NO_PLAYTEXT_STRUCTURE")
    assert item.message
    assert item.next_action
    assert "example.org" not in item.message


def test_pdf_failures_explain_the_specific_problem():
    assert "selectable text" in failure("PDF_NO_TEXT").message
    assert "200 pages" in failure("PDF_TOO_MANY_PAGES").message
    assert "10 MB" in failure("PDF_TOO_LARGE").message
