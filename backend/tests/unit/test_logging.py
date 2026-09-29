import logging

from throughline.logging import log_event


def test_logging_does_not_include_source_details(caplog):
    with caplog.at_level(logging.INFO, logger="throughline"):
        log_event("rejected", analysis_id="opaque-id", code="SOURCE_UNREADABLE")
    assert "opaque-id" in caplog.text
    assert "https://" not in caplog.text
